from datetime import datetime
from api import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    replies = db.relationship('Reply', backref='writer', lazy=True)

    def __repr__(self):
        return f"User <{self.username}>"

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    channels = db.relationship('Channel', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    posts = db.relationship('Post', backref='channel', lazy=True)

    def __repr__(self):
        return f"Channel <{self.name}>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'posts': [post.to_dict() for post in self.posts]
        }

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    replies = db.relationship('Reply', backref='original', lazy=True)

    def __repr__(self):
        return f"Post <{self.title}> by <{self.user_id}> Posted at: {self.date}"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author.to_dict(),
            'date': self.date.strftime("%Y-%m-%d %H:%M:%S"),
            'replies': [reply.to_dict() for reply in self.replies]
        }

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    def __repr__(self):
        return f"Reply <{self.title}> by <self.user_id> replied at: {self.date}"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'writer': self.writer.to_dict(),
            'date': self.date.strftime("%Y-%m-%d %H:%M:%S"),
            'post_id': self.post_id,
        }