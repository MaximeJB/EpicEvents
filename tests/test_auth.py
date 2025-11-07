"""
Tests pour le système d'authentification.

Ces tests couvrent :
- Hachage et vérification des mots de passe (Argon2)
- Création et décodage des tokens JWT
- Sauvegarde et chargement des tokens
- Fonction de login
- Fonction get_current_user
- Décorateur @require_role
"""

import pytest
import os
import jwt
from datetime import datetime, timedelta
from app.auth import (
    hash_password,
    verify_password,
    create_token,
    decode_token,
    save_token,
    load_token_locally,
    login,
    get_current_user,
    require_role,
    SECRET_KEY,
)


class TestPasswordHashing:
    """Tests pour le hachage de mots de passe avec Argon2."""

    def test_hash_password_returns_string(self):
        """Test : hash_password retourne une chaîne."""
        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_is_different_from_plain(self):
        """Test : le hash est différent du mot de passe en clair."""
        plain = "mypassword"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_hash_password_uses_salt(self):
        """Test : deux hashs du même mot de passe sont différents (salt)."""
        plain = "mypassword"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        assert hash1 != hash2

    def test_verify_password_with_correct_password(self):
        """Test : verify_password retourne True avec le bon mot de passe."""
        plain = "mypassword"
        hashed = hash_password(plain)
        assert verify_password(hashed, plain) is True

    def test_verify_password_with_wrong_password(self):
        """Test : verify_password retourne False avec un mauvais mot de passe."""
        plain = "mypassword"
        hashed = hash_password(plain)
        assert verify_password(hashed, "wrongpassword") is False

    def test_verify_password_with_invalid_hash(self):
        """Test : verify_password retourne False avec un hash invalide."""
        assert verify_password("mypassword", "invalid_hash") is False


class TestJWTTokens:
    """Tests pour la création et le décodage des tokens JWT."""

    def test_create_token_returns_string(self):
        """Test : create_token retourne une chaîne."""
        token = create_token(user_id=1, role="sales")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_contains_user_id_and_role(self):
        """Test : le token contient user_id et role."""
        token = create_token(user_id=42, role="gestion")
        payload = decode_token(token)

        assert payload["user_id"] == 42
        assert payload["role"] == "gestion"

    def test_create_token_has_expiration(self):
        """Test : le token a une date d'expiration (24h)."""
        token = create_token(user_id=1, role="sales")
        payload = decode_token(token)

        assert "exp" in payload
        exp_datetime = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        diff_hours = (exp_datetime - now).total_seconds() / 3600

        assert 24.8 < diff_hours < 25.2

    def test_decode_token_with_valid_token(self):
        """Test : decode_token décode correctement un token valide."""
        token = create_token(user_id=123, role="support")
        payload = decode_token(token)

        assert payload["user_id"] == 123
        assert payload["role"] == "support"

    def test_decode_token_with_invalid_signature(self):
        """Test : decode_token lève une exception pour un token invalide."""

        fake_token = jwt.encode({"user_id": 1}, "wrong_secret", algorithm="HS256")

        with pytest.raises(jwt.InvalidTokenError):
            decode_token(fake_token)

    def test_decode_token_with_expired_token(self):
        """Test : decode_token lève une exception pour un token expiré."""

        payload = {"user_id": 1, "role": "sales", "exp": datetime.utcnow() - timedelta(hours=1)}  # Expiré il y a 1h
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(expired_token)


class TestTokenStorage:
    """Tests pour la sauvegarde et le chargement des tokens."""

    def test_save_token_creates_file(self, clean_token_file):
        """Test : save_token crée le fichier .epicevents_token."""
        token = "test_token_12345"
        save_token(token)

        assert os.path.exists(".epicevents_token")

    def test_save_token_writes_content(self, clean_token_file):
        """Test : save_token écrit le token dans le fichier."""
        token = "test_token_12345"
        save_token(token)

        with open(".epicevents_token", "r") as f:
            content = f.read()

        assert content == token

    def test_load_token_locally_reads_file(self, clean_token_file):
        """Test : load_token_locally lit le token depuis le fichier."""
        token = "test_token_67890"
        save_token(token)

        loaded = load_token_locally()
        assert loaded == token

    def test_load_token_locally_returns_none_if_no_file(self, clean_token_file):
        """Test : load_token_locally retourne None si le fichier n'existe pas."""
        loaded = load_token_locally()
        assert loaded is None

    def test_load_token_locally_strips_whitespace(self, clean_token_file):
        """Test : load_token_locally enlève les espaces/newlines."""
        with open(".epicevents_token", "w") as f:
            f.write("  test_token_123  \n")

        loaded = load_token_locally()
        assert loaded == "test_token_123"


class TestLoginFunction:
    """Tests pour la fonction login."""

    def test_login_with_valid_credentials(self, db_session, user_sales, clean_token_file):
        """Test : login retourne True avec des identifiants corrects."""
        result = login(db_session, "sales@test.com", "password123")
        assert result is True

    def test_login_creates_token_file(self, db_session, user_sales, clean_token_file):
        """Test : login crée un fichier token."""
        login(db_session, "sales@test.com", "password123")
        assert os.path.exists(".epicevents_token")

    def test_login_with_wrong_email(self, db_session, user_sales, clean_token_file):
        """Test : login retourne False avec un email incorrect."""
        result = login(db_session, "wrong@test.com", "password123")
        assert result is False

    def test_login_with_wrong_password(self, db_session, user_sales, clean_token_file):
        """Test : login retourne False avec un mot de passe incorrect."""
        result = login(db_session, "sales@test.com", "wrongpassword")
        assert result is False

    def test_login_does_not_create_token_on_failure(self, db_session, user_sales, clean_token_file):
        """Test : login ne crée pas de token en cas d'échec."""
        login(db_session, "sales@test.com", "wrongpassword")
        assert not os.path.exists(".epicevents_token")


class TestGetCurrentUser:
    """Tests pour la fonction get_current_user."""

    def test_get_current_user_returns_user_when_logged_in(self, db_session, user_sales, clean_token_file):
        """Test : get_current_user retourne l'utilisateur connecté."""
        login(db_session, "sales@test.com", "password123")

        current_user = get_current_user(db_session)

        assert current_user is not None
        assert current_user.email == "sales@test.com"
        assert current_user.role.name == "sales"

    def test_get_current_user_returns_none_when_no_token(self, db_session, clean_token_file):
        """Test : get_current_user retourne None si pas de token."""
        result = get_current_user(db_session)
        assert result is None

    def test_get_current_user_returns_none_with_expired_token(self, db_session, user_sales, clean_token_file):
        """Test : get_current_user retourne None avec un token expiré."""
        payload = {"user_id": user_sales.id, "role": "sales", "exp": datetime.utcnow() - timedelta(hours=1)}
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        save_token(expired_token)

        current_user = get_current_user(db_session)
        assert current_user is None

    def test_get_current_user_returns_none_with_invalid_token(self, db_session, clean_token_file):
        """Test : get_current_user retourne None avec un token invalide."""
        save_token("invalid_token_blabla")

        current_user = get_current_user(db_session)
        assert current_user is None


class TestRequireRoleDecorator:
    """Tests pour le décorateur @require_role."""

    def test_require_role_allows_authorized_role(self, db_session, user_sales):
        """Test : @require_role autorise les rôles permis."""

        @require_role("sales", "gestion")
        def test_function(db, current_user):
            return "success"

        result = test_function(db_session, user_sales)
        assert result == "success"

    def test_require_role_blocks_unauthorized_role(self, db_session, user_support):
        """Test : @require_role bloque les rôles non autorisés."""

        @require_role("sales", "gestion")
        def test_function(db, current_user):
            return "success"

        with pytest.raises(PermissionError) as exception_info:
            test_function(db_session, user_support)

        assert "ne dispose pas du bon rôle" in str(exception_info.value)

    def test_require_role_with_single_role(self, db_session, user_gestion):
        """Test : @require_role fonctionne avec un seul rôle."""

        @require_role("gestion")
        def test_function(db, current_user):
            return "gestion only"

        result = test_function(db_session, user_gestion)
        assert result == "gestion only"

    def test_require_role_with_multiple_roles(self, db_session, user_sales, user_gestion):
        """Test : @require_role autorise plusieurs rôles."""

        @require_role("sales", "support", "gestion")
        def test_function(db, current_user):
            return current_user.role.name

        result_sales = test_function(db_session, user_sales)
        result_gestion = test_function(db_session, user_gestion)

        assert result_sales == "sales"
        assert result_gestion == "gestion"
