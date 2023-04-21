import json
import os
import re
import bcrypt
from datetime import datetime, timedelta, timezone
from flask import request, jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required
from api import app, db
from api.models import User, Post, Channel, Category, Reply, Like
from better_profanity import profanity
profanity.load_censor_words()

restricted_mode = os.environ.get("RESTRICTED_MODE", False) == True
if restricted_mode:
    allowed_usernames = os.environ.get(
        "ALLOWED_USERNAMES", "").lower().split(",")

# use this to simply ping the server
@app.route('/ping')
@app.route('/')
def ping():
    return {"msg": "pong"}, 200


@app.route('/signup', methods=["POST"])
def signup():
    # get query params
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    # validate that params are sent in
    if username is None or password is None:
        return {"msg": "Username or password missing"}, 400

    if len(username) < 3 or len(username) > 20:
        return {"msg": "Username must be between 3 and 20 characters"}, 400

    if len(password) < 4 or len(password) > 30:
        return {"msg": "Password must be between 4 and 30 characters"}, 400

    # check for illegal characters
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return {"msg": "Username contains illegal characters"}, 400

    # check for profanity
    if (profanity.contains_profanity(username)):
        return {"msg": "Username contains profanity"}, 400

    # convert username to lowercase
    lc_username = username.lower()

    # check if user already exists (case insensitive)
    queried_user = User.query.filter(User.username.ilike(lc_username)).first()
    if queried_user:
        return {"msg": f"User <{username}> already exists"}, 409

    if restricted_mode:
        if lc_username not in allowed_usernames:
            return {"msg": f"User <{lc_username}> not allowed to sign up"}, 403

    # creating a new user and adding it to the users table
    user = User(username=lc_username, display_name=username, password_hash=bcrypt.hashpw(
        password.encode('utf-8'), bcrypt.gensalt()))
    db.session.add(user)
    db.session.commit()
    return {"msg": f"user <{username}> created successfully"}, 201


@app.route('/signin', methods=["POST"])
def login():
    # get query params
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    # validate that params are sent in
    if username is None or password is None:
        return {"msg": "username or password missing"}, 400

    if len(username) < 3 or len(username) > 20:
        return {"msg": "invalid username"}, 400

    # convert username to lowercase
    lc_username = username.lower()

    # get user by username (case insensitive)
    user = User.query.filter(User.username.ilike(lc_username)).first()

    # if user doesn't exist or the password is incorrect, we return unauthorized
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return {"msg": "incorrect username or password"}, 401

    # creating jwt token and returning it
    access_token = create_access_token(identity=lc_username)
    return {"access_token": access_token}, 200


@app.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response


# @app.after_request
# def refresh_expiring_jwts(response):
#     try:
#         exp_timestamp = get_jwt()["exp"]
#         now = datetime.now(timezone.utc)
#         target_timestamp = datetime.timestamp(now + timedelta(hours=6))
#         if target_timestamp > exp_timestamp:
#             access_token = create_access_token(identity=get_jwt_identity())
#             data = response.get_json()
#             if type(data) is dict:
#                 data["access_token"] = access_token
#                 response.data = json.dumps(data)
#         return response
#     except (RuntimeError, KeyError):
#         # Case where there is not a valid JWT. Just return the original respone
#         return response

# this is just a dummy endpoint to check if your JWT auth is working
# it will return back the username associated with your JWT token
@app.route('/identity')
@jwt_required()
def my_profile():
    return {"username": get_jwt_identity(), "display_name": User.query.filter(User.username.ilike(get_jwt_identity())).first().display_name}, 200

# CREDITS
# our authentication was inspired by the following article:
# https://dev.to/nagatodev/how-to-add-login-authentication-to-a-flask-and-react-application-23i7


@app.route('/categories')
@jwt_required()
def get_categories():
    categories = Category.query.all()
    response = []
    for category in categories:
        channels_list = [{'id': channel.id, 'name': channel.name}
                         for channel in category.channels]
        response.append(
            {'id': category.id, 'name': category.name, 'channels': channels_list})
    return {'categories': response}, 200


@app.route('/post/all')
@jwt_required()
def posts():
    posts = Post.query.all()
    posts.reverse()
    username = get_jwt_identity()
    return jsonify([post.to_dict(username=username) for post in posts])


@app.route('/channel/<int:channel_id>', methods=["GET"])
@jwt_required()
def get_channel(channel_id):
    # Get the channel object
    channel = Channel.query.get(channel_id)

    # Check if the channel exists
    if not channel:
        return {"msg": "channel not found"}, 404

    return channel.to_dict(), 200


@app.route('/channel/<int:channel_id>/posts')
@jwt_required()
def get_posts_in_channel(channel_id):
    # Get the channel object
    channel = Channel.query.get(channel_id)

    # Check if the channel exists
    if not channel:
        return {"msg": "channel not found"}, 404

    username = get_jwt_identity()
    # Get all posts in the channel and convert them to dictionaries
    posts = [post.to_dict(username=username) for post in channel.posts]

    return posts, 200


@app.route('/post/new', methods=["POST"])
@jwt_required()
def new_post():
    # get query params
    title = profanity.censor(request.json.get("title", None))
    content = profanity.censor(request.json.get("content", None))
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


@app.route('/post/<int:post_id>/reply', methods=['POST'])
@jwt_required()
def create_reply(post_id):
    # get query params
    content = profanity.censor(request.json.get("content", None))
    parent_reply_id = request.json.get("parent_reply_id", None)

    # validate that params are sent in
    if content is None:
        return {"msg": "content missing"}, 400

    # getting user
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"msg": "error fetching user from JWT token"}, 401

    # checking if the post exists
    post = Post.query.filter_by(id=post_id).first()
    if not post:
        return {"msg": "post not found"}, 404

    # Declare parent_reply outside of the conditional block
    parent_reply = None

    # Determine if this is a reply to a post or to another reply
    if parent_reply_id:
        parent_reply = Reply.query.filter_by(id=parent_reply_id).first()
        if not parent_reply:
            return {"msg": "parent reply not found"}, 404
        depth = parent_reply.depth + 1
    else:
        depth = 0

    if depth > 5:
        return {"msg": "maximum nesting level exceeded"}, 400

    # create new reply object
    reply = Reply(content=content, user_id=user.id, post=post,
                  parent_reply=parent_reply, depth=depth)
    db.session.add(reply)
    db.session.commit()

    return {"msg": "reply created successfully"}, 201


@app.route('/reply/<int:reply_id>/update', methods=['POST'])
@jwt_required()
def update_reply(reply_id):
    # getting user
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"msg": "error fetching user from JWT token"}, 401

    # checking if the reply exists
    reply = Reply.query.filter_by(id=reply_id).first()
    if not reply:
        return {"msg": "reply not found"}, 404

    # checking if the user is authorized to update the reply
    if reply.user_id != user.id:
        return {"msg": "unauthorized to update this reply"}, 403

    # get query params
    content = profanity.censor(request.json.get("content", None))

    # validate that params are sent in
    if content is None:
        return {"msg": "content missing"}, 400

    # update the reply object
    reply.content = content
    reply.edited = True
    db.session.commit()

    return {"msg": "reply updated successfully"}, 200


@app.route('/reply/<int:reply_id>/delete', methods=['POST'])
@jwt_required()
def delete_reply(reply_id):
    # getting user
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"msg": "error fetching user from JWT token"}, 401

    # checking if the reply exists
    reply = Reply.query.filter_by(id=reply_id).first()
    if not reply:
        return {"msg": "reply not found"}, 404

    # checking if the user is authorized to delete the reply
    if reply.user_id != user.id:
        return {"msg": "unauthorized to delete this reply"}, 403

    # recursively delete all child replies
    def delete_children(reply):
        for child in reply.replies:
            delete_children(child)
            db.session.delete(child)

    delete_children(reply)

    # delete the reply object
    db.session.delete(reply)
    db.session.commit()

    return {"msg": "reply and all its children deleted successfully"}, 200


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
    title = profanity.censor(request.json.get("title", None))
    content = profanity.censor(request.json.get("content", None))

    # validate that params are sent in
    if title is None or content is None:
        return {"msg": "title or content missing"}, 400

    # updating values of post
    post.title = title
    post.content = content
    post.edited = True
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


@app.route('/post/<int:post_id>/like', methods=['GET'])
@jwt_required()
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    current_user_username = get_jwt_identity()
    like = Like.query.filter_by(
        username=current_user_username, post_id=post_id).first()
    channel_id = post.channel_id
    channel = Channel.query.get(channel_id)
    username = get_jwt_identity()

    if like:
        # User has already liked this post, so delete the like
        db.session.delete(like)
        db.session.commit()
    else:
        # User has not yet liked this post, so add a new like
        new_like = Like(username=current_user_username, post_id=post_id)
        db.session.add(new_like)
        db.session.commit()

    posts = [post.to_dict(username=username) for post in channel.posts]
    return posts, 200


@app.route('/reply/<int:reply_id>/like', methods=['GET'])
@jwt_required()
def like_reply(reply_id):
    reply = Reply.query.get_or_404(reply_id)
    post = Post.query.get(reply.post_id)
    current_user_username = get_jwt_identity()
    like = Like.query.filter_by(
        username=current_user_username, reply_id=reply_id).first()
    channel_id = post.channel_id
    channel = Channel.query.get(channel_id)
    username = get_jwt_identity()

    if like:
        # User has already liked this reply, so delete the like
        db.session.delete(like)
        db.session.commit()
    else:
        # User has not yet liked this reply, so add a new like
        new_like = Like(username=current_user_username, reply_id=reply_id)
        db.session.add(new_like)
        db.session.commit()

    posts = [post.to_dict(username=username) for post in channel.posts]
    return posts, 200
