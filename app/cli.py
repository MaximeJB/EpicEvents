from app.db import SessionLocal
from app.crud.crud_user import create_user

create_user(SessionLocal(),"email@email.fr","secret123")