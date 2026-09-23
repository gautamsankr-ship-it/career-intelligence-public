# Synthetic Application Resolution Portfolio

This repository is a small, public-safe demonstration of grouped application-answer resolution.

It contains only source code, a safe HTML template, synthetic demo data, and tests that use
temporary directories. It deliberately contains no candidate profile, application history,
resume, vault export, database, credential, token, or log.

## Run

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m app.demo_auth_cli
uvicorn app.api.dashboard:app --host 127.0.0.1 --port 8000
python phase10_demo.py
```

Open `http://127.0.0.1:8000/login`. Supply the demo owner and recruiter
credentials privately through environment variables before running the
bootstrap command; no credentials are included in this repository. In
deployment mode, use `0.0.0.0` and the platform-provided `PORT`, and require a
session secret of at least 32 characters. Cookies are HTTP-only,
`SameSite=Lax`, and secure when `CAREER_SESSION_HTTPS=1`.

The optional local demo authentication store is `runtime/demo-auth.db` and is
ignored by Git. Persistent Render deployment requires Neon/PostgreSQL or
another managed database for authentication and audit logs; this public demo
does not connect to any private application database.

## Neon/PostgreSQL authentication

For deployment, set `CAREER_AUTH_DATABASE_URL` to the private Neon PostgreSQL
connection string in Render’s environment settings. Do not put the URL in
GitHub, this README, `.env.example`, or chat. When this variable is present,
the demo auth store uses PostgreSQL; when it is absent outside deployment, it
uses the ignored SQLite path for local development and tests only.

The application creates its small schema safely on startup or during the
bootstrap command; no private CRM database is migrated or accessed. The
schema contains `demo_users` (synthetic usernames, roles, and Argon2id hashes),
`demo_sessions` (opaque server-side session IDs and UTC expiry timestamps),
and `demo_auth_audit_events`. Audit rows record safe login, logout, and
synthetic recruiter-demo-view events with UTC time, role, path, success, and
optional request metadata. Passwords, session cookie contents, tokens, and
candidate data are never stored.

Set the four demo credential variables privately, then run
`python -m app.demo_auth_cli` once as a controlled provisioning step. The
bootstrap is safe for either backend and never prints passwords. In deployment
mode, startup fails unless both `CAREER_SESSION_SECRET` and
`CAREER_AUTH_DATABASE_URL` are configured.

## Render deployment preparation

Use this exact Render start command:

```text
uvicorn app.api.dashboard:app --host 0.0.0.0 --port $PORT
```

Provision the synthetic users only after setting these values as Render
private environment variables: `DEMO_OWNER_USERNAME`, `DEMO_OWNER_PASSWORD`,
`DEMO_RECRUITER_USERNAME`, and `DEMO_RECRUITER_PASSWORD`. Run the one-time
bootstrap command in a controlled Render shell or provisioning step:

```text
python -m app.demo_auth_cli
```

The bootstrap reads the four variables, stores only Argon2id password hashes,
and prints no passwords or secrets. Never put those values in the start
command, source code, README, or GitHub. SQLite on ordinary Render free
storage is not persistent across restarts or replacement instances, so it is
not suitable for production authentication. Before production use, configure
Neon/PostgreSQL or another managed persistent database for authentication and
audit logs; the private application database remains separate and is never
connected by this repository.

## Recruiter demo access

The recruiter flow is a synthetic, read-only demonstration at
`/recruiter-demo`. It contains only synthetic companies, roles, statuses, and
metrics. It does not include private candidate data, CRM records, application
history, resumes, documents, Gmail, or automation controls. There is no public
registration. Credentials must be supplied privately through Render
environment variables and must never be placed in GitHub, this README,
LinkedIn, a CV, or chat.

The public OWNER role, when provisioned, also sees synthetic demo data only;
it never exposes a private production dashboard. Neon/PostgreSQL is required
for persistent production authentication and audit logs.

## Safety boundary

All personal-looking values are synthetic placeholders such as `candidate@example.test` and
`Synthetic Company`. Tests use `tmp_path`; no repository-relative runtime storage is used.
