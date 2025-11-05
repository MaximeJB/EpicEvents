"""Opérations CRUD pour les contrats."""
import sentry_sdk

from app.auth import require_role
from app.crud.crud_client import get_client
from app.models import Client, Contract


@require_role("gestion")
def create_contract(db, current_user, status, total_amount, remaining_amount, client_id):
    """Crée un contrat.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        status: Statut du contrat (pending ou signed)
        total_amount: Montant total du contrat
        remaining_amount: Montant restant à payer
        client_id: ID du client

    Returns:
        Contract créé

    Raises:
        PermissionError: Si l'utilisateur n'est pas gestion
        ValueError: Si le client n'existe pas
    """
    client = get_client(db, client_id)
    if not client:
        raise ValueError("Client not found")
    contract = Contract(status = status, total_amount=total_amount, remaining_amount=remaining_amount, client_id=client_id)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def get_contract(db, contract_id):
    """Récupère un contrat par son ID.

    Args:
        db: Session SQLAlchemy
        contract_id: ID du contrat

    Returns:
        Contract trouvé ou None
    """
    return db.query(Contract).filter(Contract.id == contract_id).first()


@require_role("sales", "gestion")
def update_contract(db, current_user, contract_id, **kwargs):
    """Met à jour un contrat.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        contract_id: ID du contrat à modifier
        **kwargs: Champs à mettre à jour

    Returns:
        Contract modifié

    Raises:
        PermissionError: Si sales tente de modifier un contrat qui n'est pas le sien
        ValueError: Si le contrat n'existe pas
    """
    contract = get_contract(db, contract_id)
    if not contract:
        raise ValueError("Contract not found")

    if current_user.role.name == "sales" and contract.client.sales_contact_id != current_user.id:
        raise PermissionError("L'utilisateur n'a pas la permission de faire ça")

    old_status = contract.status

    for key,value, in kwargs.items():
        if hasattr(contract, key):
            setattr(contract, key, value)

    db.commit()
    db.refresh(contract)

    if contract.status == "signed" and old_status != "signed":
        sentry_sdk.capture_message(
            f"Contrat signé : ID {contract.id} pour client {contract.client.name} par {current_user.email}",
            level="info"
        )

    return contract


@require_role("gestion", "support", "sales")
def list_contracts(db, current_user):
    """Liste les contrats selon le rôle.

    Args:
        db: Session SQLAlchemy
        current_user: User connecté

    Returns:
        Liste de Contract filtrée selon le rôle:
        - Sales: contrats de ses clients
        - Support: tous les contrats
        - Gestion: tous les contrats
    """
    if current_user.role.name == "gestion":
        return db.query(Contract).all()
    elif current_user.role.name == "support":
        return db.query(Contract).all()
    else:
        return db.query(Contract).join(Client).filter(Client.sales_contact_id == current_user.id).all()
