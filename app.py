from flask import Flask
from flask_cors import CORS
from settings_function import settings
from Home_page_crankshaft import home_page

app = Flask(__name__)
CORS(app)
app.register_blueprint(settings)
app.register_blueprint(home_page)
    
@app.route('/')
def index():
    return "Badan anda bau, Harap mandi Wajib"

if __name__ == '__main__':
    app.run(debug=True)
