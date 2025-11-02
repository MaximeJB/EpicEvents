"""
Tests pour le CRUD des événements.

Ces tests couvrent :
- Création d'événements (permissions : sales pour leurs clients avec contrat signé)
- Récupération d'un événement spécifique
- Listing d'événements (filtré par rôle)
- Mise à jour d'événements (avec permissions)
"""

import pytest
from datetime import datetime
from decimal import Decimal
from app.crud.crud_event import (
    create_event,
    get_event,
    list_events,
    update_event
)
from app.crud.crud_contract import create_contract, update_contract
from app.crud.crud_client import create_client
from app.models import Event


class TestCreateEvent:
    """Tests pour la création d'événements."""

    def test_sales_can_create_event_for_signed_contract(self, db_session, all_users):
        """Test : un commercial peut créer un événement pour un contrat signé."""
        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]

        # Sales crée un client
        client = create_client(db_session, user_sales, "Client", "+111", "Corp")

        # Gestion crée un contrat
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)

        # Gestion signe le contrat
        update_contract(db_session, user_gestion, contract.id, status="signed")
        db_session.refresh(contract)

        # Sales crée un événement
        event = create_event(
            db=db_session,
            current_user=user_sales,
            start_date=datetime(2025, 6, 1, 14, 0),
            end_date=datetime(2025, 6, 1, 18, 0),
            location="Paris",
            attendees=100,
            contract_id=contract.id
        )

        assert event is not None
        assert event.location == "Paris"
        assert event.attendees == 100
        assert event.contract_id == contract.id

    def test_sales_cannot_create_event_for_pending_contract(self, db_session, all_users):
        """Test : un commercial NE PEUT PAS créer d'événement pour un contrat non signé."""
        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]

        # Sales crée un client
        client = create_client(db_session, user_sales, "Client", "+111", "Corp")

        # Gestion crée un contrat (status = pending par défaut)
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)

        # Sales tente de créer un événement
        with pytest.raises(ValueError) as exc_info:
            create_event(
                db=db_session,
                current_user=user_sales,
                start_date=datetime(2025, 6, 1, 14, 0),
                end_date=datetime(2025, 6, 1, 18, 0),
                location="Paris",
                attendees=100,
                contract_id=contract.id
            )

        assert "doit être signé" in str(exc_info.value)

    def test_sales_cannot_create_event_for_other_clients(self, db_session, all_users):
        """Test : un commercial NE PEUT PAS créer d'événement pour les clients d'un autre."""
        from app.models import User

        user_sales1 = all_users["sales"]
        user_gestion = all_users["gestion"]

        # Créer un second commercial
        user_sales2 = User(
            name="Sales 2",
            email="sales2@test.com",
            password_hash="hash",
            department="sales",
            role_id=all_users["sales"].role_id
        )
        db_session.add(user_sales2)
        db_session.commit()

        # Sales1 crée un client
        client = create_client(db_session, user_sales1, "Client", "+111", "Corp")

        # Gestion crée et signe un contrat
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)
        update_contract(db_session, user_gestion, contract.id, status="signed")
        db_session.refresh(contract)

        # Sales2 tente de créer un événement
        with pytest.raises(PermissionError):
            create_event(
                db=db_session,
                current_user=user_sales2,
                start_date=datetime(2025, 6, 1, 14, 0),
                end_date=datetime(2025, 6, 1, 18, 0),
                location="Paris",
                attendees=100,
                contract_id=contract.id
            )

    def test_support_cannot_create_event(self, db_session, all_users):
        """Test : le support NE PEUT PAS créer d'événement."""
        user_sales = all_users["sales"]
        user_support = all_users["support"]
        user_gestion = all_users["gestion"]

        # Préparer un contrat signé
        client = create_client(db_session, user_sales, "Client", "+111", "Corp")
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)
        update_contract(db_session, user_gestion, contract.id, status="signed")

        # Support tente de créer un événement
        with pytest.raises(PermissionError):
            create_event(
                db=db_session,
                current_user=user_support,
                start_date=datetime(2025, 6, 1, 14, 0),
                end_date=datetime(2025, 6, 1, 18, 0),
                location="Paris",
                attendees=100,
                contract_id=contract.id
            )

    def test_create_event_with_nonexistent_contract(self, db_session, user_sales):
        """Test : erreur si le contrat n'existe pas."""
        with pytest.raises(ValueError) as exc_info:
            create_event(
                db=db_session,
                current_user=user_sales,
                start_date=datetime(2025, 6, 1, 14, 0),
                end_date=datetime(2025, 6, 1, 18, 0),
                location="Paris",
                attendees=100,
                contract_id=99999
            )

        assert "Contract not found" in str(exc_info.value)


class TestGetEvent:
    """Tests pour la récupération d'un événement."""

    def test_get_event_by_id(self, db_session, all_users):
        """Test : peut récupérer un événement par son ID."""
        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]

        # Créer un événement
        client = create_client(db_session, user_sales, "Client", "+111", "Corp")
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)
        update_contract(db_session, user_gestion, contract.id, status="signed")
        db_session.refresh(contract)

        event = create_event(
            db_session, user_sales,
            datetime(2025, 6, 1, 14, 0), datetime(2025, 6, 1, 18, 0),
            "Paris", 100, contract.id
        )

        # Récupérer l'événement
        retrieved = get_event(db_session, event.id)

        assert retrieved is not None
        assert retrieved.id == event.id
        assert retrieved.location == "Paris"

    def test_get_event_returns_none_if_not_found(self, db_session):
        """Test : retourne None si l'événement n'existe pas."""
        retrieved = get_event(db_session, 99999)
        assert retrieved is None


class TestListEvents:
    """Tests pour le listing des événements."""

    def test_gestion_sees_all_events(self, db_session, all_users):
        """Test : la gestion voit tous les événements."""
        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]

        # Créer plusieurs événements
        client = create_client(db_session, user_sales, "Client", "+111", "Corp")
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)
        update_contract(db_session, user_gestion, contract.id, status="signed")
        db_session.refresh(contract)

        event1 = create_event(db_session, user_sales, datetime(2025, 6, 1, 14, 0), datetime(2025, 6, 1, 18, 0), "Paris", 100, contract.id)
        event2 = create_event(db_session, user_sales, datetime(2025, 7, 1, 14, 0), datetime(2025, 7, 1, 18, 0), "Lyon", 50, contract.id)

        # Gestion voit tous les événements
        events = list_events(db_session, user_gestion)
        assert len(events) == 2

    def test_support_sees_only_their_events(self, db_session, all_users):
        """Test : le support ne voit que les événements dont il est responsable."""
        user_sales = all_users["sales"]
        user_support = all_users["support"]
        user_gestion = all_users["gestion"]

        # Créer des événements
        client = create_client(db_session, user_sales, "Client", "+111", "Corp")
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)
        update_contract(db_session, user_gestion, contract.id, status="signed")
        db_session.refresh(contract)

        event1 = create_event(db_session, user_sales, datetime(2025, 6, 1, 14, 0), datetime(2025, 6, 1, 18, 0), "Paris", 100, contract.id)
        event2 = create_event(db_session, user_sales, datetime(2025, 7, 1, 14, 0), datetime(2025, 7, 1, 18, 0), "Lyon", 50, contract.id)

        # Gestion assigne event1 au support
        update_event(db_session, user_gestion, event1.id, support_contact_id=user_support.id)

        # Support ne voit que son événement
        events = list_events(db_session, user_support)
        assert len(events) == 1
        assert events[0].id == event1.id

    def test_sales_sees_events_of_their_clients(self, db_session, all_users):
        """Test : un commercial voit les événements de SES clients."""
        from app.models import User

        user_sales1 = all_users["sales"]
        user_gestion = all_users["gestion"]

        # Créer un second commercial
        user_sales2 = User(
            name="Sales 2",
            email="sales2@test.com",
            password_hash="hash",
            department="sales",
            role_id=all_users["sales"].role_id
        )
        db_session.add(user_sales2)
        db_session.commit()

        # Sales1 crée un client et un événement
        client1 = create_client(db_session, user_sales1, "Client 1", "+111", "Corp 1")
        contract1 = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client1.id)
        update_contract(db_session, user_gestion, contract1.id, status="signed")
        db_session.refresh(contract1)
        event1 = create_event(db_session, user_sales1, datetime(2025, 6, 1, 14, 0), datetime(2025, 6, 1, 18, 0), "Paris", 100, contract1.id)

        # Sales2 crée un client et un événement
        client2 = create_client(db_session, user_sales2, "Client 2", "+222", "Corp 2")
        contract2 = create_contract(db_session, user_gestion, Decimal("2000"), Decimal("1000"), client2.id)
        update_contract(db_session, user_gestion, contract2.id, status="signed")
        db_session.refresh(contract2)
        event2 = create_event(db_session, user_sales2, datetime(2025, 7, 1, 14, 0), datetime(2025, 7, 1, 18, 0), "Lyon", 50, contract2.id)

        # Sales1 ne voit que son événement
        events = list_events(db_session, user_sales1)
        assert len(events) == 1
        assert events[0].id == event1.id


class TestUpdateEvent:
    """Tests pour la mise à jour d'événements."""

    def test_gestion_can_update_any_event(self, db_session, all_users):
        """Test : la gestion peut modifier n'importe quel événement."""
        user_sales = all_users["sales"]
        user_support = all_users["support"]
        user_gestion = all_users["gestion"]

        # Créer un événement
        client = create_client(db_session, user_sales, "Client", "+111", "Corp")
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)
        update_contract(db_session, user_gestion, contract.id, status="signed")
        db_session.refresh(contract)
        event = create_event(db_session, user_sales, datetime(2025, 6, 1, 14, 0), datetime(2025, 6, 1, 18, 0), "Paris", 100, contract.id)

        # Gestion modifie et assigne au support
        updated = update_event(
            db=db_session,
            current_user=user_gestion,
            event_id=event.id,
            location="Lyon",
            support_contact_id=user_support.id
        )

        assert updated.location == "Lyon"
        assert updated.support_contact_id == user_support.id

    def test_support_can_update_their_events(self, db_session, all_users):
        """Test : le support peut modifier SES événements."""
        user_sales = all_users["sales"]
        user_support = all_users["support"]
        user_gestion = all_users["gestion"]

        # Créer un événement et l'assigner au support
        client = create_client(db_session, user_sales, "Client", "+111", "Corp")
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)
        update_contract(db_session, user_gestion, contract.id, status="signed")
        db_session.refresh(contract)
        event = create_event(db_session, user_sales, datetime(2025, 6, 1, 14, 0), datetime(2025, 6, 1, 18, 0), "Paris", 100, contract.id)
        update_event(db_session, user_gestion, event.id, support_contact_id=user_support.id)
        db_session.refresh(event)

        # Support peut modifier
        updated = update_event(
            db=db_session,
            current_user=user_support,
            event_id=event.id,
            notes="Updated by support"
        )

        assert updated.notes == "Updated by support"

    def test_support_cannot_update_other_events(self, db_session, all_users):
        """Test : le support NE PEUT PAS modifier les événements d'autres supports."""
        from app.models import User

        user_sales = all_users["sales"]
        user_support1 = all_users["support"]
        user_gestion = all_users["gestion"]

        # Créer un second support
        user_support2 = User(
            name="Support 2",
            email="support2@test.com",
            password_hash="hash",
            department="support",
            role_id=all_users["support"].role_id
        )
        db_session.add(user_support2)
        db_session.commit()

        # Créer un événement assigné au support1
        client = create_client(db_session, user_sales, "Client", "+111", "Corp")
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)
        update_contract(db_session, user_gestion, contract.id, status="signed")
        db_session.refresh(contract)
        event = create_event(db_session, user_sales, datetime(2025, 6, 1, 14, 0), datetime(2025, 6, 1, 18, 0), "Paris", 100, contract.id)
        update_event(db_session, user_gestion, event.id, support_contact_id=user_support1.id)
        db_session.refresh(event)

        # Support2 tente de modifier
        with pytest.raises(PermissionError):
            update_event(
                db=db_session,
                current_user=user_support2,
                event_id=event.id,
                notes="Unauthorized"
            )

    def test_sales_cannot_update_event(self, db_session, all_users):
        """Test : les commerciaux NE PEUVENT PAS modifier d'événements."""
        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]

        # Créer un événement
        client = create_client(db_session, user_sales, "Client", "+111", "Corp")
        contract = create_contract(db_session, user_gestion, Decimal("1000"), Decimal("500"), client.id)
        update_contract(db_session, user_gestion, contract.id, status="signed")
        db_session.refresh(contract)
        event = create_event(db_session, user_sales, datetime(2025, 6, 1, 14, 0), datetime(2025, 6, 1, 18, 0), "Paris", 100, contract.id)

        # Sales tente de modifier
        with pytest.raises(PermissionError):
            update_event(
                db=db_session,
                current_user=user_sales,
                event_id=event.id,
                location="Lyon"
            )

    def test_update_event_raises_error_if_not_found(self, db_session, user_gestion):
        """Test : lève une erreur si l'événement n'existe pas."""
        with pytest.raises(ValueError) as exc_info:
            update_event(
                db=db_session,
                current_user=user_gestion,
                event_id=99999,
                location="Nowhere"
            )

        assert "n'existe pas" in str(exc_info.value)