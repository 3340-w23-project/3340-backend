from datetime import datetime
from api import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    display_name = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True, primaryjoin="Post.user_id==User.id", foreign_keys="Post.user_id")
    replies = db.relationship('Reply', backref='author', lazy='joined', primaryjoin="Reply.user_id==User.id", foreign_keys="Reply.user_id")

    def __repr__(self):
        return f"User <{self.username}>"

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    channels = db.relationship('Channel', backref='category', lazy=True, primaryjoin="Channel.category_id==Category.id", foreign_keys="Channel.category_id")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, nullable=False)
    posts = db.relationship('Post', backref='channel', lazy=True, primaryjoin="Post.channel_id==Channel.id", foreign_keys="Post.channel_id")

    def __repr__(self):
        return f"Channel <{self.name}>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'posts': [post.to_dict() for post in self.posts]
        }
    
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    post_id = db.Column(db.Integer)
    reply_id = db.Column(db.Integer)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Like <{self.user_id}> on <{self.post_id or self.reply_id}> at: {self.date}"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    channel_id = db.Column(db.Integer, nullable=False)
    replies = db.relationship('Reply', backref='post', lazy=True, primaryjoin="Reply.post_id==Post.id", foreign_keys="Reply.post_id")
    edited = db.Column(db.Boolean, nullable=False, default=False)
    likes = db.relationship('Like', backref='post', lazy=True, primaryjoin="Like.post_id==Post.id", foreign_keys="Like.post_id")

    def __repr__(self):
        return f"Post <{self.title}> by <{self.user_id}> Posted at: {self.date}"

    def to_dict(self, username=None):
        result = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author.to_dict(),
            'date': self.date.strftime("%Y-%m-%d %H:%M:%S"),
            'likes': len(self.likes),
            'liked': False,
        }
        if self.replies:
            result['replies'] = [reply.to_dict(username=username) for reply in self.replies if not reply.parent_reply_id]
        if self.edited:
            result['edited'] = True
        if username:
            like = Like.query.filter_by(username=username, post_id=self.id).first()
            if like:
                result['liked'] = True
        return result

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer)
    parent_reply_id = db.Column(db.Integer)
    depth = db.Column(db.Integer, nullable=False)
    replies = db.relationship('Reply', backref=db.backref('parent_reply', remote_side=[id]), lazy='joined', primaryjoin="Reply.parent_reply_id==Reply.id", foreign_keys="Reply.parent_reply_id")
    edited = db.Column(db.Boolean, nullable=False, default=False)
    likes = db.relationship('Like', backref='reply', lazy=True, primaryjoin="Like.reply_id==Reply.id", foreign_keys="Like.reply_id")

    def __repr__(self):
        return f"Reply <{self.content}> by <{self.user_id}> to <{self.post_id}> Posted at: {self.date}"

    def to_dict(self, username=None):
        result = {
            'id': self.id,
            'content': self.content,
            'author': self.author.to_dict(),
            'date': self.date.strftime("%Y-%m-%d %H:%M:%S"),
            'depth': self.depth,
            'likes': len(self.likes),
            'liked': False,
        }
        if self.parent_reply_id:
            result['parent_reply'] = self.parent_reply_id
        if self.replies:
            result['replies'] = [reply.to_dict(username=username) for reply in self.replies]
        if self.edited:
            result['edited'] = True
        if username:
            like = Like.query.filter_by(username=username, reply_id=self.id).first()
            if like:
                result['liked'] = True
        return result