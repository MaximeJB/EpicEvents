"""
Tests pour le CRUD des clients.

Ces tests couvrent :
- Création de clients (permissions : sales et gestion)
- Récupération d'un client spécifique
- Listing de clients (filtré par rôle)
- Mise à jour de clients (avec permissions)
"""

import pytest
from app.managers.client import create_client, get_client, list_clients, update_client
from app.models import Client


class TestCreateClient:
    """Tests pour la création de clients."""

    def test_sales_can_create_client(self, db_session, user_sales):
        """Test : un commercial peut créer un client."""
        client = create_client(
            db=db_session,
            current_user=user_sales,
            name="John Doe",
            phone="+1234567890",
            company="ACME Corp",
            email="john@acme.com",
        )

        assert client is not None
        assert client.name == "John Doe"
        assert client.phone_number == "+1234567890"
        assert client.company_name == "ACME Corp"
        assert client.email == "john@acme.com"

    def test_sales_client_is_auto_assigned(self, db_session, user_sales):
        """Test : le client créé par un commercial lui est automatiquement assigné."""
        client = create_client(
            db=db_session,
            current_user=user_sales,
            name="Client Test",
            phone="+1111111111",
            company="Test Corp",
            email="test@test.com",
        )

        assert client.sales_contact_id == user_sales.id

    def test_gestion_can_create_client(self, db_session, user_gestion):
        """Test : la gestion peut créer un client."""
        client = create_client(
            db=db_session,
            current_user=user_gestion,
            name="Jane Smith",
            phone="+9876543210",
            company="Smith LLC",
            email="jane@smith.com",
        )

        assert client is not None
        assert client.name == "Jane Smith"

    def test_gestion_client_is_auto_assigned(self, db_session, user_gestion):
        """Test : le client créé par gestion est assigné à gestion (current_user)."""
        client = create_client(
            db=db_session,
            current_user=user_gestion,
            name="Client Gestion",
            phone="+2222222222",
            company="Gestion Corp",
            email="gestion@corp.com",
        )

        assert client.sales_contact_id == user_gestion.id

    def test_support_cannot_create_client(self, db_session, user_support):
        """Test : le support NE PEUT PAS créer de clients."""
        with pytest.raises(PermissionError):
            create_client(
                db=db_session,
                current_user=user_support,
                name="Forbidden Client",
                phone="+3333333333",
                company="Support Corp",
                email="support@corp.com",
            )

    def test_create_client_stores_in_database(self, db_session, user_sales):
        """Test : le client est bien enregistré en base."""
        client = create_client(
            db=db_session,
            current_user=user_sales,
            name="Stored Client",
            phone="+4444444444",
            company="Stored Corp",
            email="stored@corp.com",
        )

        db_client = db_session.query(Client).filter(Client.email == "stored@corp.com").first()
        assert db_client is not None
        assert db_client.id == client.id


class TestGetClient:
    """Tests pour la récupération d'un client."""

    def test_get_client_by_id(self, db_session, client_sample):
        """Test : peut récupérer un client par son ID."""
        retrieved = get_client(db_session, client_sample.id)

        assert retrieved is not None
        assert retrieved.id == client_sample.id
        assert retrieved.name == client_sample.name

    def test_get_client_returns_none_if_not_found(self, db_session):
        """Test : retourne None si le client n'existe pas."""
        retrieved = get_client(db_session, 99999)
        assert retrieved is None


class TestListClients:
    """Tests pour le listing des clients."""

    def test_sales_sees_only_their_clients(self, db_session, all_users):
        """Test : un commercial ne voit que SES clients."""
        
        user_sales1 = all_users["sales"]
        user_sales2 = User(
            name="Sales 2",
            email="sales2@test.com",
            password_hash="hash",
            department="sales",
            role_id=all_users["sales"].role_id,
        )
        db_session.add(user_sales2)
        db_session.commit()

        client1 = create_client(db_session, user_sales1, "Client 1", "+111", "Corp 1", "c1@test.com")
        client2 = create_client(db_session, user_sales1, "Client 2", "+222", "Corp 2", "c2@test.com")

        client3 = create_client(db_session, user_sales2, "Client 3", "+333", "Corp 3", "c3@test.com")

        clients = list_clients(db_session, user_sales1)
        assert len(clients) == 2
        assert all(c.sales_contact_id == user_sales1.id for c in clients)

    def test_gestion_sees_all_clients(self, db_session, all_users):
        """Test : la gestion voit tous les clients."""
        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]

        client1 = create_client(db_session, user_sales, "Client 1", "+111", "Corp 1", "c1@test.com")
        client2 = create_client(db_session, user_sales, "Client 2", "+222", "Corp 2", "c2@test.com")
        client3 = create_client(db_session, user_gestion, "Client 3", "+333", "Corp 3", "c3@test.com")

        clients = list_clients(db_session, user_gestion)
        assert len(clients) == 3

    def test_support_sees_all_clients(self, db_session, all_users):
        """Test : le support voit tous les clients (lecture seule)."""
        user_sales = all_users["sales"]
        user_support = all_users["support"]

        client1 = create_client(db_session, user_sales, "Client 1", "+111", "Corp 1", "c1@test.com")
        client2 = create_client(db_session, user_sales, "Client 2", "+222", "Corp 2", "c2@test.com")

        clients = list_clients(db_session, user_support)
        assert len(clients) == 2


class TestUpdateClient:
    """Tests pour la mise à jour de clients."""

    def test_sales_can_update_their_clients(self, db_session, user_sales):
        """Test : un commercial peut modifier SES clients."""

        client = create_client(db_session, user_sales, "Old Name", "+111", "Old Corp", "old@test.com")

        updated = update_client(
            db=db_session, current_user=user_sales, client_id=client.id, name="New Name", company_name="New Corp"
        )

        assert updated.name == "New Name"
        assert updated.company_name == "New Corp"
        assert updated.phone_number == "+111"

    def test_sales_cannot_update_other_clients(self, db_session, all_users):
        """Test : un commercial NE PEUT PAS modifier les clients d'un autre."""
        
        user_sales1 = all_users["sales"]
        user_sales2 = User(
            name="Sales 2",
            email="sales2@test.com",
            password_hash="hash",
            department="sales",
            role_id=all_users["sales"].role_id,
        )
        db_session.add(user_sales2)
        db_session.commit()

        client = create_client(db_session, user_sales1, "Client 1", "+111", "Corp 1", "c1@test.com")

        with pytest.raises(PermissionError):
            update_client(db=db_session, current_user=user_sales2, client_id=client.id, name="Hacked Name")

    def test_gestion_can_update_any_client(self, db_session, all_users):
        """Test : la gestion peut modifier n'importe quel client."""
        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]

        client = create_client(db_session, user_sales, "Client", "+111", "Corp", "client@test.com")

        updated = update_client(
            db=db_session, current_user=user_gestion, client_id=client.id, name="Updated by Gestion"
        )

        assert updated.name == "Updated by Gestion"

    def test_support_cannot_update_client(self, db_session, user_sales, user_support):
        """Test : le support NE PEUT PAS modifier de clients."""

        client = create_client(db_session, user_sales, "Client", "+111", "Corp", "client@test.com")

        with pytest.raises(PermissionError):
            update_client(db=db_session, current_user=user_support, client_id=client.id, name="Forbidden")

    def test_update_client_raises_error_if_not_found(self, db_session, user_gestion):
        """Test : lève une erreur si le client n'existe pas."""
        with pytest.raises(ValueError) as exc_info:
            update_client(db=db_session, current_user=user_gestion, client_id=99999, name="Ghost Client")

        assert "Client not found" in str(exc_info.value)

    def test_update_client_with_multiple_fields(self, db_session, user_sales):
        """Test : peut modifier plusieurs champs à la fois."""
        client = create_client(db_session, user_sales, "Old", "+111", "Old Corp", "old@test.com")

        updated = update_client(
            db=db_session,
            current_user=user_sales,
            client_id=client.id,
            name="New Name",
            phone_number="+999",
            company_name="New Corp",
        )

        assert updated.name == "New Name"
        assert updated.phone_number == "+999"
        assert updated.company_name == "New Corp"
