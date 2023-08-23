from flask import Flask

app = Flask(__name__)

from app.routes.subdomain_enum_routes import subdomain_enum_bp
app.register_blueprint(subdomain_enum_bp)
