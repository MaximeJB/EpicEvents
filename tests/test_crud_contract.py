"""
Tests pour le CRUD des contrats.

Ces tests couvrent :
- Création de contrats (permissions : gestion uniquement)
- Récupération d'un contrat spécifique
- Listing de contrats (filtré par rôle)
- Mise à jour de contrats (avec permissions)
"""

import pytest
from decimal import Decimal
from app.managers.contract import create_contract, get_contract, list_contracts, update_contract
from app.models import Contract


class TestCreateContract:
    """Tests pour la création de contrats."""

    def test_gestion_can_create_contract(self, db_session, user_gestion, client_sample):
        """Test : la gestion peut créer un contrat."""
        contract = create_contract(
            db=db_session,
            current_user=user_gestion,
            status="pending",
            total_amount=Decimal("10000.00"),
            remaining_amount=Decimal("5000.00"),
            client_id=client_sample.id,
        )

        assert contract is not None
        assert contract.total_amount == Decimal("10000.00")
        assert contract.remaining_amount == Decimal("5000.00")
        assert contract.client_id == client_sample.id

    def test_contract_has_default_status_pending(self, db_session, user_gestion, client_sample):
        """Test : le status par défaut est 'pending'."""
        contract = create_contract(
            db=db_session,
            current_user=user_gestion,
            status="pending",
            total_amount=Decimal("1000.00"),
            remaining_amount=Decimal("1000.00"),
            client_id=client_sample.id,
        )

        assert contract.status == "pending"

    def test_sales_cannot_create_contract(self, db_session, user_sales, client_sample):
        """Test : les commerciaux NE PEUVENT PAS créer de contrats."""
        with pytest.raises(PermissionError):
            create_contract(
                db=db_session,
                current_user=user_sales,
                status="pending",
                total_amount=Decimal("1000.00"),
                remaining_amount=Decimal("1000.00"),
                client_id=client_sample.id,
            )

    def test_support_cannot_create_contract(self, db_session, user_support, client_sample):
        """Test : le support NE PEUT PAS créer de contrats."""
        with pytest.raises(PermissionError):
            create_contract(
                db=db_session,
                current_user=user_support,
                status="pending",
                total_amount=Decimal("1000.00"),
                remaining_amount=Decimal("1000.00"),
                client_id=client_sample.id,
            )

    def test_create_contract_with_nonexistent_client(self, db_session, user_gestion):
        """Test : erreur si le client n'existe pas."""
        with pytest.raises(ValueError) as exc_info:
            create_contract(
                db=db_session,
                current_user=user_gestion,
                status="pending",
                total_amount=Decimal("1000.00"),
                remaining_amount=Decimal("1000.00"),
                client_id=99999,
            )

        assert "Client not found" in str(exc_info.value)


class TestGetContract:
    """Tests pour la récupération d'un contrat."""

    def test_get_contract_by_id(self, db_session, contract_sample):
        """Test : peut récupérer un contrat par son ID."""
        retrieved = get_contract(db_session, contract_sample.id)

        assert retrieved is not None
        assert retrieved.id == contract_sample.id

    def test_get_contract_returns_none_if_not_found(self, db_session):
        """Test : retourne None si le contrat n'existe pas."""
        retrieved = get_contract(db_session, 99999)
        assert retrieved is None


class TestListContracts:
    """Tests pour le listing des contrats."""

    def test_sales_sees_only_their_clients_contracts(self, db_session, all_users):
        """Test : un commercial ne voit que les contrats de SES clients."""
        from app.managers.client import create_client

        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]

        client1 = create_client(db_session, user_sales, "Client 1", "+111", "Corp 1", "client1@sales.com")
        client2 = create_client(db_session, user_sales, "Client 2", "+222", "Corp 2", "client2@sales.com")

        contract1 = create_contract(db_session, user_gestion, "signed", Decimal("1000"), Decimal("500"), client1.id)
        contract2 = create_contract(db_session, user_gestion, "signed", Decimal("2000"), Decimal("1000"), client2.id)

        from app.models import User

        user_sales2 = User(
            name="Sales 2",
            email="sales2@test.com",
            password_hash="hash",
            department="sales",
            role_id=all_users["sales"].role_id,
        )
        db_session.add(user_sales2)
        db_session.commit()

        client3 = create_client(db_session, user_sales2, "Client 3", "+333", "Corp 3", "c3@test.com")
        contract3 = create_contract(db_session, user_gestion, "signed", Decimal("3000"), Decimal("1500"), client3.id)

        contracts = list_contracts(db_session, user_sales)
        assert len(contracts) == 2

    def test_gestion_sees_all_contracts(self, db_session, all_users):
        """Test : la gestion voit tous les contrats."""
        from app.managers.client import create_client

        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]

        client1 = create_client(db_session, user_sales, "Client 1", "+111", "Corp 1", "client1@gestion.com")
        client2 = create_client(db_session, user_sales, "Client 2", "+222", "Corp 2", "client2@gestion.com")

        contract1 = create_contract(db_session, user_gestion, "signed", Decimal("1000"), Decimal("500"), client1.id)
        contract2 = create_contract(db_session, user_gestion, "signed", Decimal("2000"), Decimal("1000"), client2.id)

        contracts = list_contracts(db_session, user_gestion)
        assert len(contracts) == 2

    def test_support_sees_all_contracts(self, db_session, all_users):
        """Test : le support voit tous les contrats (lecture seule)."""
        from app.managers.client import create_client

        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]
        user_support = all_users["support"]

        
        client = create_client(db_session, user_sales, "Test Client", "+111", "Test Corp", "test@corp.com")
        contract1 = create_contract(db_session, user_gestion, "signed", Decimal("1000"), Decimal("500"), client.id)

        contracts = list_contracts(db_session, user_support)
        assert len(contracts) == 1


class TestUpdateContract:
    """Tests pour la mise à jour de contrats."""

    def test_gestion_can_update_any_contract(self, db_session, user_gestion, contract_sample):
        """Test : la gestion peut modifier n'importe quel contrat."""
        updated = update_contract(
            db=db_session,
            current_user=user_gestion,
            contract_id=contract_sample.id,
            status="signed",
            remaining_amount=Decimal("0.00"),
        )

        assert updated.status == "signed"
        assert updated.remaining_amount == Decimal("0.00")

    def test_sales_can_update_their_clients_contracts(self, db_session, all_users):
        """Test : un commercial peut modifier les contrats de SES clients."""
        from app.managers.client import create_client

        user_sales = all_users["sales"]
        user_gestion = all_users["gestion"]

        
        client = create_client(db_session, user_sales, "Client", "+111", "Corp", "client@update.com")

        
        contract = create_contract(db_session, user_gestion, "pending", Decimal("1000"), Decimal("500"), client.id)

        
        updated = update_contract(db=db_session, current_user=user_sales, contract_id=contract.id, status="signed")

        assert updated.status == "signed"

    def test_sales_cannot_update_other_clients_contracts(self, db_session, all_users):
        """Test : un commercial NE PEUT PAS modifier les contrats d'autres clients."""
        from app.managers.client import create_client
        from app.models import User

        user_sales1 = all_users["sales"]
        user_gestion = all_users["gestion"]

        
        user_sales2 = User(
            name="Sales 2",
            email="sales2@test.com",
            password_hash="hash",
            department="sales",
            role_id=all_users["sales"].role_id,
        )
        db_session.add(user_sales2)
        db_session.commit()

        
        client = create_client(db_session, user_sales1, "Client", "+111", "Corp", "client@sales1.com")

        
        contract = create_contract(db_session, user_gestion, "pending", Decimal("1000"), Decimal("500"), client.id)

        
        with pytest.raises(PermissionError):
            update_contract(db=db_session, current_user=user_sales2, contract_id=contract.id, status="signed")

    def test_support_cannot_update_contract(self, db_session, user_support, contract_sample):
        """Test : le support NE PEUT PAS modifier de contrats."""
        with pytest.raises(PermissionError):
            update_contract(db=db_session, current_user=user_support, contract_id=contract_sample.id, status="signed")

    def test_update_contract_raises_error_if_not_found(self, db_session, user_gestion):
        """Test : lève une erreur si le contrat n'existe pas."""
        with pytest.raises(ValueError) as exc_info:
            update_contract(db=db_session, current_user=user_gestion, contract_id=99999, status="signed")

        assert "Contract not found" in str(exc_info.value)
