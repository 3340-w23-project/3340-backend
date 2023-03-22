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

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    replies = db.relationship('Reply', backref='original', lazy=True)

    def __repr__(self):
        return f"Post <{self.title}> by <{self.user_id}> Posted at: {self.date}"

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    def __repr__(self):
        return f"Reply <{self.title}> by <self.user_id> replied at: {self.date}"
