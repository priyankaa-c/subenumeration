from flask import Flask, render_template
from app.routes.app_routes import app_routes_bp
from dotenv import load_dotenv


# app = Flask(__name__)

# @app.before_first_request
# def before_first_request():
#     load_dotenv()

load_dotenv()  # Load environment variables using dotenv

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'results'
# Register the blueprint
app.register_blueprint(app_routes_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True,host='192.168.29.131')
