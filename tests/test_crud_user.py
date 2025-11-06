"""
Tests pour le CRUD des utilisateurs.

Ces tests couvrent :
- Création d'utilisateurs
- Lecture d'utilisateurs
- Listing d'utilisateurs
- Mise à jour d'utilisateurs
- Suppression d'utilisateurs
"""

import pytest
from app.managers.user import create_user, get_user, get_user_by_id, list_users, update_user, delete_user
from app.models import User
from app.auth import verify_password


class TestCreateUser:
    """Tests pour la création d'utilisateurs."""

    def test_create_user_with_valid_data(self, db_session, role_sales, user_gestion):
        """Test : peut créer un utilisateur avec des données valides."""
        user = create_user(
            db=db_session,
            current_user=user_gestion,
            email="newuser@test.com",
            password="securepassword",
            name="New User",
            department="sales",
            role_id=role_sales.id,
        )

        assert user is not None
        assert user.id is not None
        assert user.email == "newuser@test.com"

    def test_create_user_hashes_password(self, db_session, role_sales, user_gestion):
        """Test : le mot de passe est bien haché."""
        password = "plainpassword"
        user = create_user(
            db=db_session,
            current_user=user_gestion,
            email="test@test.com",
            password=password,
            name="Test User",
            department="sales",
            role_id=role_sales.id,
        )

        assert user.password_hash != password
        assert verify_password(user.password_hash, password) is True

    def test_create_user_stores_in_database(self, db_session, role_sales, user_gestion):
        """Test : l'utilisateur est bien enregistré en base."""
        user = create_user(
            db=db_session,
            current_user=user_gestion,
            email="stored@test.com",
            password="password123",
            name="Stored User",
            department="sales",
            role_id=role_sales.id,
        )

        
        db_user = db_session.query(User).filter(User.email == "stored@test.com").first()
        assert db_user is not None
        assert db_user.id == user.id

    def test_create_user_returns_refreshed_user(self, db_session, role_sales, user_gestion):
        """Test : l'utilisateur retourné contient l'ID assigné par la DB."""
        user = create_user(
            db=db_session,
            current_user=user_gestion,
            email="refreshed@test.com",
            password="password123",
            name="Refreshed User",
            department="sales",
            role_id=role_sales.id,
        )

        
        assert user.id is not None
        assert isinstance(user.id, int)


class TestUserCRUDIntegration:
    """Tests d'intégration pour le CRUD utilisateur."""

    def test_can_create_multiple_users(self, db_session, role_sales, user_gestion):
        """Test : peut créer plusieurs utilisateurs."""
        user1 = create_user(db_session, user_gestion, "user1@test.com", "pass1", "User 1", "sales", role_sales.id)
        user2 = create_user(db_session, user_gestion, "user2@test.com", "pass2", "User 2", "sales", role_sales.id)
        user3 = create_user(db_session, user_gestion, "user3@test.com", "pass3", "User 3", "sales", role_sales.id)

        
        assert user1 is not None
        assert user2 is not None
        assert user3 is not None
        assert user1.email == "user1@test.com"
        assert user2.email == "user2@test.com"
        assert user3.email == "user3@test.com"

    def test_users_have_unique_emails(self, db_session, role_sales, user_gestion):
        """Test : deux utilisateurs ne peuvent pas avoir le même email."""
        from sqlalchemy.exc import IntegrityError

        create_user(db_session, user_gestion, "duplicate@test.com", "pass1", "User 1", "sales", role_sales.id)

        with pytest.raises(IntegrityError):
            create_user(db_session, user_gestion, "duplicate@test.com", "pass2", "User 2", "sales", role_sales.id)


class TestGetUser:
    """Tests pour la récupération d'utilisateurs."""

    def test_get_user_by_email(self, db_session, user_sales):
        """Test : peut récupérer un utilisateur par son email."""
        retrieved = get_user(db_session, "sales@test.com")

        assert retrieved is not None
        assert retrieved.id == user_sales.id
        assert retrieved.name == "Sales User"

    def test_get_user_returns_none_if_not_found(self, db_session):
        """Test : retourne None si l'utilisateur n'existe pas."""
        retrieved = get_user(db_session, "nonexistent@test.com")
        assert retrieved is None

    def test_get_user_by_id(self, db_session, user_gestion):
        """Test : peut récupérer un utilisateur par son ID."""
        retrieved = get_user_by_id(db_session, user_gestion.id)

        assert retrieved is not None
        assert retrieved.email == "gestion@test.com"
        assert retrieved.name == "Gestion User"

    def test_get_user_by_id_returns_none_if_not_found(self, db_session):
        """Test : retourne None si l'ID n'existe pas."""
        retrieved = get_user_by_id(db_session, 99999)
        assert retrieved is None


class TestListUsers:
    """Tests pour le listing des utilisateurs."""

    def test_gestion_can_list_all_users(self, db_session, all_users):
        """Test : la gestion peut lister tous les utilisateurs."""
        user_gestion = all_users["gestion"]
        users = list_users(db_session, user_gestion)

        
        assert len(users) == 3
        assert any(u.email == "sales@test.com" for u in users)
        assert any(u.email == "support@test.com" for u in users)
        assert any(u.email == "gestion@test.com" for u in users)

    def test_sales_cannot_list_users(self, db_session, user_sales):
        """Test : les commerciaux NE PEUVENT PAS lister les utilisateurs."""
        with pytest.raises(PermissionError):
            list_users(db_session, user_sales)

    def test_support_cannot_list_users(self, db_session, user_support):
        """Test : le support NE PEUT PAS lister les utilisateurs."""
        with pytest.raises(PermissionError):
            list_users(db_session, user_support)


class TestUpdateUser:
    """Tests pour la mise à jour d'utilisateurs."""

    def test_gestion_can_update_user(self, db_session, user_gestion, user_sales):
        """Test : la gestion peut modifier un utilisateur."""
        updated = update_user(
            db=db_session,
            current_user=user_gestion,
            user_id=user_sales.id,
            name="Updated Sales User",
            department="marketing",
        )

        assert updated.name == "Updated Sales User"
        assert updated.department == "marketing"
        assert updated.email == "sales@test.com"  # Inchangé

    def test_gestion_can_update_user_role(self, db_session, user_gestion, user_sales, role_support):
        """Test : la gestion peut changer le rôle d'un utilisateur."""
        updated = update_user(db=db_session, current_user=user_gestion, user_id=user_sales.id, role_id=role_support.id)

        db_session.refresh(updated)
        assert updated.role_id == role_support.id
        assert updated.role.name == "support"

    def test_sales_cannot_update_user(self, db_session, user_sales, user_support):
        """Test : les commerciaux NE PEUVENT PAS modifier d'utilisateurs."""
        with pytest.raises(PermissionError):
            update_user(db=db_session, current_user=user_sales, user_id=user_support.id, name="Hacked Name")

    def test_support_cannot_update_user(self, db_session, user_support, user_sales):
        """Test : le support NE PEUT PAS modifier d'utilisateurs."""
        with pytest.raises(PermissionError):
            update_user(db=db_session, current_user=user_support, user_id=user_sales.id, name="Forbidden")

    def test_update_user_raises_error_if_not_found(self, db_session, user_gestion):
        """Test : lève une erreur si l'utilisateur n'existe pas."""
        with pytest.raises(ValueError) as exc_info:
            update_user(db=db_session, current_user=user_gestion, user_id=99999, name="Ghost User")

        assert "User not found" in str(exc_info.value)


class TestDeleteUser:
    """Tests pour la suppression d'utilisateurs."""

    def test_gestion_can_delete_user(self, db_session, user_gestion, role_sales):
        """Test : la gestion peut supprimer un utilisateur."""
        
        user_to_delete = create_user(
            db=db_session,
            current_user=user_gestion,
            email="todelete@test.com",
            password="password123",
            name="To Delete",
            department="sales",
            role_id=role_sales.id,
        )

        user_id = user_to_delete.id

        
        result = delete_user(db_session, user_gestion, user_id)
        assert result is True

        
        deleted = get_user_by_id(db_session, user_id)
        assert deleted is None

    def test_sales_cannot_delete_user(self, db_session, user_sales, user_support):
        """Test : les commerciaux NE PEUVENT PAS supprimer d'utilisateurs."""
        with pytest.raises(PermissionError):
            delete_user(db_session, user_sales, user_support.id)

    def test_support_cannot_delete_user(self, db_session, user_support, user_sales):
        """Test : le support NE PEUT PAS supprimer d'utilisateurs."""
        with pytest.raises(PermissionError):
            delete_user(db_session, user_support, user_sales.id)

    def test_delete_user_raises_error_if_not_found(self, db_session, user_gestion):
        """Test : lève une erreur si l'utilisateur n'existe pas."""
        with pytest.raises(ValueError) as exc_info:
            delete_user(db_session, user_gestion, 99999)

        assert "User not found" in str(exc_info.value)
