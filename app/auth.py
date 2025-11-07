"""Module d'authentification et d'autorisation pour Epic Events CRM.

Ce module gère le hachage de mots de passe avec Argon2, la création et décodage
de tokens JWT, ainsi que le système de permissions basé sur les rôles.
"""

import os
from datetime import datetime, timedelta, UTC

from argon2 import PasswordHasher
import jwt


SECRET_KEY = os.getenv("SECRET_KEY")
ph = PasswordHasher()


def create_token(user_id, role):
    """Crée un token JWT pour un utilisateur.

    Args:
        user_id: ID de l'utilisateur
        role: Rôle de l'utilisateur

    Returns:
        Token JWT encodé avec expiration de 24h
    """
    payload = {"user_id": user_id, "role": role, "exp": datetime.now(UTC) + timedelta(hours=24)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token):
    """Décode un token JWT.

    Args:
        token: Token JWT encodé

    Returns:
        Payload décodé du token
    """
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


def save_token(token):
    """Sauvegarde le token dans un fichier local.

    Args:
        token: Token JWT à sauvegarder
    """
    with open(".epicevents_token", "w") as f:
        f.write(token)


def load_token_locally():
    """Charge le token depuis le fichier local.

    Returns:
        Token JWT si le fichier existe, None sinon
    """
    try:
        with open(".epicevents_token", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def hash_password(plain_password):
    """Hache un mot de passe avec Argon2.

    Args:
        plain_password: Mot de passe en clair

    Returns:
        Mot de passe haché
    """
    return ph.hash(plain_password)


def verify_password(hashed_password, plain_password):
    """Vérifie un mot de passe contre son hash.

    Args:
        hashed_password: Hash Argon2 stocké
        plain_password: Mot de passe en clair à vérifier

    Returns:
        True si le mot de passe est correct, False sinon
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except Exception:
        return False


def login(db, email, password):
    """Authentifie un utilisateur et crée un token.

    Args:
        db: Session SQLAlchemy
        email: Email de l'utilisateur
        password: Mot de passe en clair

    Returns:
        True si l'authentification réussit et le token est créé, False sinon
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return False
    if not verify_password(user.password_hash, password):
        return False

    token = create_token(user.id, user.role.name)
    save_token(token)
    return True


def get_current_user(db):
    """Récupère l'utilisateur actuellement connecté.

    Args:
        db: Session SQLAlchemy

    Returns:
        User si connecté, None sinon

    Raises:
        jwt.ExpiredSignatureError: Si le token est expiré
        jwt.InvalidTokenError: Si le token est invalide
    """
    token = load_token_locally()

    if token is None:
        return None

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

    user_id = payload["user_id"]
    user = db.query(User).filter(User.id == user_id).first()
    return user


def require_role(*allowed_roles):
    """Décorateur pour vérifier qu'un utilisateur a le bon rôle.

    Les superusers (is_superuser=True) bypass toutes les vérifications.

    Args:
        *allowed_roles: Liste des rôles autorisés (strings)

    Returns:
        Fonction décorée qui vérifie les permissions

    Raises:
        PermissionError: Si le rôle de current_user n'est pas autorisé

    Example:
        @require_role("sales", "gestion")
        def create_client(db, current_user, ...):
            pass
    """

    def decorator(func):
        def wrapper(db, current_user, *args, **kwargs):
            if hasattr(current_user, 'is_superuser') and current_user.is_superuser:
                return func(db, current_user, *args, **kwargs)

            if current_user.role.name not in allowed_roles:
                raise PermissionError("L'utilisateur ne dispose pas du bon rôle pour cette action")
            return func(db, current_user, *args, **kwargs)

        return wrapper

    return decorator
