from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.models.task import Task
from app.models.user import User


class FakeScalars:
    def __init__(self, values: list[object]):
        self._values = values

    def all(self) -> list[object]:
        return list(self._values)


class FakeExecuteResult:
    def __init__(
        self,
        *,
        one: object | None = None,
        scalar_values: list[object] | None = None,
        rows: list[tuple[object, int]] | None = None,
    ):
        self._one = one
        self._scalar_values = scalar_values or []
        self._rows = rows or []

    def scalar_one_or_none(self) -> object | None:
        return self._one

    def scalars(self) -> FakeScalars:
        return FakeScalars(self._scalar_values)

    def all(self) -> list[tuple[object, int]]:
        return list(self._rows)


def build_user(**overrides: object) -> User:
    payload = {
        "id": uuid.uuid4(),
        "email": "user@example.com",
        "password_hash": "hashed-password",
        "created_at": datetime.now(UTC),
    }
    payload.update(overrides)
    return User(**payload)


def build_task(**overrides: object) -> Task:
    payload = {
        "id": uuid.uuid4(),
        "user_id": overrides.pop("user_id", uuid.uuid4()),
        "title": "Test task",
        "description": "Test description",
        "status": "pending",
        "task_type": "general",
        "agent_name": "GeneralAssistantAgent",
        "result_text": None,
        "execution_trace": [],
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    payload.update(overrides)
    return Task(**payload)
