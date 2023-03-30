from datetime import datetime, timedelta, timezone
import json
from flask import request, jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required
import bcrypt
from api import app, db
from api.models import User, Post, Channel, Category

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

@app.route('/post/all')
def posts():
    posts = Post.query.all()
    posts.reverse()
    return jsonify([post.to_dict() for post in posts])

@app.route('/channel/<int:channel_id>/posts')
def get_posts_in_channel(channel_id):
    # Get the channel object
    channel = Channel.query.get(channel_id)

    # Check if the channel exists
    if not channel:
        return {"msg": "channel not found"}, 404

    # Get all posts in the channel and convert them to dictionaries
    posts = [post.to_dict() for post in channel.posts]

    return {'channel_name': channel.name, 'posts': posts}, 200

@app.route('/post/new', methods=["POST"])
@jwt_required()
def new_post():
    # get query params
    title = request.json.get("title", None)
    content = request.json.get("content", None)
    channel_id = request.json.get("channel_id", None)

    # validate that params are sent in
    if title is None or content is None or channel_id is None:
        return {"msg": "title, content, or channel_id missing"}, 400

    # getting user
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"msg": "error fetching user from JWT token"}, 401

    # checking if the channel exists
    channel = Channel.query.filter_by(id=channel_id).first()
    if not channel:
        return {"msg": "channel not found"}, 404

    # creating and adding the new post to the specified channel
    post = Post(title=title, content=content, author=user, channel=channel)
    db.session.add(post)
    db.session.commit()

    return {"msg": "post created successfully"}, 200

@app.route('/post/<post_id>/update', methods=["POST"])
@jwt_required()
def update_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    if not post:
        return {"msg": "post not found"}, 404

    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"msg": "error fetching user from JWT token"}, 401

    if post.author != user:
        return {"msg": "You do not have permission to modify this post"}, 401

    # get query params
    title = request.json.get("title", None)
    content = request.json.get("content", None)

    # validate that params are sent in
    if title is None or content is None:
        return {"msg": "title or content missing"}, 400

    # updating values of post
    post.title = title
    post.content = content
    db.session.commit()

    return {"msg": "post updated successfully"}, 200

@app.route('/post/<post_id>/delete', methods=["POST"])
@jwt_required()
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    if not post:
        return {"msg": "post not found"}, 404

    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"msg": "error fetching user from JWT token"}, 401

    if post.author != user:
        return {"msg": "You do not have permission to modify this post"}, 401

    # deleting replies and post itself
    for reply in post.replies:
        db.session.delete(reply)
    db.session.delete(post)
    db.session.commit()

    return {"msg": f"successfully deleted post {post_id}"}, 200

@app.route('/categories')
def get_categories():
    categories = Category.query.all()
    response = []
    for category in categories:
        channels_list = [{'id': channel.id, 'name': channel.name} for channel in category.channels]
        response.append({'id': category.id, 'name': category.name, 'channels': channels_list})
    return {'categories': response}, 200