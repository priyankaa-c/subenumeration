# app/enumeration_scripts/feroxbuster.py

import subprocess
from flask import request

def run_feroxbuster(domain, wordlist_path, options):
    command = ['feroxbuster', '--url', domain]
    
    if wordlist_path:
        command.extend(['-w', wordlist_path])
        
    command.extend(options)
    
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout.splitlines()

def get_feroxbuster_results(options, target_url, wordlist_path):
    command = ['feroxbuster', '-u', target_url, '-w', wordlist_path, *options]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout
