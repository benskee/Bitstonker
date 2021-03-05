from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    price = db.Column(db.String(50), nullable=False)
