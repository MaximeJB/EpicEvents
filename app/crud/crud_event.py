"""Opérations CRUD pour les événements."""
from app.auth import require_role
from app.crud.crud_contract import get_contract
from app.crud.crud_user import get_user_by_id
from app.models import Client, Contract, Event


@require_role("sales")
def create_event(db, current_user, start_date, end_date, location, attendees, contract_id, notes=None):
    """Crée un événement.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        start_date: Date de début de l'événement
        end_date: Date de fin de l'événement
        location: Lieu de l'événement
        attendees: Nombre de participants
        contract_id: ID du contrat associé
        notes: Notes additionnelles (optionnel)

    Returns:
        Event créé

    Raises:
        PermissionError: Si l'utilisateur n'est pas sales ou si le client n'est pas le sien
        ValueError: Si le contrat n'existe pas ou n'est pas signé
    """
    contract = get_contract(db, contract_id)
    if not contract:
        raise ValueError("Contract not found")
    if contract.status != "signed":
        raise ValueError("Le contrat doit être signé")
    if contract.client.sales_contact_id != current_user.id:
        raise PermissionError("Vous ne pouvez créer un événements que pour vos client")

    event = Event(start_date=start_date, end_date=end_date, location=location, attendees=attendees, contract_id=contract_id, notes=notes)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db, event_id):
    """Récupère un événement par son ID.

    Args:
        db: Session SQLAlchemy
        event_id: ID de l'événement

    Returns:
        Event trouvé ou None
    """
    return db.query(Event).filter(Event.id == event_id).first()


@require_role("support", "gestion")
def update_event(db, current_user, event_id, **kwargs):
    """Met à jour un événement.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        event_id: ID de l'événement à modifier
        **kwargs: Champs à mettre à jour

    Returns:
        Event modifié

    Raises:
        PermissionError: Si support tente de modifier un événement qui n'est pas le sien
        ValueError: Si l'événement n'existe pas
    """
    event = get_event(db, event_id)
    if not event:
        raise ValueError("L'événement n'existe pas")
    if current_user.role.name == "support" :
        if event.support_contact_id != current_user.id:
            raise PermissionError("Vous ne pouvez modifier un événements que pour vos client")

    for key,value, in kwargs.items():
        if hasattr(event, key):
                setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return event


@require_role("sales", "support", "gestion")
def list_events(db, current_user):
    """Liste les événements selon le rôle.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté

    Returns:
        Liste d'Event filtrée selon le rôle:
        - Sales: événements de ses clients
        - Support: événements qui lui sont assignés
        - Gestion: tous les événements
    """
    if current_user.role.name == "gestion":
        return db.query(Event).all()
    elif current_user.role.name == "support":
        return db.query(Event).filter(Event.support_contact_id == current_user.id).all()
    else:
        return db.query(Event).join(Contract).join(Client).filter(Client.sales_contact_id == current_user.id).all()


@require_role("gestion")
def assign_support(db, current_user, event_id, support_user_id):
    """Assigne un support à un événement.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        event_id: ID de l'événement
        support_user_id: ID de l'utilisateur support à assigner

    Returns:
        Event modifié

    Raises:
        PermissionError: Si l'utilisateur n'est pas gestion
        ValueError: Si l'événement ou le support n'existe pas, ou si l'utilisateur n'est pas support
    """
    event = get_event(db, event_id)
    if not event:
        raise ValueError("L'événement n'existe pas")

    support_user = get_user_by_id(db, support_user_id)
    if not support_user:
        raise ValueError("L'utilisateur support n'existe pas")

    if support_user.role.name != "support":
        raise ValueError("L'utilisateur doit avoir le rôle 'support'")

    event.support_contact_id = support_user_id
    db.commit()
    db.refresh(event)
    return event
