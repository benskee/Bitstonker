from app import db
from app.models import User

print(User.query.get(1877).price)