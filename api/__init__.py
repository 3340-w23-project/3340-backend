from dotenv import load_dotenv
load_dotenv()
import os
from datetime import timedelta
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# initializing Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# jwt config
app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JSON_SORT_KEYS"] = False
jwt = JWTManager(app)

# create the extension
db = SQLAlchemy()

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URI')
# initialize the app with the extension
db.init_app(app)

# allowing all origins and methods
# this is pretty insecure - don't ever use this in production code
CORS(app, supports_credentials=True)

from api import routes
