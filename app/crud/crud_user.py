from sqlalchemy.orm import Session
from app.models import User
from app.auth import hash_password, require_role


@require_role("gestion")
def create_user(db, current_user, 
                email, 
                password, 
                name, 
                department, 
                role_id):
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

def get_user_by_id(db, user_id):
    return db.query(User).filter(User.id == user_id).first()

@require_role("gestion")
def list_users(db, current_user):
    return db.query(User).all()

@require_role("gestion")
def update_user(db, current_user, user_id, **kwargs):
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")

    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user

@require_role("gestion")
def delete_user(db, current_user, user_id):
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")

    db.delete(user)
    db.commit()
    return True