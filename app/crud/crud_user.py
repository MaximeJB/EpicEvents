from sqlalchemy.orm import Session
from app.models import User
from app.auth import hash_password


def create_user(db: Session, email, password):
    hashed_password = hash_password(password)
    new_user = User(email=email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

