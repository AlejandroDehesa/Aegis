from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.v1.auth import get_current_user, login, signup
from app.schemas.user import UserCreate, UserLogin

from .helpers import FakeExecuteResult, build_user


class AuthTests(unittest.TestCase):
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

        with self.assertRaises(HTTPException) as context:
            login(UserLogin(email="none@example.com", password="wrong"), db=db)

        self.assertEqual(context.exception.status_code, 401)

    def test_login_success_returns_access_token(self) -> None:
        user = build_user(email="ok@example.com", password_hash="hashed")
        db = MagicMock()
        db.execute.return_value = FakeExecuteResult(one=user)

        with (
            patch("app.api.v1.auth.verify_password", return_value=True),
            patch("app.api.v1.auth.create_access_token", return_value="token-123"),
        ):
            response = login(UserLogin(email="ok@example.com", password="secret"), db=db)

        self.assertEqual(response.access_token, "token-123")

    def test_get_current_user_success(self) -> None:
        user = build_user()
        db = MagicMock()
        db.get.return_value = user
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="abc")

        with patch("app.api.v1.auth.decode_access_token", return_value={"sub": str(user.id)}):
            current_user = get_current_user(credentials=credentials, db=db)

        self.assertEqual(current_user.id, user.id)


if __name__ == "__main__":
    unittest.main()
