from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials

from app.api.v1.auth import get_current_user, login, signup
from app.core.config import Settings, settings, _validate_runtime_settings
from app.core.database import SessionLocal, reset_test_schema
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin

from .helpers import FakeExecuteResult, build_user


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_test_schema()

    def _create_user(
        self,
        *,
        email: str = "user@example.com",
        password: str = "Secret123",
    ) -> User:
        with SessionLocal() as db:
            user = User(
                email=email,
                password_hash=hash_password(password),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    def test_signup_creates_user(self) -> None:
        db = MagicMock()
        db.execute.return_value = FakeExecuteResult(one=None)

        with patch("app.api.v1.auth.hash_password", return_value="hashed"):
            user = signup(
                UserCreate(email="new@example.com", password="secret123"),
                db=db,
            )

        self.assertEqual(user.email, "new@example.com")
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(user)

    def test_signup_duplicate_email_returns_400(self) -> None:
        db = MagicMock()
        db.execute.return_value = FakeExecuteResult(one=build_user(email="dupe@example.com"))

        with self.assertRaises(HTTPException) as context:
            signup(UserCreate(email="dupe@example.com", password="secret123"), db=db)

        self.assertEqual(context.exception.status_code, 400)

    def test_login_invalid_credentials_returns_401(self) -> None:
        db = MagicMock()
        db.execute.return_value = FakeExecuteResult(one=None)
        response = MagicMock()

        with self.assertRaises(HTTPException) as context:
            login(UserLogin(email="none@example.com", password="wrong123"), response=response, db=db)

        self.assertEqual(context.exception.status_code, 401)

    def test_login_success_returns_access_token(self) -> None:
        user = build_user(email="ok@example.com", password_hash="hashed")
        db = MagicMock()
        db.execute.return_value = FakeExecuteResult(one=user)
        response = MagicMock()

        with (
            patch("app.api.v1.auth.verify_password", return_value=True),
            patch("app.api.v1.auth.create_access_token", return_value="token-123"),
        ):
            token_response = login(
                UserLogin(email="ok@example.com", password="secret123"),
                response=response,
                db=db,
            )

        self.assertEqual(token_response.access_token, "token-123")

    def test_get_current_user_success(self) -> None:
        user = build_user()
        db = MagicMock()
        db.get.return_value = user
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="abc")
        request = MagicMock()
        request.cookies = {}

        with patch("app.api.v1.auth.decode_access_token", return_value={"sub": str(user.id)}):
            current_user = get_current_user(request=request, credentials=credentials, db=db)

        self.assertEqual(current_user.id, user.id)

    def test_login_sets_http_only_cookie(self) -> None:
        self._create_user(email="cookie@example.com", password="Secret123")

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/login",
                json={"email": "cookie@example.com", "password": "Secret123"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cookies.get(settings.AUTH_COOKIE_NAME))
        cookie_header = response.headers.get("set-cookie", "")
        self.assertIn(f"{settings.AUTH_COOKIE_NAME}=", cookie_header)
        self.assertIn("HttpOnly", cookie_header)
        self.assertIn("SameSite=lax", cookie_header)

    def test_me_works_with_cookie_session(self) -> None:
        self._create_user(email="me@example.com", password="Secret123")

        with TestClient(app) as client:
            login_response = client.post(
                "/api/v1/login",
                json={"email": "me@example.com", "password": "Secret123"},
            )
            response = client.get("/api/v1/me")

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "me@example.com")

    def test_logout_clears_cookie_and_invalidates_me(self) -> None:
        self._create_user(email="logout@example.com", password="Secret123")

        with TestClient(app) as client:
            client.post(
                "/api/v1/login",
                json={"email": "logout@example.com", "password": "Secret123"},
            )
            logout_response = client.post("/api/v1/logout")
            me_response = client.get("/api/v1/me")

        self.assertEqual(logout_response.status_code, 204)
        cookie_header = logout_response.headers.get("set-cookie", "")
        self.assertIn(f"{settings.AUTH_COOKIE_NAME}=", cookie_header)
        self.assertTrue("Max-Age=0" in cookie_header or "expires=" in cookie_header.lower())
        self.assertEqual(me_response.status_code, 401)

    def test_me_accepts_bearer_fallback_for_api_compatibility(self) -> None:
        user = self._create_user(email="bearer@example.com", password="Secret123")
        access_token = create_access_token(subject=str(user.id))

        with TestClient(app) as client:
            response = client.get(
                "/api/v1/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "bearer@example.com")

    def test_signup_rejects_invalid_email(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/signup",
                json={"email": "not-an-email", "password": "Secret123"},
            )

        self.assertEqual(response.status_code, 422)

    def test_signup_rejects_short_password(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/signup",
                json={"email": "short@example.com", "password": "abc123"},
            )

        self.assertEqual(response.status_code, 422)

    def test_signup_rejects_whitespace_password(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/signup",
                json={"email": "space@example.com", "password": "        "},
            )

        self.assertEqual(response.status_code, 422)

    def test_signup_normalizes_email(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/signup",
                json={"email": "  MixedCase@Example.COM  ", "password": "Secret123"},
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["email"], "mixedcase@example.com")

    def test_production_rejects_placeholder_jwt_secret(self) -> None:
        with self.assertRaises(ValueError):
            _validate_runtime_settings(
                Settings(
                APP_ENV="production",
                DATABASE_URL="sqlite+pysqlite:///:memory:",
                JWT_SECRET_KEY="replace-with-a-long-random-jwt-secret-min-32-chars",
            )
            )


if __name__ == "__main__":
    unittest.main()
