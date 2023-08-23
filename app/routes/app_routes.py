import os
import subprocess
from fpdf import FPDF
from flask import Blueprint, send_file, render_template, current_app, request, redirect, url_for
import re
import mysql.connector
import uuid
import datetime
from dotenv import load_dotenv

# Create a new Flask app instance for the blueprint
app_routes_bp = Blueprint('app_routes', __name__)

def before_first_request():
    load_dotenv()

def consolidate_results(result_list):
    consolidated = "\n".join(result_list)
    return consolidated

def generate_unique_id():
    return str(uuid.uuid4())

def get_mysql_credentials():
    mysql_credentials = {
        'host': os.environ.get('DB_HOST'),
        'database': os.environ.get('DB_NAME'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD')
    }
    return mysql_credentials
    
@app_routes_bp.before_app_first_request
def before_first_request():
    app_routes_bp.config = {'UPLOAD_FOLDER': 'results'}

def create_mysql_connection():
    credentials = get_mysql_credentials()
    conn = mysql.connector.connect(**credentials)
    return conn

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

@app_routes_bp.route('/subdom_enum', methods=['GET', 'POST'])
def run_subdomainenum():
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

@app_routes_bp.route('/results/<result_id>', methods=['GET'])def show_results(result_id):    timestamp, domain, txt_data = retrieve_results(result_id)    txt_filename = generate_file_name(domain, 'txt')    txt_path = os.path.join(app.config['UPLOAD_FOLDER'], txt_filename)        with open(txt_path, 'wb') as txt_file:        txt_file.write(txt_data)    with open(txt_path, 'r') as txt_file:        consolidated_results = txt_file.read()        return render_template('subdom_results.html', result_id=result_id, domain=domain, consolidated_results=consolidated_results)

def generate_file_name(domain, extension):
    domain_without_tld = domain.split('.')[0]
    return f'{domain_without_tld}_results.{extension}'

def save_results_to_txt(result_id, domain, consolidated_results):
    txt_filename = generate_file_name(domain, 'txt')
    txt_path = os.path.join(app.config['UPLOAD_FOLDER'], txt_filename)
    with open(txt_path, 'w') as txt_file:
        txt_file.write(consolidated_results)
    
    pdf_filename = generate_file_name(domain, 'pdf')
    pdf_path = create_pdf(domain, consolidated_results)
    
    csv_filename = generate_file_name(domain, 'csv')
    csv_path = create_csv(domain, consolidated_results)
    
    return txt_path, pdf_path, csv_path

def create_pdf(domain, consolidated_results):
    domain_without_tld = domain.split('.')[0]
    pdf_filename = f'{domain_without_tld}_results.pdf'
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Enumeration Results", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Domain: {domain}", ln=True, align='L')
    pdf.cell(200, 10, txt="Consolidated Results:", ln=True, align='L')
    pdf.multi_cell(0, 5, txt=consolidated_results)
    pdf.output(pdf_path)
    return pdf_path

def create_csv(domain, consolidated_results):
    domain_without_tld = domain.split('.')[0]
    csv_filename = f'{domain_without_tld}_results.csv'
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    with open(csv_path, 'w') as f:
        f.write('Consolidated Results:\n')
        f.write(consolidated_results)
        f.write('\n')
    return csv_path

@app_routes_bp.route('/results/<result_id>/text', methods=['GET'])
def show_results_text(result_id):
    timestamp, domain, txt_data = retrieve_results(result_id)
    return txt_data

@app_routes_bp.route('/download/<result_id>/<file_type>', methods=['GET'])
def download_file(result_id, file_type):
    if file_type not in ['pdf', 'csv']:
        return "Invalid file type"
    
    _, _, txt_data = retrieve_results(result_id)
    domain = retrieve_results(result_id)[1]
    filename = generate_file_name(domain, file_type)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    return send_file(file_path, as_attachment=True)

@app_routes_bp.route('/download/txt/<result_id>', methods=['GET'])
def download_txt_file(result_id):
    _, _, txt_data = retrieve_results(result_id)
    domain = retrieve_results(result_id)[1]
    filename = generate_file_name(domain, 'txt')
    txt_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    with open(txt_path, 'wb') as txt_file:
        txt_file.write(txt_data)
    
    return send_file(txt_path, as_attachment=True)

def run_enumeration_script(tool, domain):
    script_path = os.path.join('enumeration_scripts', f'{tool}.py')
    result = subprocess.run(['python', script_path, domain], capture_output=True, text=True)
    return result.stdout
