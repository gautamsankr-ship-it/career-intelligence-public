from __future__ import annotations

import sqlite3
import secrets
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.api.dashboard as dashboard
from app.services import demo_auth_service
from app.services.demo_auth_service import DemoAuthStore


@pytest.fixture
def public_client(tmp_path, monkeypatch):
    auth_db = tmp_path / "demo-auth.db"
    monkeypatch.setattr(demo_auth_service, "AUTH_DB_PATH", str(auth_db))
    store = DemoAuthStore()
    credentials = {
        "owner_username": f"synthetic-owner-{secrets.token_hex(4)}",
        "owner_password": secrets.token_urlsafe(16),
        "recruiter_username": f"synthetic-recruiter-{secrets.token_hex(4)}",
        "recruiter_password": secrets.token_urlsafe(16),
    }
    store.upsert_user(credentials["owner_username"], credentials["owner_password"], "OWNER")
    store.upsert_user(credentials["recruiter_username"], credentials["recruiter_password"], "RECRUITER")
    return TestClient(dashboard.app), auth_db, credentials


def test_login_works_without_openai_key(public_client, monkeypatch):
    client, _, _ = public_client
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.get("/login")
    assert response.status_code == 200
    assert "Synthetic career-intelligence demo" in response.text


def test_render_start_configuration_is_valid_without_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    readme = Path(__file__).resolve().parents[1] / "README.md"
    assert "uvicorn app.api.dashboard:app --host 0.0.0.0 --port $PORT" in readme.read_text(encoding="utf-8")
    assert dashboard.server_config({"CAREER_DEPLOYMENT_MODE": "1", "PORT": "10000"}) == ("0.0.0.0", 10000)


def test_owner_demo_login_is_synthetic(public_client):
    client, _, credentials = public_client
    response = client.post("/login", data={"username": credentials["owner_username"], "password": credentials["owner_password"]}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    page = client.get("/")
    assert page.status_code == 200
    assert "No private production dashboard" in page.text


def test_recruiter_login_reaches_synthetic_demo_only(public_client):
    client, _, credentials = public_client
    response = client.post("/login", data={"username": credentials["recruiter_username"], "password": credentials["recruiter_password"]}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/recruiter-demo"
    page = client.get("/recruiter-demo")
    assert page.status_code == 200
    assert "Synthetic recruiter demonstration" in page.text
    assert "Northstar Ledger" in page.text
    assert "Harbour Metrics" in page.text
    assert "Juniper Payments" in page.text
    assert "candidate@example" not in page.text


def test_recruiter_cannot_access_private_or_unknown_routes_or_write(public_client):
    client, _, credentials = public_client
    client.post("/login", data={"username": credentials["recruiter_username"], "password": credentials["recruiter_password"]})
    for path in ("/", "/action-required", "/applications", "/automation", "/private-production-route", "/documents/resume"):
        assert client.get(path).status_code == 403
    assert client.post("/apply", data={}).status_code == 403
    assert client.post("/recruiter-demo", data={}).status_code == 403


def test_logout_invalidates_server_session(public_client):
    client, _, credentials = public_client
    client.post("/login", data={"username": credentials["recruiter_username"], "password": credentials["recruiter_password"]})
    assert client.get("/recruiter-demo").status_code == 200
    assert client.post("/logout", follow_redirects=False).status_code == 303
    assert client.get("/recruiter-demo", follow_redirects=False).status_code == 303


def test_unauthenticated_and_health_behavior(public_client):
    client, _, _ = public_client
    assert client.get("/recruiter-demo", follow_redirects=False).status_code == 303
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["demo"] is True


def test_passwords_are_argon2id_hashes_and_runtime_only(public_client):
    _, auth_db, _ = public_client
    with sqlite3.connect(auth_db) as connection:
        stored = connection.execute("SELECT password_hash FROM demo_users").fetchall()
    assert all(row[0].startswith("$argon2id$") for row in stored)
    assert all(row[0] not in {""} for row in stored)
    assert "app/data" not in str(auth_db)


def test_sqlite_audit_events_record_synthetic_recruiter_activity(public_client):
    client, auth_db, credentials = public_client
    client.post("/login", data={"username": credentials["recruiter_username"], "password": credentials["recruiter_password"]})
    client.get("/recruiter-demo")
    client.post("/logout")
    with sqlite3.connect(auth_db) as connection:
        events = [row[0] for row in connection.execute("SELECT event_type FROM demo_auth_audit_events ORDER BY id")]
    assert "LOGIN_SUCCESS" in events
    assert "RECRUITER_DEMO_VIEW" in events
    assert "LOGOUT" in events


def test_postgresql_backend_is_selected_without_connecting():
    store = DemoAuthStore(database_url="postgresql" + "://synthetic-test.invalid/demo")
    assert store.uses_postgresql is True
    assert store.path is None


def test_deployment_import_requires_postgresql_url():
    environment = os.environ.copy()
    environment.pop("CAREER_AUTH_DATABASE_URL", None)
    environment["CAREER_DEPLOYMENT_MODE"] = "1"
    environment["CAREER_SESSION_SECRET"] = "synthetic-test-secret-012345678901234567890123"
    result = subprocess.run(
        [sys.executable, "-c", "import app.api.dashboard"],
        env=environment,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    assert result.returncode != 0
    assert "CAREER_AUTH_DATABASE_URL must be configured" in result.stderr
