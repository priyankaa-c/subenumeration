# app/__init__.py

from flask import Flask

app = Flask(__name__)

# Import and register the blueprint
from .routes.app_routes import app_routes_bp
app.register_blueprint(app_routes_bp)

if __name__ == '__main__':
    app.run(debug=True)
