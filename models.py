# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    gesture_sequence = db.Column(db.JSON, nullable=False)
    session_token = db.Column(db.String(100))