from app.auth import require_role
from app.models import Client
from sqlalchemy.orm import Session


@require_role("sales", "gestion")
def create_client(db, current_user, name, phone, company):
    """
    Crée un client.
    
    Permissions: 
    
        Sales : ✓ (le client  lui sera assigné automatiquement)
        Support : ✗
        Gestion : ✓
        
    Args:
        db: Session SQLAlchemy
        current_user: User connecté (vient de auth.get_current_user)
        name, phone, company: Infos du client
        
    Returns:
        Client créé
        
    Raises:
        PermissionError: Si le rôle n'est pas autorisé
    """
    client = Client(name=name, 
                    phone_number=phone, 
                    company_name=company,
                    sales_contact_id=current_user.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def list_clients(db, current_user):
    """
    Liste les clients selon le rôle.
    
    Logique métier:
        - Sales : SEULEMENT ses clients (sales_contact_id == current_user.id)
        - Support : Aucun client (pas dans leurs attributions)
        - Gestion : TOUS les clients
        
    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        
    Returns:
        Liste de Client
    """
    if current_user.role.name == "sales":
        return db.query(Client).filter(Client.sales_contact_id == current_user.id).all()
    else: 
        return db.query(Client).all()
    
def get_client(db: Session, client_id):
        return db.query(Client).filter(Client.id == client_id).first()


    

@require_role("sales", "gestion")
def update_client(db, current_user, client_id: int, **kwargs):
    """
    Met à jour un client.
    
    Permissions:
        - Sales : Seulement SES clients
        - Support : ✗
        - Gestion : Tous les clients
        
    Args:
        db: Session SQLAlchemy
        current_user: User connecté
        client_id: ID du client à modifier
        **kwargs: Champs à mettre à jour (ex: name="Nouveau nom")
        
    Returns:
        Client modifié
        
    Raises:
        PermissionError: Si pas autorisé
        ValueError: Si client_id n'existe pas
    """
    client = get_client(db, client_id)
    if not client:
         raise ValueError("Client not found")
    
    if current_user.role.name == "sales" and client.sales_contact_id != current_user.id:
        raise PermissionError("L'utilisateur n'a pas la permission de faire ça")
    
    for key, value in kwargs.items():
         if hasattr(client, key):
              setattr(client, key, value)
    
    db.commit()
    db.refresh(client)
    return client
    