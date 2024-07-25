from flask import Flask
from flask_cors import CORS
from settings_function import settings

app = Flask(__name__)
CORS(app)
app.register_blueprint(settings)

@app.route('/')
def index():
    return "This is a basic flask application"

if __name__ == '__main__':
    app.run(debug=True)
