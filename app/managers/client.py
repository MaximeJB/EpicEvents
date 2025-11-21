"""Opérations CRUD pour les clients."""

import re

from app.auth import require_role
from app.models import Client


@require_role("sales", "gestion")
def create_client(db, current_user, name, phone, company, email):
    """Crée un client.

    Le client est automatiquement assigné à l'utilisateur connecté.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        name: Nom du client
        phone: Numéro de téléphone
        company: Nom de l'entreprise
        email: Email du client

    Returns:
        Client créé

    Raises:
        PermissionError: Si le rôle n'est pas autorisé (sales ou gestion)
        ValueError: Si les données sont invalides
    """
    # Validation email
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise ValueError("Format email invalide")

    # Validation téléphone (doit contenir des chiffres)
    if not re.search(r'\d', phone):
        raise ValueError("Le numéro de téléphone doit contenir des chiffres")

    client = Client(name=name, email=email, phone_number=phone, company_name=company, sales_contact_id=current_user.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def list_clients(db, current_user):
    """Liste les clients selon le rôle.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté

    Returns:
        Liste de Client filtrée selon le rôle:
        - Sales: seulement ses clients
        - Support: aucun client
        - Gestion: tous les clients
    """
    if current_user.role.name == "sales":
        return db.query(Client).filter(Client.sales_contact_id == current_user.id).all()
    else:
        return db.query(Client).all()


def get_client(db, client_id):
    """Récupère un client par son ID.

    Args:
        db: Session SQLAlchemy
        client_id: ID du client

    Returns:
        Client trouvé ou None
    """
    return db.query(Client).filter(Client.id == client_id).first()


@require_role("sales", "gestion")
def update_client(db, current_user, client_id, **kwargs):
    """Met à jour un client.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        client_id: ID du client à modifier
        **kwargs: Champs à mettre à jour

    Returns:
        Client modifié

    Raises:
        PermissionError: Si sales tente de modifier un client qui n'est pas le sien
        ValueError: Si le client n'existe pas
    """
    client = get_client(db, client_id)
    if not client:
        raise ValueError("Client not found")

    if current_user.role.name == "sales" and client.sales_contact_id != current_user.id:
        raise PermissionError("L'utilisateur n'a pas la permission de faire ça")

    # Validation des nouvelles valeurs
    if 'email' in kwargs:
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', kwargs['email']):
            raise ValueError("Format email invalide")

    if 'phone_number' in kwargs:
        if not re.search(r'\d', kwargs['phone_number']):
            raise ValueError("Le numéro de téléphone doit contenir des chiffres")

    for key, value in kwargs.items():
        if hasattr(client, key):
            setattr(client, key, value)

    db.commit()
    db.refresh(client)
    return client
