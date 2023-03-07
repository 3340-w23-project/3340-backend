import json
from datetime import timedelta
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

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

# create the extension
db = SQLAlchemy()

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = data['database_uri']
# initialize the app with the extension
db.init_app(app)

from backend import routes
