"""
Tests pour le CRUD des utilisateurs.

Ces tests couvrent :
- Création d'utilisateurs
- Lecture d'utilisateurs
- Mise à jour d'utilisateurs
- Suppression d'utilisateurs (si implémenté)
"""

import pytest
from app.crud.crud_user import create_user
from app.models import User
from app.auth import verify_password


class TestCreateUser:
    """Tests pour la création d'utilisateurs."""

    def test_create_user_with_valid_data(self, db_session):
        """Test : peut créer un utilisateur avec des données valides."""
        user = create_user(
            db=db_session,
            email="newuser@test.com",
            password="securepassword"
        )

        assert user is not None
        assert user.id is not None
        assert user.email == "newuser@test.com"

    def test_create_user_hashes_password(self, db_session):
        """Test : le mot de passe est bien haché."""
        password = "plainpassword"
        user = create_user(
            db=db_session,
            email="test@test.com",
            password=password
        )

        # Le hash ne doit pas être égal au mot de passe en clair
        assert user.password_hash != password
        # Mais on doit pouvoir vérifier le mot de passe
        assert verify_password(password, user.password_hash) is True

    def test_create_user_stores_in_database(self, db_session):
        """Test : l'utilisateur est bien enregistré en base."""
        user = create_user(
            db=db_session,
            email="stored@test.com",
            password="password123"
        )

        # Vérifier qu'on peut le retrouver en base
        db_user = db_session.query(User).filter(User.email == "stored@test.com").first()
        assert db_user is not None
        assert db_user.id == user.id

    def test_create_user_returns_refreshed_user(self, db_session):
        """Test : l'utilisateur retourné contient l'ID assigné par la DB."""
        user = create_user(
            db=db_session,
            email="refreshed@test.com",
            password="password123"
        )

        # L'ID doit avoir été assigné par la base
        assert user.id is not None
        assert isinstance(user.id, int)


class TestUserCRUDIntegration:
    """Tests d'intégration pour le CRUD utilisateur."""

    def test_can_create_multiple_users(self, db_session):
        """Test : peut créer plusieurs utilisateurs."""
        user1 = create_user(db_session, "user1@test.com", "pass1")
        user2 = create_user(db_session, "user2@test.com", "pass2")
        user3 = create_user(db_session, "user3@test.com", "pass3")

        users = db_session.query(User).all()
        assert len(users) == 3

    def test_users_have_unique_emails(self, db_session):
        """Test : deux utilisateurs ne peuvent pas avoir le même email."""
        from sqlalchemy.exc import IntegrityError

        create_user(db_session, "duplicate@test.com", "pass1")

        # Tenter de créer un deuxième utilisateur avec le même email
        with pytest.raises(IntegrityError):
            create_user(db_session, "duplicate@test.com", "pass2")
