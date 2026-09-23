"""Synthetic recruiter-facing FastAPI/Jinja demonstration."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

from app.services.demo_auth_service import DemoAuthStore, DemoUser

app = FastAPI(title="Synthetic Career Intelligence Demo")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates" / "dashboard"))
SESSION_COOKIE = "demo_session"
SESSION_MAX_AGE = 8 * 60 * 60
DEPLOYMENT_MODE = os.getenv("CAREER_DEPLOYMENT_MODE", "0").lower() in {"1", "true", "yes"}
configured_secret = os.getenv("CAREER_SESSION_SECRET", "").strip()
if DEPLOYMENT_MODE and len(configured_secret) < 32:
    raise RuntimeError("CAREER_SESSION_SECRET must be at least 32 characters in deployment mode")
if DEPLOYMENT_MODE and not os.getenv("CAREER_AUTH_DATABASE_URL", "").strip():
    raise RuntimeError("CAREER_AUTH_DATABASE_URL must be configured in deployment mode")
SESSION_SIGNER = TimestampSigner(configured_secret or secrets.token_urlsafe(32))
SESSION_HTTPS = os.getenv("CAREER_SESSION_HTTPS", "0").lower() in {"1", "true", "yes"}


def server_config(environment: dict[str, str] | None = None) -> tuple[str, int]:
    values = environment if environment is not None else os.environ
    deployment = values.get("CAREER_DEPLOYMENT_MODE", "0").lower() in {"1", "true", "yes"}
    host = "0.0.0.0" if deployment else values.get("CAREER_HOST", "127.0.0.1")
    port_name = "PORT" if deployment else "CAREER_PORT"
    return host, int(values.get(port_name, "8000"))


def _session_id(request: Request) -> str | None:
    value = request.cookies.get(SESSION_COOKIE)
    if not value:
        return None
    try:
        return SESSION_SIGNER.unsign(value, max_age=SESSION_MAX_AGE).decode("utf-8")
    except (BadSignature, SignatureExpired):
        return None


def current_user(request: Request) -> DemoUser | None:
    user = DemoAuthStore().get_session(_session_id(request))
    request.state.demo_user = user
    return user


def _set_session_cookie(response: RedirectResponse, session_id: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        SESSION_SIGNER.sign(session_id).decode("utf-8"),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=SESSION_HTTPS,
    )


def _clear_session_cookie(response: RedirectResponse) -> None:
    response.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax", secure=SESSION_HTTPS)


@app.middleware("http")
async def authentication_guard(request: Request, call_next):
    if request.url.path in {"/login", "/logout", "/health"}:
        request.state.demo_user = current_user(request)
        return await call_next(request)
    user = current_user(request)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    if user.role == "RECRUITER" and (request.url.path != "/recruiter-demo" or request.method != "GET"):
        return PlainTextResponse("Recruiter access is limited to the synthetic demo.", status_code=403)
    return await call_next(request)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": ""})


@app.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    store = DemoAuthStore()
    user = store.authenticate(username, password)
    if user is None:
        store.record_audit_event(
            event_type="LOGIN_FAILURE",
            username=None,
            role=None,
            request_path="/login",
            success=False,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Sign-in failed. Check your username and password."},
            status_code=401,
        )
    session_id = store.create_session(user)
    store.record_audit_event(
        event_type="LOGIN_SUCCESS",
        username=user.username,
        role=user.role,
        request_path="/login",
        success=True,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    destination = "/recruiter-demo" if user.role == "RECRUITER" else "/"
    response = RedirectResponse(url=destination, status_code=303)
    _set_session_cookie(response, session_id)
    return response


@app.get("/logout")
def logout(request: Request):
    store = DemoAuthStore()
    user = current_user(request)
    if user is not None:
        store.record_audit_event(
            event_type="LOGOUT",
            username=user.username,
            role=user.role,
            request_path="/logout",
            success=True,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    store.delete_session(_session_id(request))
    response = RedirectResponse(url="/login", status_code=303)
    _clear_session_cookie(response)
    return response


@app.post("/logout")
def logout_post(request: Request):
    return logout(request)


@app.get("/health")
def health():
    return JSONResponse({"status": "healthy", "demo": True})


@app.get("/")
def owner_demo(request: Request):
    return templates.TemplateResponse(
        request,
        "owner_demo.html",
        {"active": "owner", "title": "Synthetic owner demo"},
    )


@app.get("/recruiter-demo")
def recruiter_demo(request: Request):
    user = getattr(request.state, "demo_user", None)
    DemoAuthStore().record_audit_event(
        event_type="RECRUITER_DEMO_VIEW",
        username=user.username if user else None,
        role=user.role if user else None,
        request_path="/recruiter-demo",
        success=True,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return templates.TemplateResponse(
        request,
        "recruiter_demo.html",
        {
            "active": "recruiter",
            "metrics": [
                {"label": "Synthetic opportunities", "value": 3},
                {"label": "Review queue", "value": 1},
                {"label": "Confirmed submissions", "value": 0},
            ],
            "opportunities": [
                {"company": "Northstar Ledger", "role": "Finance Systems Analyst", "location": "Edinburgh / Remote", "status": "Synthetic review"},
                {"company": "Harbour Metrics", "role": "Part-time FP&A Analyst", "location": "Glasgow", "status": "Needs verification"},
                {"company": "Juniper Payments", "role": "Fintech Operations Associate", "location": "Remote UK", "status": "Watch"},
            ],
        },
    )


@app.get("/action-required", response_class=HTMLResponse)
def action_required(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "owner_demo.html",
        {"active": "owner", "title": "Synthetic action review"},
    )
