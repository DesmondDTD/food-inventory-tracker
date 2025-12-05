from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# --- User Model ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # One-to-many relationship: one user can have many items
    items = db.relationship('Item', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


# --- Item Model ---
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50))
    expiration_date = db.Column(db.DateTime, nullable=True)  
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Foreign key to link item to a user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Item {self.name}>'

