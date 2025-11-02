from app.crud.crud_client import get_client
from app.auth import require_role
from app.models import Contract, Client


@require_role("gestion")
def create_contract(db, current_user, total_amount, remaining_amount, client_id):
    client = get_client(db, client_id)
    if not client: 
        raise ValueError("Client not found")
    contract = Contract(total_amount=total_amount, remaining_amount=remaining_amount, client_id=client_id)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract

def get_contract(db, contract_id):
    return db.query(Contract).filter(Contract.id == contract_id).first()

@require_role("sales", "gestion")
def update_contract(db, current_user, contract_id, **kwargs):
    contract = get_contract(db, contract_id)
    if not contract:
        raise ValueError("Contract not found")
    
    if current_user.role.name == "sales" and contract.client.sales_contact_id != current_user.id:
        raise PermissionError("L'utilisateur n'a pas la permission de faire ça")
    
    for key,value, in kwargs.items():
        if hasattr(contract, key):
            setattr(contract, key, value)

    db.commit()
    db.refresh(contract)
    return contract

@require_role("gestion", "support", "sales")
def list_contracts(db, current_user):
    if current_user.role.name == "gestion":
        return db.query(Contract).all()
    elif current_user.role.name == "support":
        return db.query(Contract).all()
    else: 
        return db.query(Contract).join(Client).filter(Client.sales_contact_id == current_user.id).all()
