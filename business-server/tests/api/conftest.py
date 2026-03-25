"""
Fixtures for FastAPI integration tests against a real PostgreSQL database
and real Clerk JWTs (see business-server/.env.test).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _load_env_test() -> None:
    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env.test"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value


_load_env_test()


@pytest.fixture(scope="session")
def test_admin_token() -> str:
    token = os.environ.get("TEST_ADMIN_TOKEN", "").strip()
    if not token:
        pytest.skip("Set TEST_ADMIN_TOKEN in .env.test (or environment)")
    return token


@pytest.fixture(scope="session")
def test_customer_token() -> str:
    token = os.environ.get("TEST_CUSTOMER_TOKEN", "").strip()
    if not token:
        pytest.skip("Set TEST_CUSTOMER_TOKEN in .env.test (or environment)")
    return token


@pytest.fixture
def admin_headers(test_admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {test_admin_token}"}


@pytest.fixture
def customer_headers(test_customer_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {test_customer_token}"}


@pytest.fixture
def invalid_headers() -> dict[str, str]:
    return {"Authorization": "Bearer not-a-valid-jwt"}


@pytest.fixture
def no_headers() -> dict[str, str]:
    return {}


@pytest.fixture(scope="session")
def client() -> TestClient:
    from app.api import app

    with TestClient(app) as c:
        yield c
