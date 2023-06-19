from datetime import datetime
from api import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    display_name = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, nullable=False)
    role = db.relationship('Role', primaryjoin="foreign(Role.id)==User.role_id", backref='users', uselist=False)
    posts = db.relationship('Post', backref='author', lazy=True, primaryjoin="foreign(Post.username)==User.username")
    replies = db.relationship('Reply', backref='author', lazy=True, primaryjoin="foreign(Reply.username)==User.username")

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name
        }

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    channels = db.relationship('Channel', backref='category', lazy=True, primaryjoin="foreign(Channel.category_id)==Category.id")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, nullable=False)
    posts = db.relationship('Post', backref='channel', lazy=True, primaryjoin="foreign(Post.channel_id)==Channel.id")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }
    
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    post_id = db.Column(db.Integer)
    reply_id = db.Column(db.Integer)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    channel_id = db.Column(db.Integer, nullable=False)
    replies = db.relationship('Reply', backref='post', lazy=True, primaryjoin="foreign(Reply.post_id)==Post.id")
    edited = db.Column(db.Boolean, nullable=False, default=False)
    edited_date = db.Column(db.DateTime, nullable=True)
    likes = db.relationship('Like', backref='post', lazy=True, primaryjoin="Like.post_id==Post.id", foreign_keys="Like.post_id")
    likes = db.relationship('Like', backref='post', lazy=True, primaryjoin="foreign(Like.post_id)==Post.id")

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
    username = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    post_id = db.Column(db.Integer)
    parent_reply_id = db.Column(db.Integer)
    depth = db.Column(db.Integer, nullable=False)
    replies = db.relationship('Reply', backref=db.backref('parent_reply', remote_side=[id]), lazy='joined', primaryjoin="foreign(Reply.parent_reply_id)==Reply.id")
    edited = db.Column(db.Boolean, nullable=False, default=False)
    edited_date = db.Column(db.DateTime, nullable=True)
    likes = db.relationship('Like', backref='reply', lazy=True, primaryjoin="Like.reply_id==Reply.id", foreign_keys="Like.reply_id")
    likes = db.relationship('Like', backref='reply', lazy=True, primaryjoin="foreign(Like.reply_id)==Reply.id")

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