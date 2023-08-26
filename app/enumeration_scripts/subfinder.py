# subenumeration/app/enumeration_scripts/subfinder.py
import subprocess
import sys
import re

def run_subfinder(domain):
    try:
        result = subprocess.run(['subfinder', '-d', domain], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            subdomains = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b|\b[a-zA-Z0-9.-]+\.{1}[a-zA-Z]{2,}\b', result.stdout)
            return "\n".join(subdomains)
        else:
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Enumeration took too long and was terminated."

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python subfinder.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]

    subfinder_results = run_subfinder(domain)

    print(subfinder_results)

