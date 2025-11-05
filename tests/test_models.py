"""
Tests pour les modèles SQLAlchemy.

Ces tests vérifient :
- La création des objets
- Les relations entre modèles
- Les contraintes (unique, nullable, etc.)
- Les valeurs par défaut
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models import Role, User, Client, Contract, Event


class TestRoleModel:
    """Tests pour le modèle Role."""

    def test_create_role(self, db_session):
        """Test : peut créer un rôle basique."""
        role = Role(name="sales")
        db_session.add(role)
        db_session.commit()

        assert role.id is not None
        assert role.name == "sales"

    def test_role_name_is_unique(self, db_session):
        """Test : le nom du rôle doit être unique."""
        role1 = Role(name="sales")
        role2 = Role(name="sales")

        db_session.add(role1)
        db_session.commit()

        db_session.add(role2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_role_name_cannot_be_null(self, db_session):
        """Test : le nom du rôle ne peut pas être null."""
        role = Role(name=None)
        db_session.add(role)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestUserModel:
    """Tests pour le modèle User."""

    def test_create_user(self, db_session, role_sales):
        """Test : peut créer un utilisateur complet."""
        user = User(
            name="John Doe",
            email="john@example.com",
            password_hash="hashed_password",
            department="sales",
            role_id=role_sales.id
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.department == "sales"

    def test_user_email_is_unique(self, db_session, role_sales):
        """Test : l'email doit être unique."""
        user1 = User(
            name="User 1",
            email="duplicate@example.com",
            password_hash="hash1",
            role_id=role_sales.id
        )
        user2 = User(
            name="User 2",
            email="duplicate@example.com",
            password_hash="hash2",
            role_id=role_sales.id
        )

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_has_role_relationship(self, db_session, role_sales):
        """Test : la relation User -> Role fonctionne."""
        user = User(
            name="Test User",
            email="test@example.com",
            password_hash="hash",
            role_id=role_sales.id
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.role is not None
        assert user.role.name == "sales"

    def test_role_has_users_relationship(self, db_session, role_sales):
        """Test : la relation Role -> Users fonctionne."""
        user1 = User(
            name="User 1",
            email="user1@example.com",
            password_hash="hash",
            role_id=role_sales.id
        )
        user2 = User(
            name="User 2",
            email="user2@example.com",
            password_hash="hash",
            role_id=role_sales.id
        )

        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(role_sales)

        assert len(role_sales.users) == 2


class TestClientModel:
    """Tests pour le modèle Client."""

    def test_create_client(self, db_session, user_sales):
        """Test : peut créer un client complet."""
        client = Client(
            name="ACME Corp",
            email="acme@corp.com",
            phone_number="+123456789",
            company_name="ACME Corporation",
            sales_contact_id=user_sales.id
        )
        db_session.add(client)
        db_session.commit()

        assert client.id is not None
        assert client.name == "ACME Corp"
        assert client.company_name == "ACME Corporation"

    def test_client_has_timestamps(self, db_session, user_sales):
        """Test : created_at est automatiquement défini."""
        client = Client(
            name="Test Client",
            email="test@client.com",
            phone_number="+111111111",
            company_name="Test Corp",
            sales_contact_id=user_sales.id
        )
        db_session.add(client)
        db_session.commit()
        db_session.refresh(client)

        assert client.created_at is not None
        assert isinstance(client.created_at, datetime)

    def test_client_has_sales_contact_relationship(self, db_session, user_sales):
        """Test : la relation Client -> User (sales_contact) fonctionne."""
        client = Client(
            name="Test Client",
            email="testclient2@corp.com",
            phone_number="+222222222",
            company_name="Test Corp",
            sales_contact_id=user_sales.id
        )
        db_session.add(client)
        db_session.commit()
        db_session.refresh(client)

        assert client.sales_contact is not None
        assert client.sales_contact.email == "sales@test.com"

    def test_user_has_clients_relationship(self, db_session, user_sales):
        """Test : la relation User -> Clients fonctionne."""
        client1 = Client(
            name="Client 1",
            email="client1@corp.com",
            phone_number="+111111111",
            company_name="Corp 1",
            sales_contact_id=user_sales.id
        )
        client2 = Client(
            name="Client 2",
            email="client2@corp.com",
            phone_number="+222222222",
            company_name="Corp 2",
            sales_contact_id=user_sales.id
        )

        db_session.add_all([client1, client2])
        db_session.commit()
        db_session.refresh(user_sales)

        assert len(user_sales.clients) == 2


class TestContractModel:
    """Tests pour le modèle Contract."""

    def test_create_contract(self, db_session, client_sample):
        """Test : peut créer un contrat complet."""
        contract = Contract(
            total_amount=Decimal("10000.50"),
            remaining_amount=Decimal("5000.25"),
            status="pending",
            client_id=client_sample.id
        )
        db_session.add(contract)
        db_session.commit()

        assert contract.id is not None
        assert contract.total_amount == Decimal("10000.50")
        assert contract.remaining_amount == Decimal("5000.25")

    def test_contract_has_default_status(self, db_session, client_sample):
        """Test : le statut par défaut est 'pending'."""
        contract = Contract(
            total_amount=Decimal("1000.00"),
            remaining_amount=Decimal("1000.00"),
            client_id=client_sample.id
        )
        db_session.add(contract)
        db_session.commit()
        db_session.refresh(contract)

        assert contract.status == "pending"

    def test_contract_has_created_at(self, db_session, client_sample):
        """Test : created_at est automatiquement défini."""
        contract = Contract(
            total_amount=Decimal("1000.00"),
            remaining_amount=Decimal("1000.00"),
            client_id=client_sample.id
        )
        db_session.add(contract)
        db_session.commit()
        db_session.refresh(contract)

        assert contract.created_at is not None
        assert isinstance(contract.created_at, datetime)

    def test_contract_has_client_relationship(self, db_session, client_sample):
        """Test : la relation Contract -> Client fonctionne."""
        contract = Contract(
            total_amount=Decimal("1000.00"),
            remaining_amount=Decimal("1000.00"),
            client_id=client_sample.id
        )
        db_session.add(contract)
        db_session.commit()
        db_session.refresh(contract)

        assert contract.client is not None
        assert contract.client.name == client_sample.name

    def test_client_has_contracts_relationship(self, db_session, client_sample):
        """Test : la relation Client -> Contracts fonctionne."""
        contract1 = Contract(
            total_amount=Decimal("1000.00"),
            remaining_amount=Decimal("500.00"),
            client_id=client_sample.id
        )
        contract2 = Contract(
            total_amount=Decimal("2000.00"),
            remaining_amount=Decimal("1000.00"),
            client_id=client_sample.id
        )

        db_session.add_all([contract1, contract2])
        db_session.commit()
        db_session.refresh(client_sample)

        assert len(client_sample.contracts) == 2


class TestEventModel:
    """Tests pour le modèle Event."""

    def test_create_event(self, db_session, contract_sample, user_support):
        """Test : peut créer un événement complet."""
        event = Event(
            start_date=datetime(2025, 6, 1, 14, 0),
            end_date=datetime(2025, 6, 1, 18, 0),
            location="Paris Convention Center",
            attendees=100,
            notes="Important conference",
            support_contact_id=user_support.id,
            contract_id=contract_sample.id
        )
        db_session.add(event)
        db_session.commit()

        assert event.id is not None
        assert event.location == "Paris Convention Center"
        assert event.attendees == 100

    def test_event_has_contract_relationship(self, db_session, contract_sample, user_support):
        """Test : la relation Event -> Contract fonctionne."""
        event = Event(
            start_date=datetime(2025, 6, 1, 14, 0),
            end_date=datetime(2025, 6, 1, 18, 0),
            location="Test Location",
            attendees=50,
            notes="Test event",
            support_contact_id=user_support.id,
            contract_id=contract_sample.id
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        assert event.contract is not None
        assert event.contract.id == contract_sample.id

    def test_event_has_support_contact_relationship(self, db_session, contract_sample, user_support):
        """Test : la relation Event -> User (support_contact) fonctionne."""
        event = Event(
            start_date=datetime(2025, 6, 1, 14, 0),
            end_date=datetime(2025, 6, 1, 18, 0),
            location="Test Location",
            attendees=50,
            notes="Test event",
            support_contact_id=user_support.id,
            contract_id=contract_sample.id
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        assert event.support_contact is not None
        assert event.support_contact.email == "support@test.com"

    def test_user_support_has_events_relationship(self, db_session, contract_sample, user_support):
        """Test : la relation User -> Events fonctionne."""
        event1 = Event(
            start_date=datetime(2025, 6, 1, 14, 0),
            end_date=datetime(2025, 6, 1, 18, 0),
            location="Location 1",
            attendees=50,
            notes="Event 1",
            support_contact_id=user_support.id,
            contract_id=contract_sample.id
        )
        event2 = Event(
            start_date=datetime(2025, 7, 1, 14, 0),
            end_date=datetime(2025, 7, 1, 18, 0),
            location="Location 2",
            attendees=75,
            notes="Event 2",
            support_contact_id=user_support.id,
            contract_id=contract_sample.id
        )

        db_session.add_all([event1, event2])
        db_session.commit()
        db_session.refresh(user_support)

        assert len(user_support.events) == 2
