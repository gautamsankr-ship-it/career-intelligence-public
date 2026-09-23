"""Provision explicitly configured synthetic demo users."""

from __future__ import annotations

import os

from app.services.demo_auth_service import DemoAuthStore


def main() -> None:
    store = DemoAuthStore()
    owner_username = os.getenv("DEMO_OWNER_USERNAME", "").strip()
    owner_password = os.getenv("DEMO_OWNER_PASSWORD", "")
    recruiter_username = os.getenv("DEMO_RECRUITER_USERNAME", "").strip()
    recruiter_password = os.getenv("DEMO_RECRUITER_PASSWORD", "")
    if not owner_username or not owner_password:
        raise SystemExit("Set DEMO_OWNER_USERNAME and DEMO_OWNER_PASSWORD privately first.")
    if not recruiter_username or not recruiter_password:
        raise SystemExit("Set DEMO_RECRUITER_USERNAME and DEMO_RECRUITER_PASSWORD privately first.")
    store.upsert_user(owner_username, owner_password, "OWNER")
    store.upsert_user(recruiter_username, recruiter_password, "RECRUITER")
    print("Synthetic demo authentication bootstrap complete.")


if __name__ == "__main__":
    main()
