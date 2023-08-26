# app/routes/app_routes.py
from flask import Blueprint, render_template, request, send_file, redirect, url_for
import os
import subprocess
import re
import xml.etree.ElementTree as ET

app_routes_bp = Blueprint('app_routes', __name__, template_folder='templates')

def generate_file_name(domain, extension):
    domain_without_tld = domain.split('.')[0]
    return f'{domain_without_tld}_results.{extension}'

@app_routes_bp.route('/subdom_enum', methods=['GET', 'POST'])
def subdom_enum():
    if request.method == 'POST':
        domain = request.form.get('domain')
        
        # Run subdomain enumeration scripts
        findomain_results = run_findomain(domain)
        subfinder_results = run_subfinder(domain)
        crtsh_results = run_crtsh(domain)
        
        # Extract unique subdomains from non-empty results
        non_empty_results = [result for result in [findomain_results, subfinder_results, crtsh_results] if result.strip()]
        unique_subdomains = set()

        for result in non_empty_results:
            subdomains = result.strip().split('\n')
            for subdomain in subdomains:
                if subdomain.endswith(domain):
                    unique_subdomains.add(subdomain)
        
        # Store filtered results in temporary file
        temp_filename = f"results/subdomain/temp/{generate_file_name(domain, 'txt')}"
        with open(temp_filename, 'w') as temp_file:
            temp_file.write('\n'.join(unique_subdomains))

        return redirect(url_for('app_routes.show_results', domain=domain))

    return render_template('subdom_enum.html')

def run_findomain(domain):
    try:
        result = subprocess.run(['python', 'app/enumeration_scripts/findomain.py', domain], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Enumeration took too long and was terminated."

def run_subfinder(domain):
    try:
        result = subprocess.run(['python', 'app/enumeration_scripts/subfinder.py', domain], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Enumeration took too long and was terminated."

def run_crtsh(domain):
    try:
        result = subprocess.run(['python', 'app/enumeration_scripts/crtsh.py', domain], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Enumeration took too long and was terminated."


@app_routes_bp.route('/show_results/<domain>')
def show_results(domain):
    temp_filename = f"results/subdomain/temp/{generate_file_name(domain, 'txt')}"
    consolidated_results = []

    with open(temp_filename, 'r') as temp_file:
        consolidated_results = temp_file.readlines()

    # Remove blank lines
    consolidated_results = [line.strip() for line in consolidated_results if line.strip()]

    # Use the same unique_subdomains set from subdom_enum function
    unique_subdomains = set(consolidated_results)

    return render_template('subdom_results.html', subdomains=unique_subdomains)
