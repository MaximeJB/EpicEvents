from sqlalchemy.orm import Session
from app.models import User
from app.auth import hash_password


def create_user(db: Session, email, password, name, department, role_id):
    hashed_password = hash_password(password)
    new_user = User(email=email, 
                    password_hash=hashed_password, 
                    name=name, 
                    department=department, 
                    role_id=role_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user(db, email):
    return db.query(User).filter(User.email == email).first()