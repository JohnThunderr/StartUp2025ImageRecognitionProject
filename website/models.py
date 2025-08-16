from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    
    # Role controls which dashboard users see. 'customer' or 'developer'
    role = db.Column(db.String(50), default="customer")
    
    # Track when the user account was created
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())