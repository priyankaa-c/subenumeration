# app/enumeration_scripts/crtsh.py

import requests
import sys
import re

def run_crtsh(domain):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            subdomains = set(item['name_value'] for item in data)
            filtered_subdomains = [subdomain for subdomain in subdomains if re.match(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b|\b[a-zA-Z0-9.-]+\.{1}[a-zA-Z]{2,}\b', subdomain)]

            return "\n".join(filtered_subdomains)

        else:

            return f"Error: Failed to fetch data from crt.sh"

    except requests.RequestException as e:

        return f"Error: {e}"



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python crtsh.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]

    crtsh_results = run_crtsh(domain)

    print(crtsh_results)

