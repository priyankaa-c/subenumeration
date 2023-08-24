# app/__init__.py

from flask import Flask

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'results'  # Define your upload folder path here

# Import and register the blueprint
from .routes.app_routes import app_routes_bp
app.register_blueprint(app_routes_bp)

if __name__ == '__main__':
    app.run(debug=True)
