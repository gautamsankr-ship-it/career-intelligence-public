"""Synthetic demo authentication and audit storage."""

from __future__ import annotations

import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pwdlib import PasswordHash

AUTH_DB_PATH = os.getenv("DEMO_AUTH_DB_PATH", "runtime/demo-auth.db")
password_hash = PasswordHash.recommended()


@dataclass(frozen=True)
class DemoUser:
    username: str
    role: str


class DemoAuthStore:
    """Authentication store with PostgreSQL deployment and SQLite local modes."""

    def __init__(self, path: str | Path | None = None, database_url: str | None = None):
        configured_url = database_url if database_url is not None else os.getenv("CAREER_AUTH_DATABASE_URL", "")
        self.database_url = configured_url.strip()
        self.path = None if self.database_url else Path(path or AUTH_DB_PATH)

    @property
    def uses_postgresql(self) -> bool:
        return bool(self.database_url)

    def _connect(self):
        if self.uses_postgresql:
            try:
                import psycopg
                from psycopg.rows import dict_row
            except ImportError as exc:
                raise RuntimeError("PostgreSQL support requires the psycopg package.") from exc
            return psycopg.connect(self.database_url, row_factory=dict_row)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_schema(self) -> None:
        with self._connect() as connection:
            if self.uses_postgresql:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS demo_users (
                        username TEXT PRIMARY KEY,
                        role TEXT NOT NULL CHECK (role IN ('OWNER', 'RECRUITER')),
                        password_hash TEXT NOT NULL
                    )
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS demo_sessions (
                        session_id TEXT PRIMARY KEY,
                        username TEXT NOT NULL REFERENCES demo_users(username),
                        expires_at TIMESTAMPTZ NOT NULL
                    )
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS demo_auth_audit_events (
                        id BIGSERIAL PRIMARY KEY,
                        username TEXT,
                        role TEXT CHECK (role IN ('OWNER', 'RECRUITER')),
                        event_type TEXT NOT NULL,
                        occurred_at_utc TIMESTAMPTZ NOT NULL,
                        request_path TEXT,
                        success BOOLEAN NOT NULL,
                        user_agent TEXT,
                        ip_address TEXT
                    )
                """)
            else:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS demo_users (
                        username TEXT PRIMARY KEY,
                        role TEXT NOT NULL CHECK (role IN ('OWNER', 'RECRUITER')),
                        password_hash TEXT NOT NULL
                    )
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS demo_sessions (
                        session_id TEXT PRIMARY KEY,
                        username TEXT NOT NULL REFERENCES demo_users(username),
                        expires_at TEXT NOT NULL
                    )
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS demo_auth_audit_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        role TEXT,
                        event_type TEXT NOT NULL,
                        occurred_at_utc TEXT NOT NULL,
                        request_path TEXT,
                        success INTEGER NOT NULL,
                        user_agent TEXT,
                        ip_address TEXT
                    )
                """)

    def upsert_user(self, username: str, password: str, role: str) -> None:
        username = username.strip()
        role = role.strip().upper()
        if not username or not password:
            raise ValueError("Username and password are required")
        if role not in {"OWNER", "RECRUITER"}:
            raise ValueError("Role must be OWNER or RECRUITER")
        self.ensure_schema()
        placeholder = "%s" if self.uses_postgresql else "?"
        with self._connect() as connection:
            connection.execute(
                f"INSERT INTO demo_users (username, role, password_hash) VALUES ({placeholder}, {placeholder}, {placeholder}) "
                "ON CONFLICT(username) DO UPDATE SET role = excluded.role, password_hash = excluded.password_hash",
                (username, role, password_hash.hash(password)),
            )

    def authenticate(self, username: str, password: str) -> DemoUser | None:
        self.ensure_schema()
        placeholder = "%s" if self.uses_postgresql else "?"
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT username, role, password_hash FROM demo_users WHERE lower(username) = lower({placeholder})",
                (username.strip(),),
            ).fetchone()
        if row is None or not password_hash.verify(password, row["password_hash"]):
            return None
        return DemoUser(username=row["username"], role=row["role"])

    def create_session(self, user: DemoUser, ttl_seconds: int = 8 * 60 * 60) -> str:
        self.ensure_schema()
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        if not self.uses_postgresql:
            expires_at = expires_at.isoformat()
        placeholder = "%s" if self.uses_postgresql else "?"
        with self._connect() as connection:
            connection.execute(
                f"INSERT INTO demo_sessions (session_id, username, expires_at) VALUES ({placeholder}, {placeholder}, {placeholder})",
                (session_id, user.username, expires_at),
            )
        return session_id

    def get_session(self, session_id: str | None) -> DemoUser | None:
        if not session_id:
            return None
        self.ensure_schema()
        placeholder = "%s" if self.uses_postgresql else "?"
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT s.username, u.role, s.expires_at FROM demo_sessions s JOIN demo_users u "
                f"ON u.username = s.username WHERE s.session_id = {placeholder}",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            expires_at = row["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                connection.execute(f"DELETE FROM demo_sessions WHERE session_id = {placeholder}", (session_id,))
                return None
        return DemoUser(username=row["username"], role=row["role"])

    def delete_session(self, session_id: str | None) -> None:
        if not session_id:
            return
        self.ensure_schema()
        placeholder = "%s" if self.uses_postgresql else "?"
        with self._connect() as connection:
            connection.execute(f"DELETE FROM demo_sessions WHERE session_id = {placeholder}", (session_id,))

    def record_audit_event(
        self,
        *,
        event_type: str,
        username: str | None,
        role: str | None,
        request_path: str | None,
        success: bool,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        self.ensure_schema()
        occurred_at = datetime.now(timezone.utc)
        if not self.uses_postgresql:
            occurred_at = occurred_at.isoformat()
        placeholder = "%s" if self.uses_postgresql else "?"
        with self._connect() as connection:
            connection.execute(
                f"INSERT INTO demo_auth_audit_events "
                f"(username, role, event_type, occurred_at_utc, request_path, success, user_agent, ip_address) "
                f"VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})",
                (username, role, event_type, occurred_at, request_path, success, user_agent, ip_address),
            )
