from app.crud.crud_client import get_client
from app.crud.crud_contract import get_contract
from app.auth import require_role
from app.models import Contract, Client, Event


@require_role("sales")
def create_event(db, current_user, start_date, end_date, location, attendees, contract_id):
    contract = get_contract(db, contract_id)
    if not contract:
        raise ValueError("Contract not found")
    if contract.status != "signed":
        raise ValueError("Le contrat doit être signé")
    if contract.client.sales_contact_id != current_user.id:
        raise PermissionError("Vous ne pouvez créer un événements que pour vos client")

    event = Event(start_date=start_date, end_date=end_date, location=location, attendees=attendees, contract_id=contract_id)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def get_event(db, event_id):
    return db.query(Event).filter(Event.id == event_id).first()

@require_role("support", "gestion")
def update_event(db, current_user, event_id, **kwargs):
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
    if current_user.role.name == "gestion":
        return db.query(Event).all()
    elif current_user.role.name == "support":
        return db.query(Event).filter(Event.support_contact_id == current_user.id).all()
    else: 
        return db.query(Event).join(Contract).join(Client).filter(Client.sales_contact_id == current_user.id).all()
