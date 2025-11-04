

import jwt
import os
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC
from argon2 import PasswordHasher
from app.models import User

SECRET_KEY = os.getenv("SECRET_KEY")
ph = PasswordHasher()


def create_token(user_id, role):
    payload = { 
        "user_id" : user_id,
        "role": role,
        "exp" : datetime.now(UTC) + timedelta(hours=24)
        }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token):
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

def save_token(token):
    with open(".epicevents_token", "w") as f:
        f.write(token)

def load_token_locally() -> str | None:
    """Charge le token si il existe."""
    try:
        with open(".epicevents_token", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def hash_password(plain_password):
    return ph.hash(plain_password)

def verify_password(hashed_password, plain_password):
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except:
        return False


def login(db: Session, email, password):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return False
    if not verify_password(user.password_hash, password):
        return False
    
    token = create_token(user.id, user.role.name)
    save_token(token)
    return True


def get_current_user(db):
    """
    Récupère l'utilisateur actuellement connecté.
    
    Process:
        1. Charger le token local
        2. Décoder le JWT
        3. Récupérer le user depuis la DB
        
    Args:
        db: Session SQLAlchemy
        
    Returns:
        User si connecté, None sinon
        
    Gestion d'erreurs:
        - Token inexistant → return None
        - Token expiré → supprimer le token + return None
        - Token invalide → return None
    """
     
    token = load_token_locally()

    if token is None:
        return None
    
    try : 
        payload =  decode_token(token)
    except jwt.ExpiredSignatureError:
        return None 
    except jwt.InvalidTokenError:
        return None
    
    user_id = payload["user_id"]
    user = db.query(User).filter(User.id == user_id).first()
    return user

def require_role(*allowed_roles):
    """
    Décorateur pour vérifier qu'un utilisateur a le bon rôle.

    Usage dans crud.py:
        @require_role("sales", "gestion")
        def create_client(db, current_user, ...):
            Cette fonction ne s'exécute que si current_user.role.name
            est "sales" ou "gestion"
            ...

    Les superusers (is_superuser=True) bypass toutes les vérifications de permissions.

    Args:
        *allowed_roles: Liste des rôles autorisés (strings)

    Raises:
        PermissionError: Si le rôle de current_user n'est pas autorisé
    """
    def decorator(func):
        def wrapper(db, current_user, *args, **kwargs):
            if hasattr(current_user, 'is_superuser') and current_user.is_superuser:
                return func(db, current_user, *args, **kwargs)

            if current_user.role.name not in allowed_roles:
                raise PermissionError(f"L'utilisateur ne dispose pas du bon rôle pour cette action")
            return func(db, current_user, *args, **kwargs)
        return wrapper
    return decorator


