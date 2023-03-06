import json
from datetime import timedelta
from flask import Flask
from flask_jwt_extended import JWTManager

# getting config details
with open('config.json') as f:
    data = json.load(f)

# initializing Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = data['secret_key']

# jwt config
app.config["JWT_SECRET_KEY"] = data['jwt_secret_key']
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)

from backend import routes
