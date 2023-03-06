import json
from flask import Flask

# getting config details
with open('config.json') as f:
    data = json.load(f)

# initializing Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = data['secret_key']

from backend import routes
