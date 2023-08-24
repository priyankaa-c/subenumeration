# app/routes/app_routes.py

import os
import subprocess
from fpdf import FPDF
from flask import Blueprint, send_file, render_template, current_app, request, redirect, url_for
from app.enumeration_scripts.feroxbuster import *
from app.enumeration_scripts.findomain import run_findomain
from app.enumeration_scripts.subfinder import run_subfinder
from app.enumeration_scripts.crtsh import run_crtsh
import re
import mysql.connector
import uuid
import datetime
from dotenv import *

# Create a new Flask app instance for the blueprint
app_routes_bp = Blueprint('app_routes', __name__, template_folder='templates')

# Define the configuration key for the blueprint
app_routes_bp.config = {'UPLOAD_FOLDER': 'results'}

# @app_routes_bp.before_app_first_request
# def before_first_request():
#     load_dotenv()

# Function to consolidate results.
def consolidate_results(result_list):
    consolidated = "\n".join(result_list)
    return consolidated

# Function to generate unique uuid.
def generate_unique_id():
    return str(uuid.uuid4())

# Function to fetch database details from environment file.
def get_mysql_credentials():
    mysql_credentials = {
        'host': os.environ.get('DB_HOST'),
        'database': os.environ.get('DB_NAME'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD')
    }
    return mysql_credentials
    

def before_first_request():
    app_routes_bp.config = {'UPLOAD_FOLDER': 'results'}

# Function to make mysql connection.
def create_mysql_connection():
    credentials = get_mysql_credentials()
    conn = mysql.connector.connect(**credentials)
    return conn

# Function to store output file in database as blob storage.
def store_results(result_id, domain, txt_path, pdf_path, csv_path):
    current_time = datetime.datetime.now()
    conn = create_mysql_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO enumeration_results (result_id, timestamp, domain, txt_data, pdf_data, csv_data)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    with open(txt_path, 'rb') as txt_file, open(pdf_path, 'rb') as pdf_file, open(csv_path, 'rb') as csv_file:
        txt_data = txt_file.read()
        pdf_data = pdf_file.read()
        csv_data = csv_file.read()
        cursor.execute(insert_query, (result_id, current_time, domain, txt_data, pdf_data, csv_data))

    conn.commit()
    cursor.close()
    conn.close()

def retrieve_results(result_id):
    conn = create_mysql_connection()
    cursor = conn.cursor()

    select_query = """
    SELECT timestamp, domain, txt_data
    FROM enumeration_results
    WHERE result_id = %s
    """
    cursor.execute(select_query, (result_id,))
    row = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    if row:
        timestamp, domain, txt_data = row
        return timestamp, domain, txt_data
    else:
        return None, None, None

def update_paths(result_id):
    # Update PDF and CSV paths in the database entry
    pass

# ------------------------------------------
# Function to fetch input from user via subdom_enum.html web page, and passing it to enumeration scripts, and consolidate all the results from findomain.py, subfinder.py and crtsh.py.
@app_routes_bp.route('/subdom_enum', methods=['GET', 'POST'])
def subdom_enum():
    if request.method == 'POST':
        domain = request.form['domain']

        # Run enumeration scripts and consolidate results
        findomain_results = run_enumeration_script('findomain', domain)
        subfinder_results = run_enumeration_script('subfinder', domain)
        crtsh_results = run_enumeration_script('crtsh', domain)

        consolidated_results = consolidate_results([findomain_results, subfinder_results, crtsh_results])

        result_id = generate_unique_id()

        txt_path, pdf_path, csv_path = save_results_to_txt(result_id, domain, consolidated_results)

        # Store results in the database
        store_results(result_id, domain, txt_path, pdf_path, csv_path)

        # Redirect to results page
        return redirect(url_for('app_routes.show_results', result_id=result_id))

    return render_template('subdom_enum.html')

# Function to run enumeration scripts (findomain.py, subfinder.py, and crtsh.py)
def run_enumeration_script(tool, domain):
    script_path = os.path.join('app', 'enumeration_scripts', f'{tool}.py')
    result = subprocess.run(['python', script_path, domain], capture_output=True, text=True)
    return result.stdout

# Function to render output on subdom_results.html page from text file.
@app_routes_bp.route('/results/<result_id>', methods=['GET'])
def show_results(result_id):
    timestamp, domain, txt_data = retrieve_results(result_id)
    txt_filename = generate_file_name(domain, 'txt')
    txt_path = os.path.join(current_app.config['UPLOAD_FOLDER'], txt_filename)

    with open(txt_path, 'w') as txt_file:
        txt_file.write(txt_data)

    with open(txt_path, 'r') as txt_file:
        consolidated_results = txt_file.read()

    unique_subdomains = extract_unique_urls(consolidated_results)  # Implement this function
    unique_ips = extract_unique_ips(consolidated_results)  # Implement this function

    return render_template('subdom_results.html', result_id=result_id, domain=domain, unique_subdomains=unique_subdomains, unique_ips=unique_ips)

# Function to extract unique URLs from consolidated results
def extract_unique_urls(consolidated_results):
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', consolidated_results)
    return list(set(urls))  # Convert to set and back to list to remove duplicates

# Function to extract unique IP addresses from consolidated results
def extract_unique_ips(consolidated_results):
    ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', consolidated_results)
    return list(set(ips))  # Convert to set and back to list to remove duplicates

# Extract IP addresses from output.
def get_unique_subdomains_ips(domain):
    temp_output_path = f"static/temp/{domain.replace('.', '_')}_output.txt"
    unique_subdomains, unique_ips = set(), set()

    with open(temp_output_path, 'r') as temp_file:
        for line in temp_file:
            line = line.strip()
            if is_valid_domain_or_ip(line):
                if is_ip_address(line):
                    unique_ips.add(line)
                else:
                    unique_subdomains.add(line)
    
    return unique_subdomains, unique_ips

def is_valid_domain_or_ip(text):
    # Check if the text is a valid domain name or IP address
    return is_valid_domain(text) or is_ip_address(text)

def is_valid_domain(domain):
    # Check if the domain matches a valid domain pattern
    domain_pattern = r'\b(?:[a-zA-Z0-9.-]+\.{1}[a-zA-Z]{2,})\b'
    return re.match(domain_pattern, domain)

def is_ip_address(text):
    # Check if the text is a valid IP address
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    return re.match(ip_pattern, text)

# Function to consolidate results.
def consolidate_results(result_list):
    consolidated = "\n".join(result_list)
    return consolidated

# Function to save consolidated results to a temporary file.
def save_results_to_temp_file(consolidated_results, domain):
    temp_output_path = f"static/temp/{domain.replace('.', '_')}_output.txt"
    
    with open(temp_output_path, 'w') as temp_file:
        temp_file.write(consolidated_results)

@app_routes_bp.route('/download/<result_id>/<file_type>', methods=['GET'])
def download_file(result_id, file_type):
    if file_type not in ['pdf', 'csv']:
        return "Invalid file type"

    _, _, txt_data = retrieve_results(result_id)
    domain = retrieve_results(result_id)[1]
    filename = generate_file_name(domain, file_type)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    return send_file(file_path, as_attachment=True)

@app_routes_bp.route('/download/txt/<result_id>', methods=['GET'])
def download_txt_file(result_id):
    _, _, txt_data = retrieve_results(result_id)
    domain = retrieve_results(result_id)[1]
    filename = generate_file_name(domain, 'txt')
    txt_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    with open(txt_path, 'wb') as txt_file:
        txt_file.write(txt_data)
    
    return send_file(txt_path, as_attachment=True)

# -------------------------------------------
# Function to generate output file name as domain name (eg enumeration for example.com, output file name would be example_com_xxxxxxxx.xxx)
def generate_file_name(domain, extension):
    domain_without_tld = domain.split('.')[0]
    return f'{domain_without_tld}_results.{extension}'

# Function to save subdomain enumeration output in text file.
def save_results_to_txt(result_id, domain, consolidated_results):
    upload_folder = app_routes_bp.config['UPLOAD_FOLDER']  # Access the config through the blueprint
    txt_filename = generate_file_name(domain, 'txt')
    txt_path = os.path.join(upload_folder, txt_filename)
    with open(txt_path, 'w') as txt_file:
        txt_file.write(consolidated_results)

    pdf_filename = generate_file_name(domain, 'pdf')
    pdf_path = create_pdf(domain, consolidated_results)

    csv_filename = generate_file_name(domain, 'csv')
    csv_path = create_csv(domain, consolidated_results)

    return txt_path, pdf_path, csv_path

# Function to create output file as in PDF format.
def create_pdf(domain, consolidated_results):
    domain_without_tld = domain.split('.')[0]
    pdf_filename = f'{domain_without_tld}_results.pdf'
    pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_filename)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Enumeration Results", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Domain: {domain}", ln=True, align='L')
    pdf.cell(200, 10, txt="Consolidated Results:", ln=True, align='L')
    pdf.multi_cell(0, 5, txt=consolidated_results)
    pdf.output(pdf_path)
    return pdf_path

# Function to create output file as in CSV format.
def create_csv(domain, consolidated_results):
    domain_without_tld = domain.split('.')[0]
    csv_filename = f'{domain_without_tld}_results.csv'
    csv_path = os.path.join(current_app.config['UPLOAD_FOLDER'], csv_filename)
    with open(csv_path, 'w') as f:
        f.write('Consolidated Results:\n')
        f.write(consolidated_results)
        f.write('\n')
    return csv_path

@app_routes_bp.route('/results/<result_id>/text', methods=['GET'])
def show_results_text(result_id):
    timestamp, domain, txt_data = retrieve_results(result_id)
    return txt_data

#---------------------- Directory Brute Forcing-------------------------
# Route for directory brute forcing
@app_routes_bp.route('/feroxbuster', methods=['GET', 'POST'])
def feroxbuster():
    if request.method == 'POST':
        target_url = request.form.get('target_url')
        wordlist = request.files.get('wordlist')
        options = request.form.getlist('options')

        wordlist_path = '/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt'
        if wordlist:
            wordlist_path = 'app/static/temp/' + wordlist.filename
            wordlist.save(wordlist_path)

        feroxbuster_results = get_feroxbuster_results(options, target_url, wordlist_path)
        results = []
        for line in feroxbuster_results.splitlines():
           parts = line.split(' ')
           if len(parts) >= 2:
               results.append({'url': parts[1], 'status_code': parts[0]})
        
        return render_template('feroxbuster_results.html', feroxbuster_results=results)
    
    return render_template('feroxbuster.html')
