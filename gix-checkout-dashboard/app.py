from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

import requests
import streamlit as st
from supabase import create_client

from data import (
    fetch_checkouts as db_fetch_checkouts,
    fetch_event_categories,
    fetch_events_with_client,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast?"
    "latitude=47.6566&longitude=-122.3035"
    "&daily=precipitation_sum,temperature_2m_max"
    "&timezone=America/Los_Angeles&forecast_days=3"
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _read_env(name: str) -> str:
    try:
        val = st.secrets[name]
        s = str(val).strip()
        if s:
            return s
    except (KeyError, FileNotFoundError, TypeError, AttributeError):
        pass
    return (os.getenv(name) or "").strip()


def get_supabase_client() -> tuple[Any | None, str | None]:
    try:
        url = _read_env("SUPABASE_URL")
        key = _read_env("SUPABASE_KEY")
        if not url or not key:
            return None, "missing_creds"
        client = create_client(url, key)
        if client is None:
            return None, "client_none"
        return client, None
    except Exception as exc:
        logger.warning("Supabase create_client failed: %s", exc)
        return None, "client_error"


@st.cache_resource
def get_supabase() -> Any | None:
    client, err = get_supabase_client()
    if err is not None or client is None:
        return None
    return client


def fetch_weather() -> str | None:
    try:
        resp = requests.get(WEATHER_URL, timeout=5)
        if resp.status_code != 200:
            logger.warning("Open-Meteo returned status %s", resp.status_code)
            return None
        weather_data: dict[str, Any] = resp.json()
        try:
            assert "daily" in weather_data, "weather response missing 'daily' field"
            assert "precipitation_sum" in weather_data["daily"], "missing precipitation_sum"
            assert isinstance(
                weather_data["daily"]["precipitation_sum"], list
            ), "precipitation_sum should be a list"
            assert len(weather_data["daily"]["precipitation_sum"]) == 3, (
                "expected 3 forecast days"
            )
        except AssertionError as exc:
            logger.warning("Open-Meteo response assert failed: %s", exc)
            return None

        daily = weather_data["daily"]
        times: list[str] = daily.get("time") or []
        precs: list[float | None] = daily["precipitation_sum"]
        heavy_days: list[str] = []
        for i, p in enumerate(precs):
            val = float(p) if p is not None else 0.0
            if val > 5.0 and i < len(times):
                try:
                    d = datetime.fromisoformat(times[i]).date()
                    heavy_days.append(d.strftime("%A"))
                except ValueError:
                    heavy_days.append(times[i])
        if not heavy_days:
            return None
        if len(heavy_days) == 1:
            return (
                f"Heavy rain expected {heavy_days[0]}, consider returning early"
            )
        return (
            "Heavy rain expected "
            + ", ".join(heavy_days[:-1])
            + f" and {heavy_days[-1]}, consider returning early"
        )
    except requests.RequestException as exc:
        logger.warning("Open-Meteo request failed: %s", exc)
        return None
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning("Open-Meteo parse failed: %s", exc)
        return None


def parse_ts(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def due_status(due: datetime, now: datetime) -> tuple[str, str]:
    due_d = due.astimezone(timezone.utc).date()
    today = now.astimezone(timezone.utc).date()
    delta = (due_d - today).days
    if delta < 0:
        n = -delta
        label = "1 day overdue" if n == 1 else f"{n} days overdue"
        return label, "overdue"
    if delta == 0:
        return "Due today", "soon"
    if delta == 1:
        return "Due tomorrow", "soon"
    if delta <= 3:
        return f"Due in {delta} days", "soon"
    return f"Due in {delta} days", "ok"


def fmt_short(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%b %d, %Y")


def fmt_event_date(dt: datetime) -> str:
    d = dt.astimezone(timezone.utc)
    return f"{d:%a}, {d:%b} {d.day}, {d:%Y}"


def render_active_checkout_card(row: dict[str, Any], now: datetime) -> None:
    due = parse_ts(row["due_date"])
    co = parse_ts(row["checkout_date"])
    status_text, band = due_status(due, now)
    with st.container(border=True):
        st.markdown(f"**{row.get('item_name', 'Item')}**")
        st.caption(row.get("item_category", "uncategorized"))
        st.write(f"Checked out {fmt_short(co)}")
        st.write(f"Due {fmt_short(due)}")
        st.write(status_text)
        if band == "overdue":
            st.markdown(":red[Overdue]")
        elif band == "soon":
            st.markdown(":orange[Due soon]")
        else:
            st.markdown("On track")
        if row.get("notes"):
            st.caption(row["notes"])


def render_returned_card(row: dict[str, Any]) -> None:
    due = parse_ts(row["due_date"])
    co = parse_ts(row["checkout_date"])
    with st.container(border=True):
        st.markdown(f"**{row.get('item_name', 'Item')}**")
        st.caption(row.get("item_category", "uncategorized"))
        st.write(f"Checked out {fmt_short(co)}, due {fmt_short(due)}")


def layout_checkout_cards(
    items: list[dict[str, Any]],
    render_one,
    *,
    single_row_max: int,
    wrapped_cols: int,
) -> None:
    if not items:
        return
    if len(items) <= single_row_max:
        cols = st.columns(len(items))
        for col, row in zip(cols, items):
            with col:
                render_one(row)
        return
    for i in range(0, len(items), wrapped_cols):
        chunk = items[i : i + wrapped_cols]
        cols = st.columns(wrapped_cols)
        for j, row in enumerate(chunk):
            with cols[j]:
                render_one(row)


def _event_row_valid(row: dict[str, Any]) -> bool:
    return bool(
        row.get("title")
        and row.get("event_date")
        and row.get("category")
    )


def render_header() -> None:
    st.title("GIX student dashboard")
    st.caption(
        "Check your equipment loans and browse upcoming GIX events."
    )


def fetch_checkouts(email: str) -> list[dict[str, Any]]:
    client = get_supabase()
    if client is None:
        return []
    return db_fetch_checkouts(client, email)


def render_checkouts_tab() -> None:
    client = get_supabase()
    if client is None:
        _, err = get_supabase_client()
        if err == "missing_creds":
            st.error(
                "Database credentials are missing. For Streamlit Cloud, open "
                "the app **Settings → Secrets** and add SUPABASE_URL and "
                "SUPABASE_KEY (TOML), then **Reboot** or redeploy. Locally, copy "
                ".env.example to .env and fill both values."
            )
        else:
            st.error(
                "Cannot reach the database. Check your Supabase URL and key in "
                "Secrets, then try again."
            )
        return

    st.subheader("Equipment checkouts")
    st.caption("See what you have out and when it is due.")

    with st.form("email_form"):
        email_input = st.text_input(
            "Your email",
            placeholder="netid@uw.edu",
            help="Same email staff use for your checkout record.",
        )
        submitted = st.form_submit_button("Show my checkouts")

    hint = fetch_weather()
    if hint:
        st.info(hint)

    if submitted:
        st.session_state["dashboard_email"] = (email_input or "").strip()

    lookup_email = st.session_state.get("dashboard_email", "").strip()

    if not lookup_email:
        return

    if not EMAIL_PATTERN.match(lookup_email):
        st.warning("Please enter a valid email address.")
        return

    try:
        rows = fetch_checkouts(lookup_email)
    except Exception:
        st.error("Cannot reach the database. Try refreshing.")
        return

    if not rows:
        st.info("No checkouts found for this email.")
        return

    now = datetime.now(timezone.utc)
    active = [r for r in rows if not r.get("returned")]
    returned = [r for r in rows if r.get("returned")]

    active.sort(key=lambda r: parse_ts(r["due_date"]))

    st.subheader("Active checkouts")
    if not active:
        st.write("No active checkouts.")
    else:
        layout_checkout_cards(
            active,
            lambda r: render_active_checkout_card(r, now),
            single_row_max=3,
            wrapped_cols=2,
        )

    with st.expander("Returned history"):
        if not returned:
            st.write("No returned items on file.")
        else:
            returned.sort(
                key=lambda r: parse_ts(r["due_date"]), reverse=True
            )
            layout_checkout_cards(
                returned,
                render_returned_card,
                single_row_max=3,
                wrapped_cols=2,
            )


def render_events_tab() -> None:
    st.subheader("Upcoming GIX events")
    st.caption("Filter by category to see what is coming up.")

    client = get_supabase()
    if client is None:
        st.error(
            "Cannot reach the events database. Try refreshing."
        )
        return

    try:
        all_categories = fetch_event_categories(client)
    except Exception:
        st.error(
            "Cannot reach the events database. Try refreshing."
        )
        return

    if not all_categories:
        st.info("No event categories found yet.")
        return

    selected = st.multiselect(
        "Categories",
        options=all_categories,
        default=all_categories,
    )

    if not selected:
        st.info("Select at least one category to see events.")
        return

    try:
        raw_events = fetch_events_with_client(client, selected)
    except Exception:
        st.error(
            "Cannot reach the events database. Try refreshing."
        )
        return

    valid_events: list[dict[str, Any]] = []
    skipped = 0
    for row in raw_events:
        if _event_row_valid(row):
            valid_events.append(row)
        else:
            skipped += 1

    st.caption(f"Showing {len(valid_events)} events")

    if not valid_events:
        st.info(
            "No events match these categories. Try selecting more."
        )
        if skipped:
            st.warning(
                f"{skipped} events were hidden due to missing data."
            )
        return

    for row in valid_events:
        ed = parse_ts(str(row["event_date"]))
        with st.container(border=True):
            st.markdown(f"**{row['title']}**")
            st.markdown(f":violet[**{row['category']}**]")
            st.write(fmt_event_date(ed))
            st.write(row.get("location") or "Location TBD")
            st.write(row.get("description") or "")

    if skipped:
        st.warning(
            f"{skipped} events were hidden due to missing data."
        )


st.set_page_config(page_title="GIX Checkout", layout="centered")

render_header()

tab_checkouts, tab_events = st.tabs(["My checkouts", "GIX events"])

with tab_checkouts:
    render_checkouts_tab()

with tab_events:
    render_events_tab()
