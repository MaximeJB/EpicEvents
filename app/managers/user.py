"""Opérations CRUD pour les utilisateurs."""

import re

import sentry_sdk

from app.auth import hash_password, require_role
from app.models import User


@require_role("gestion")
def create_user(db, current_user, email, password, name, department, role_id):
    """Crée un utilisateur.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        email: Email de l'utilisateur
        password: Mot de passe en clair (sera haché)
        name: Nom de l'utilisateur
        department: Département de l'utilisateur
        role_id: ID du rôle

    Returns:
        User créé

    Raises:
        PermissionError: Si l'utilisateur n'est pas gestion
        ValueError: Si les données sont invalides
    """
    # Validation email
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise ValueError("Format email invalide")

    # Validation mot de passe (minimum 8 caractères)
    if len(password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères")

    # Validation département
    valid_departments = ['sales', 'support', 'gestion']
    if department not in valid_departments:
        raise ValueError(f"Le département doit être l'un des suivants : {', '.join(valid_departments)}")

    hashed_password = hash_password(password)
    new_user = User(email=email, password_hash=hashed_password, name=name, department=department, role_id=role_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    sentry_sdk.capture_message(
        f"Collaborateur créé : {new_user.email} (ID: {new_user.id}) par {current_user.email}", level="info"
    )

    return new_user


def get_user(db, email):
    """Récupère un utilisateur par son email.

    Args:
        db: Session SQLAlchemy
        email: Email de l'utilisateur

    Returns:
        User trouvé ou None
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db, user_id):
    """Récupère un utilisateur par son ID.

    Args:
        db: Session SQLAlchemy
        user_id: ID de l'utilisateur

    Returns:
        User trouvé ou None
    """
    return db.query(User).filter(User.id == user_id).first()


@require_role("gestion")
def list_users(db, current_user):
    """Liste tous les utilisateurs.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté

    Returns:
        Liste de tous les User

    Raises:
        PermissionError: Si l'utilisateur n'est pas gestion
    """
    return db.query(User).all()


@require_role("gestion")
def update_user(db, current_user, user_id, **kwargs):
    """Met à jour un utilisateur.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        user_id: ID de l'utilisateur à modifier
        **kwargs: Champs à mettre à jour

    Returns:
        User modifié

    Raises:
        PermissionError: Si l'utilisateur n'est pas gestion
        ValueError: Si l'utilisateur n'existe pas
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")

    # Validation des nouvelles valeurs
    if 'email' in kwargs:
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', kwargs['email']):
            raise ValueError("Format email invalide")

    if 'department' in kwargs:
        valid_departments = ['sales', 'support', 'gestion']
        if kwargs['department'] not in valid_departments:
            raise ValueError(f"Le département doit être l'un des suivants : {', '.join(valid_departments)}")

    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)

    sentry_sdk.capture_message(
        f"Collaborateur modifié : {user.email} (ID: {user.id}) par {current_user.email}", level="info"
    )

    return user


@require_role("gestion")
def delete_user(db, current_user, user_id):
    """Supprime un utilisateur.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        user_id: ID de l'utilisateur à supprimer

    Returns:
        True si la suppression a réussi

    Raises:
        PermissionError: Si l'utilisateur n'est pas gestion
        ValueError: Si l'utilisateur n'existe pas
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")

    db.delete(user)
    db.commit()
    return True
