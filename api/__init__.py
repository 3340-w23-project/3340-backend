from dotenv import load_dotenv
import os
from datetime import timedelta
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
import pymysql

load_dotenv()
pymysql.install_as_MySQLdb()

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

# ssl config
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {
        "ssl": {
            "ca": os.getenv('CA_CERT'),
        }
    }
}

# initialize the app with the extension
db.init_app(app)

from api import routes