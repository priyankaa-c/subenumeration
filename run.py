from flask import Flask, render_template
from app.routes.app_routes import app_routes_bp

app = Flask(__name__)

# Register the blueprint
app.register_blueprint(app_routes_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    #app.run(debug=True)    app.run(debug=True,host='192.168.29.131')
