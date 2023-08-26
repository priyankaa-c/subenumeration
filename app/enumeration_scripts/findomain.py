# subenumeration/app/enumeration_scripts/findomain.py
import subprocess
import sys
import re

def run_findomain(domain):
    try:
        result = subprocess.run(['findomain', '-t', domain], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            subdomains = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b|\b[a-zA-Z0-9.-]+\.{1}[a-zA-Z]{2,}\b', result.stdout)
            return "\n".join(subdomains)
        else:
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Enumeration took too long and was terminated."

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python findomain.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]

    findomain_results = run_findomain(domain)

    print(findomain_results)


