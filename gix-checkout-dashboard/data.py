from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import create_client

_ROOT = Path(__file__).resolve().parent


def _load_env() -> None:
    load_dotenv(_ROOT / ".env")


def _client_from_env() -> Any | None:
    _load_env()
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_KEY") or "").strip()
    if not url or not key:
        return None
    return create_client(url, key)


def fetch_checkouts(client: Any, email: str) -> list[dict[str, Any]]:
    result = (
        client.table("checkouts")
        .select("*")
        .ilike("student_email", email.strip())
        .execute()
    )
    return result.data or []


def fetch_event_categories(client: Any) -> list[str]:
    result = client.table("events").select("category").execute()
    rows = result.data or []
    cats = sorted({str(r["category"]).strip() for r in rows if r.get("category")})
    return cats


def fetch_events_with_client(
    client: Any, categories: list[str]
) -> list[dict[str, Any]]:
    now_iso = datetime.now(timezone.utc).isoformat()
    q = client.table("events").select("*").gte("event_date", now_iso)
    if categories:
        q = q.in_("category", categories)
    result = q.order("event_date", desc=False).execute()
    return result.data or []


def fetch_events(categories: list[str]) -> list[dict[str, Any]]:
    """Load Supabase client from environment only. Used by pytest."""
    client = _client_from_env()
    if client is None:
        return []
    return fetch_events_with_client(client, categories)
