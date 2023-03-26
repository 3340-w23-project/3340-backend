from datetime import datetime, timedelta, timezone
import json
from flask import request, jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required
import bcrypt
from api import app, db
from api.models import User

# use this to simply ping the server
@app.route('/ping')
@app.route('/')
def ping():
    return {"msg":"pong"}, 200

@app.route('/signup', methods=["POST"])
def signup():
    # get query params
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    
    # validate that params are sent in
    if username is None or password is None:
        return {"msg": "username or password missing"}, 400

    # check if user already exists
    queried_user = User.query.filter_by(username=username).first()
    if queried_user:
        return {"msg": f"user <{username}> already exists"}, 409

    # creating a new user and adding it to the users table
    user = User(username=username, password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()))
    db.session.add(user)
    db.session.commit()
    return {"msg": f"user <{username}> created successfully"}, 201

@app.route('/login', methods=["POST"])
def login():
    # get query params
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    
    # validate that params are sent in
    if username is None or password is None:
        return {"msg": "username or password missing"}, 400

    # get user by username
    user = User.query.filter_by(username=username).first()

    # if user doesn't exist or the password is incorrect, we return unauthorized
    if not user:
        return {"msg":"incorrect username or password"}, 401
    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
        return {"msg":"incorrect username or password"}, 401

    # creating jwt token and returning it
    access_token = create_access_token(identity=username)
    return {"access_token":access_token}, 200

@app.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        return response

# this is just a dummy endpoint to check if your JWT auth is working
# it will return back the username associated with your JWT token
@app.route('/identity')
@jwt_required()
def my_profile():
    return {"identity": get_jwt_identity()}, 200

# CREDITS
# our authentication was inspired by the following article:
# https://dev.to/nagatodev/how-to-add-login-authentication-to-a-flask-and-react-application-23i7
