

"""
Configuration pytest et fixtures réutilisables.

Ce fichier contient :
- Configuration de la base de données de test
- Fixtures pour créer des objets de test (users, roles, etc.)
- Setup/teardown pour isoler les tests
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Role, User, Client, Contract, Event
from app.auth import hash_password



TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def engine():
    """
    Crée un moteur SQLAlchemy pour les tests.
    """
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """
    Crée une session de base de données pour chaque test.
    La session est rollback après chaque test pour isolation.
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def role_sales(db_session):
    """Crée un rôle 'sales' pour les tests (ou le réutilise s'il existe)."""
    role = db_session.query(Role).filter(Role.name == "sales").first()
    if not role:
        role = Role(name="sales")
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
    return role


@pytest.fixture
def role_support(db_session):
    """Crée un rôle 'support' pour les tests (ou le réutilise s'il existe)."""
    role = db_session.query(Role).filter(Role.name == "support").first()
    if not role:
        role = Role(name="support")
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
    return role


@pytest.fixture
def role_gestion(db_session):
    """Crée un rôle 'gestion' pour les tests (ou le réutilise s'il existe)."""
    role = db_session.query(Role).filter(Role.name == "gestion").first()
    if not role:
        role = Role(name="gestion")
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
    return role


@pytest.fixture
def all_roles(db_session):
    """Crée les 3 rôles d'un coup et retourne un dict."""
    sales = Role(name="sales")
    support = Role(name="support")
    gestion = Role(name="gestion")

    db_session.add_all([sales, support, gestion])
    db_session.commit()

    return {
        "sales": sales,
        "support": support,
        "gestion": gestion
    }



@pytest.fixture
def user_sales(db_session, role_sales):
    """
    Crée un utilisateur avec le rôle 'sales'.
    Mot de passe: 'password123'
    """
    user = User(
        name="Sales User",
        email="sales@test.com",
        password_hash=hash_password("password123"),
        department="sales",
        role_id=role_sales.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_support(db_session, role_support):
    """
    Crée un utilisateur avec le rôle 'support'.
    Mot de passe: 'password123'
    """
    user = User(
        name="Support User",
        email="support@test.com",
        password_hash=hash_password("password123"),
        department="support",
        role_id=role_support.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_gestion(db_session, role_gestion):
    """
    Crée un utilisateur avec le rôle 'gestion'.
    Mot de passe: 'password123'
    """
    user = User(
        name="Gestion User",
        email="gestion@test.com",
        password_hash=hash_password("password123"),
        department="gestion",
        role_id=role_gestion.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def all_users(db_session, all_roles):
    """Crée les 3 utilisateurs d'un coup et retourne un dict."""
    user_sales = User(
        name="Sales User",
        email="sales@test.com",
        password_hash=hash_password("password123"),
        department="sales",
        role_id=all_roles["sales"].id
    )
    user_support = User(
        name="Support User",
        email="support@test.com",
        password_hash=hash_password("password123"),
        department="support",
        role_id=all_roles["support"].id
    )
    user_gestion = User(
        name="Gestion User",
        email="gestion@test.com",
        password_hash=hash_password("password123"),
        department="gestion",
        role_id=all_roles["gestion"].id
    )

    db_session.add_all([user_sales, user_support, user_gestion])
    db_session.commit()

    # Forcer le chargement des relations 'role' pour éviter les lazy loading errors
    db_session.refresh(user_sales)
    db_session.refresh(user_support)
    db_session.refresh(user_gestion)
    _ = user_sales.role  # Force le chargement de la relation
    _ = user_support.role
    _ = user_gestion.role

    return {
        "sales": user_sales,
        "support": user_support,
        "gestion": user_gestion
    }




@pytest.fixture
def client_sample(db_session, user_sales):
    """Crée un client de test associé à un commercial."""
    client = Client(
        name="John Doe",
        phone_number="+1234567890",
        company_name="ACME Corp",
        sales_contact_id=user_sales.id
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client



@pytest.fixture
def contract_sample(db_session, client_sample):
    """Crée un contrat de test associé à un client."""
    from decimal import Decimal
    contract = Contract(
        total_amount=Decimal("10000.00"),
        remaining_amount=Decimal("5000.00"),
        status="pending",
        client_id=client_sample.id
    )
    db_session.add(contract)
    db_session.commit()
    db_session.refresh(contract)
    return contract




@pytest.fixture
def clean_token_file():
    """
    Nettoie le fichier de token avant et après chaque test.
    """
    token_file = ".epicevents_token"

    
    if os.path.exists(token_file):
        os.remove(token_file)

    yield

    
    if os.path.exists(token_file):
        os.remove(token_file)
