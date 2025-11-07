"""Tests end-to-end (E2E) pour simuler des workflows complets utilisateur.

Ces tests simulent des scénarios complets d'utilisation du CRM
en mockant les inputs utilisateur avec side_effect.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.auth import hash_password, login
from app.managers.client import create_client, list_clients
from app.managers.contract import create_contract, list_contracts, update_contract
from app.managers.event import assign_support, create_event, list_events
from app.managers.user import create_user
from app.models import User


class TestE2ECommercialWorkflow:
    """Tests E2E pour le workflow d'un commercial."""

    def test_complete_sales_workflow(self, db_session, role_sales, role_gestion):
        """Test E2E : Un commercial crée un client, gestion crée contrat, commercial crée événement.

        Ce test simule le workflow complet :
        1. Gestion crée un commercial
        2. Commercial se connecte
        3. Commercial crée un client
        4. Gestion crée un contrat pour ce client
        5. Gestion signe le contrat
        6. Commercial crée un événement pour le contrat signé
        """

        gestion_user = User(
            email="gestion@epic.com",
            password_hash=hash_password("gestion123"),
            name="Manager Gestion",
            department="gestion",
            role_id=role_gestion.id,
        )
        db_session.add(gestion_user)
        db_session.commit()
        db_session.refresh(gestion_user)

        sales_user = create_user(
            db=db_session,
            current_user=gestion_user,
            email="commercial@epic.com",
            password="sales123",
            name="Jean Commercial",
            department="sales",
            role_id=role_sales.id,
        )

        assert sales_user is not None
        assert sales_user.email == "commercial@epic.com"
        assert sales_user.role.name == "sales"


        with patch("app.auth.save_token") as mock_save_token:
            login_success = login(db=db_session, email="commercial@epic.com", password="sales123")

        assert login_success is True
        mock_save_token.assert_called_once()


        client = create_client(
            db=db_session,
            current_user=sales_user,
            name="ACME Corporation",
            phone="+33 1 23 45 67 89",
            company="ACME Corp",
            email="contact@acme.com",
        )

        assert client is not None
        assert client.name == "ACME Corporation"
        assert client.sales_contact_id == sales_user.id


        clients = list_clients(db=db_session, current_user=sales_user)
        assert len(clients) == 1
        assert clients[0].id == client.id


        contract = create_contract(
            db=db_session,
            current_user=gestion_user,
            status="pending",
            total_amount=Decimal("50000"),
            remaining_amount=Decimal("50000"),
            client_id=client.id,
        )

        assert contract is not None
        assert contract.status == "pending"
        assert contract.client_id == client.id


        with patch("app.managers.contract.sentry_sdk.capture_message") as mock_sentry:
            signed_contract = update_contract(
                db=db_session, current_user=gestion_user, contract_id=contract.id, status="signed"
            )

        assert signed_contract.status == "signed"
        mock_sentry.assert_called_once()


        event = create_event(
            db=db_session,
            current_user=sales_user,
            start_date=datetime(2025, 7, 1, 14, 0),
            end_date=datetime(2025, 7, 1, 18, 0),
            location="Paris Convention Center",
            attendees=200,
            contract_id=contract.id,
            notes="Grand événement de lancement produit",
        )

        assert event is not None
        assert event.location == "Paris Convention Center"
        assert event.contract_id == contract.id


        events = list_events(db=db_session, current_user=sales_user)
        assert len(events) == 1
        assert events[0].id == event.id


class TestE2ESupportWorkflow:
    """Tests E2E pour le workflow du support."""

    def test_complete_support_workflow(self, db_session, role_sales, role_support, role_gestion):
        """Test E2E : Workflow complet avec assignation et modification par le support.

        Ce test simule :
        1. Création complète d'un événement (sales + gestion)
        2. Gestion assigne un support à l'événement
        3. Support se connecte et modifie l'événement
        4. Support voit uniquement ses événements
        """

        gestion_user = User(
            email="gestion@epic.com",
            password_hash=hash_password("gestion123"),
            name="Manager Gestion",
            department="gestion",
            role_id=role_gestion.id,
        )
        sales_user = User(
            email="sales@epic.com",
            password_hash=hash_password("sales123"),
            name="Sales User",
            department="sales",
            role_id=role_sales.id,
        )
        support_user = User(
            email="support@epic.com",
            password_hash=hash_password("support123"),
            name="Support User",
            department="support",
            role_id=role_support.id,
        )
        db_session.add_all([gestion_user, sales_user, support_user])
        db_session.commit()


        client = create_client(db_session, sales_user, "Client Test", "+123", "Corp", "test@test.com")
        contract = create_contract(db_session, gestion_user, "signed", Decimal("10000"), Decimal("5000"), client.id)
        event = create_event(
            db_session,
            sales_user,
            datetime(2025, 8, 1, 10, 0),
            datetime(2025, 8, 1, 18, 0),
            "Salle des fêtes",
            50,
            contract.id,
            "Événement test",
        )


        updated_event = assign_support(
            db=db_session, current_user=gestion_user, event_id=event.id, support_user_id=support_user.id
        )

        assert updated_event.support_contact_id == support_user.id


        with patch("app.auth.save_token"):
            login_success = login(db=db_session, email="support@epic.com", password="support123")

        assert login_success is True


        support_events = list_events(db=db_session, current_user=support_user)
        assert len(support_events) == 1
        assert support_events[0].id == event.id


        from app.managers.event import update_event

        modified_event = update_event(
            db=db_session,
            current_user=support_user,
            event_id=event.id,
            notes="Notes mises à jour par le support",
            attendees=75,
        )

        assert modified_event.notes == "Notes mises à jour par le support"
        assert modified_event.attendees == 75


class TestE2EGestionWorkflow:
    """Tests E2E pour le workflow de la gestion."""

    def test_complete_gestion_workflow(self, db_session, role_sales, role_support, role_gestion):
        """Test E2E : Gestion gère tous les aspects du CRM.

        Ce test simule :
        1. Gestion crée plusieurs utilisateurs (sales, support)
        2. Gestion voit tous les clients (même ceux des sales)
        3. Gestion voit tous les contrats
        4. Gestion voit tous les événements
        5. Gestion peut tout modifier
        """

        gestion_user = User(
            email="gestion@epic.com",
            password_hash=hash_password("gestion123"),
            name="Admin Gestion",
            department="gestion",
            role_id=role_gestion.id,
        )
        db_session.add(gestion_user)
        db_session.commit()
        db_session.refresh(gestion_user)


        with patch("app.managers.user.sentry_sdk.capture_message"):
            sales1 = create_user(db_session, gestion_user, "sales1@epic.com", "password123", "Sales 1", "sales", role_sales.id)
            sales2 = create_user(db_session, gestion_user, "sales2@epic.com", "password123", "Sales 2", "sales", role_sales.id)
            support1 = create_user(
                db_session, gestion_user, "support1@epic.com", "password123", "Support 1", "support", role_support.id
            )


        client1 = create_client(db_session, sales1, "Client 1", "+111", "Corp1", "c1@test.com")
        client2 = create_client(db_session, sales2, "Client 2", "+222", "Corp2", "c2@test.com")


        all_clients = list_clients(db=db_session, current_user=gestion_user)
        assert len(all_clients) == 2


        contract1 = create_contract(db_session, gestion_user, "signed", Decimal("20000"), Decimal("10000"), client1.id)
        contract2 = create_contract(db_session, gestion_user, "pending", Decimal("30000"), Decimal("30000"), client2.id)


        all_contracts = list_contracts(db=db_session, current_user=gestion_user)
        assert len(all_contracts) == 2


        event1 = create_event(
            db_session, sales1, datetime(2025, 9, 1, 10, 0), datetime(2025, 9, 1, 18, 0), "Paris", 100, contract1.id
        )


        assign_support(db_session, gestion_user, event1.id, support1.id)


        all_events = list_events(db=db_session, current_user=gestion_user)
        assert len(all_events) == 1


        from app.managers.event import update_event

        modified = update_event(db_session, gestion_user, event1.id, location="Lyon")
        assert modified.location == "Lyon"


class TestE2EPermissionsWorkflow:
    """Tests E2E pour vérifier l'isolation des permissions."""

    def test_sales_cannot_see_other_sales_data(self, db_session, role_sales, role_gestion):
        """Test E2E : Un commercial ne voit QUE ses propres clients/événements."""

        gestion_user = User(
            email="gestion@epic.com",
            password_hash=hash_password("password123"),
            name="Gestion",
            department="gestion",
            role_id=role_gestion.id,
        )
        sales1 = User(
            email="sales1@epic.com",
            password_hash=hash_password("password123"),
            name="Sales 1",
            department="sales",
            role_id=role_sales.id,
        )
        sales2 = User(
            email="sales2@epic.com",
            password_hash=hash_password("password123"),
            name="Sales 2",
            department="sales",
            role_id=role_sales.id,
        )
        db_session.add_all([gestion_user, sales1, sales2])
        db_session.commit()


        client1 = create_client(db_session, sales1, "Client Sales 1", "+111", "Corp1", "s1@test.com")


        client2 = create_client(db_session, sales2, "Client Sales 2", "+222", "Corp2", "s2@test.com")


        sales1_clients = list_clients(db_session, sales1)
        assert len(sales1_clients) == 1
        assert sales1_clients[0].id == client1.id


        sales2_clients = list_clients(db_session, sales2)
        assert len(sales2_clients) == 1
        assert sales2_clients[0].id == client2.id


        gestion_clients = list_clients(db_session, gestion_user)
        assert len(gestion_clients) == 2


        with pytest.raises(PermissionError):
            from app.managers.client import update_client

            update_client(db_session, sales1, client2.id, name="Tentative hack")
