import json
import os
import re
import bcrypt
from datetime import datetime, timedelta, timezone
from flask import request, jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required
from api import app, db
from api.models import User, Post, Channel, Category, Reply, Like, Role, Dislike
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
        return {"msg": "Username or password missing."}, 400

    if len(username) < 3 or len(username) > 20:
        return {"msg": "Username must be between 3 and 20 characters."}, 400

    if len(password) < 4 or len(password) > 30:
        return {"msg": "Password must be between 4 and 30 characters."}, 400

    # check for illegal characters
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return {"msg": "Username contains illegal characters."}, 400

    # check for profanity
    if (profanity.contains_profanity(username)):
        return {"msg": "Please choose a different username."}, 400

    # convert username to lowercase
    lc_username = username.lower()

    # check if user already exists (case insensitive)
    queried_user = User.query.filter(User.username.ilike(lc_username)).first()
    if queried_user:
        return {"msg": "User already exists."}, 409

    # check if restricted mode is enabled and if user is allowed to sign up
    if restricted_mode:
        if lc_username not in allowed_usernames:
            return {"msg": "Signup is currently restricted, please try again later."}, 403

    # creating a new user and adding it to the users table
    user = User(username=lc_username, display_name=username, role_id=1,
                password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()))
    db.session.add(user)
    db.session.commit()

    role = Role.query.filter(Role.id == user.role_id).first()
    if role:
        role = role.name

    # login user
    access_token = create_access_token(identity=lc_username)

    return {
        "username": lc_username,
        "display_name": username,
        "role_id": user.role_id,
        "role": role,
        "access_token": access_token
    }, 201


@app.route('/signin', methods=["POST"])
def signin():
    # get query params
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    # validate that params are sent in
    if username is None or password is None:
        return {"msg": "Username or password missing"}, 400

    if len(username) < 3 or len(username) > 20:
        return {"msg": "Username must be between 3 and 20 characters."}, 400

    # convert username to lowercase
    lc_username = username.lower()

    # get user by username (case insensitive)
    user = User.query.filter(User.username.ilike(lc_username)).first()

    # if user doesn't exist or the password is incorrect, we return unauthorized
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return {"msg": "Incorrect username or password"}, 401

    # get role
    role_id = user.role_id
    if role_id == None:
        role_id = 1

    role = Role.query.filter(Role.id == role_id).first()
    if role:
        role = role.name

    # creating jwt token and returning it
    access_token = create_access_token(identity=lc_username)
    return {
        "username": lc_username,
        "display_name": user.display_name,
        "role_id": role_id,
        "role": role,
        "access_token": access_token
    }, 200


@app.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"msg": "Logout successful"})
    unset_jwt_cookies(response)
    return response


# this is just a dummy endpoint to check if your JWT auth is working
# it will return back the username associated with your JWT token
@app.route('/identity')
@jwt_required()
def my_profile():
    user = User.query.filter(User.username.ilike(get_jwt_identity())).first()
    role = Role.query.filter(Role.id == user.role_id).first().name
    if role:
        role = role.name
    return {
        "username": user.username,
        "display_name": user.display_name,
        "role_id": user.role_id,
        "role": role,
    }, 200


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
        return {"msg": "Channel not found"}, 404

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
        return {"msg": "Title, content, or channel_id missing"}, 400

    # getting user
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"msg": "Error fetching user from JWT token"}, 401

    # checking if the channel exists
    channel = Channel.query.filter_by(id=channel_id).first()
    if not channel:
        return {"msg": "Channel not found"}, 404

    # creating and adding the new post to the specified channel
    post = Post(title=title, content=content, author=user, channel=channel)
    db.session.add(post)
    db.session.commit()

    return {"msg": "Post created successfully"}, 200


@app.route('/reply/<int:item_id>', methods=['POST'])
@jwt_required()
def create_reply(item_id):
    # get query params
    content = profanity.censor(request.json.get("content", None))
    parent_reply_id = request.json.get("parent_reply_id", None)

    # validate that params are sent in
    if content is None:
        return {"msg": "Content missing"}, 400

    # getting user
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"msg": "Error fetching user"}, 401

    # checking if the post exists
    post = Post.query.filter_by(id=item_id).first()
    if not post:
        return {"msg": "Post not found"}, 404

    # Declare parent_reply outside of the conditional block
    parent_reply = None

    # Determine if this is a reply to a post or to another reply
    if parent_reply_id:
        parent_reply = Reply.query.filter_by(id=parent_reply_id).first()
        if not parent_reply:
            return {"msg": "Parent reply not found"}, 404
        depth = parent_reply.depth + 1
    else:
        depth = 0

    if depth > 5:
        return {"msg": "Maximum nesting level exceeded"}, 400

    # create new reply object
    reply = Reply(content=content, username=username, post=post,
                  parent_reply=parent_reply, depth=depth)
    db.session.add(reply)
    db.session.commit()

    return {"msg": "Reply created successfully"}, 201


@app.route('/delete/<item_type>/<int:item_id>', methods=['POST'])
@jwt_required()
def delete_item(item_type, item_id):
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"msg": "Error fetching user from JWT token"}, 401

    # checking if the item exists
    if item_type == 'post':
        item = Post.query.filter_by(id=item_id).first()
    elif item_type == 'reply':
        item = Reply.query.filter_by(id=item_id).first()
    else:
        return {"msg": "Invalid item type"}, 400

    if not item:
        return {"msg": "Item not found"}, 404

    # checking if the user is authorized to delete the item
    if item_type == 'post' and item.author != user:
        return {"msg": "Unauthorized to delete this post"}, 403
    elif item_type == 'reply' and item.username != username:
        return {"msg": "Unauthorized to delete this reply"}, 403

    # recursively delete all child items
    def delete_children(item):
        for child in item.replies:
            delete_children(child)
            db.session.delete(child)

    delete_children(item)

    # delete the item object
    db.session.delete(item)
    db.session.commit()

    return {"msg": item_type.capitalize() + " deleted successfully"}, 200


@app.route('/edit/<item_type>/<int:item_id>', methods=['POST'])
@jwt_required()
def update_item(item_type, item_id):
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"msg": "Error fetching user"}, 401

    # checking if the item is valid
    if item_type == 'post':
        item = Post.query.filter_by(id=item_id).first()
    elif item_type == 'reply':
        item = Reply.query.filter_by(id=item_id).first()
    else:
        return {"msg": "Invalid item type"}, 400

    if not item:
        return {"msg": "Item not found"}, 404

    # checking if the user is authorized to update the item
    if item_type == 'post' and item.author != user:
        return {"msg": "Unauthorized to update this post"}, 403
    elif item_type == 'reply' and item.username != username:
        return {"msg": "Unauthorized to update this reply"}, 403

    # validate that params are sent in
    if item_type == 'post':
        title = profanity.censor(request.json.get("title", None))

        if title is None:
            return {"msg": "Title missing"}, 400

        item.title = title

    content = profanity.censor(request.json.get("content", None))

    if content is None:
        return {"msg": "Content missing"}, 400

    # update the item object
    item.content = content
    item.edited = True
    item.edited_date = datetime.utcnow()
    db.session.commit()

    return {"msg": item_type.capitalize() + " updated successfully"}, 200


@app.route('/like/<item_type>/<int:item_id>', methods=['POST'])
@jwt_required()
def like_item(item_type, item_id):
    username = get_jwt_identity()
    if not username:
        return {"msg": "Error fetching user"}, 401

    # checking if the item exists
    if item_type == 'post':
        like_query = Like.query.filter_by(username=username, post_id=item_id)
        dislike_query = Dislike.query.filter_by(
            username=username, post_id=item_id)
    elif item_type == 'reply':
        like_query = Like.query.filter_by(username=username, reply_id=item_id)
        dislike_query = Dislike.query.filter_by(
            username=username, reply_id=item_id)
    else:
        return {"msg": "Invalid item type"}, 400

    username = get_jwt_identity()

    like = like_query.first()

    if like:
        # User has already liked this item, so remove the like
        db.session.delete(like)
    else:
        dislike = dislike_query.first()
        if dislike:
            # User has disliked this item, so remove the dislike
            db.session.delete(dislike)
        # add a new like
        if item_type == 'post':
            new_like = Like(username=username, post_id=item_id)
        elif item_type == 'reply':
            new_like = Like(username=username, reply_id=item_id)
        db.session.add(new_like)
    db.session.commit()

    return {}, 200


@app.route('/dislike/<item_type>/<int:item_id>', methods=['POST'])
@jwt_required()
def dislike_item(item_type, item_id):
    username = get_jwt_identity()
    if not username:
        return {"msg": "Error fetching user"}, 401

    # checking if the item exists
    if item_type == 'post':
        like_query = Like.query.filter_by(username=username, post_id=item_id)
        dislike_query = Dislike.query.filter_by(
            username=username, post_id=item_id)
    elif item_type == 'reply':
        like_query = Like.query.filter_by(username=username, reply_id=item_id)
        dislike_query = Dislike.query.filter_by(
            username=username, reply_id=item_id)
    else:
        return {"msg": "Invalid item type"}, 400

    username = get_jwt_identity()

    dislike = dislike_query.first()

    if dislike:
        # User has already disliked this item, so remove the dislike
        db.session.delete(dislike)
    else:
        like = like_query.first()
        if like:
            # User has liked this item, so remove the like
            db.session.delete(like)
        # add a new dislike
        if item_type == 'post':
            new_dislike = Dislike(username=username, post_id=item_id)
        elif item_type == 'reply':
            new_dislike = Dislike(username=username, reply_id=item_id)
        db.session.add(new_dislike)
    db.session.commit()

    return {}, 200