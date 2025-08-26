# utils/db.py
from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional

import streamlit as st
from supabase import Client, create_client


# -----------------------------
# Internal helpers
# -----------------------------
def _get_secret(name: str) -> Optional[str]:
    """
    Resolve a secret from environment (Replit Secrets) first,
    then fall back to Streamlit secrets (secrets.toml) if available.
    """
    val = os.getenv(name)
    if val:
        return val
    try:
        # st.secrets behaves like a Mapping when secrets.toml exists
        if hasattr(st, "secrets") and name in st.secrets:
            return st.secrets[name]  # type: ignore[index]
    except Exception:
        pass
    return None


def _require_creds() -> tuple[str, str]:
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError(
            "Supabase credentials missing. Set SUPABASE_URL and SUPABASE_ANON_KEY "
            "in Replit Secrets (recommended) or in .streamlit/secrets.toml."
        )
    return url, key


# -----------------------------
# Client factory (cached)
# -----------------------------
@st.cache_resource(show_spinner=False)
def get_supabase() -> Client:
    """
    Returns a cached Supabase client. Safe to call many times.
    """
    url, key = _require_creds()
    return create_client(url, key)


# -----------------------------
# Convenience data helpers
# -----------------------------
@st.cache_data(ttl=60, show_spinner=False)
def fetch_table(
    table_name: str,
    *,
    select: str = "*",
    limit: Optional[int] = None,
    order_by: Optional[str] = None,
    desc: bool = False,
) -> List[Dict[str, Any]]:
    """
    Fetch all rows from a table (optionally limited and ordered).
    Cached for 60s to avoid hammering the DB on every rerun.
    """
    sb = get_supabase()
    q = sb.table(table_name).select(select)
    if order_by:
        q = q.order(order_by, desc=desc)
    if limit:
        q = q.limit(limit)
    resp = q.execute()
    return resp.data or []


@st.cache_data(ttl=60, show_spinner=False)
def fetch_table_where(
    table_name: str,
    *,
    select: str = "*",
    eq: Optional[Dict[str, Any]] = None,
    gte: Optional[Dict[str, Any]] = None,
    lte: Optional[Dict[str, Any]] = None,
    ilike: Optional[Dict[str, str]] = None,
    order_by: Optional[str] = None,
    desc: bool = False,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Flexible WHERE helper:
      - eq={"plate_number": "AB-12345"}
      - gte={"trip_date": "2025-08-01"}
      - lte={"trip_date": "2025-08-31"}
      - ilike={"make": "%tesla%"}
    """
    sb = get_supabase()
    q = sb.table(table_name).select(select)

    for d, fn in [
        (eq, "eq"),
        (gte, "gte"),
        (lte, "lte"),
        (ilike, "ilike"),
    ]:
        if d:
            for k, v in d.items():
                q = getattr(q, fn)(k, v)

    if order_by:
        q = q.order(order_by, desc=desc)
    if limit:
        q = q.limit(limit)

    resp = q.execute()
    return resp.data or []


def insert_rows(table_name: str, rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Insert one or many rows. Returns inserted rows (if enabled) or empty list.
    """
    rows = list(rows)
    if not rows:
        return []
    sb = get_supabase()
    resp = sb.table(table_name).insert(rows).execute()
    return resp.data or []


def upsert_rows(table_name: str, rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Upsert one or many rows (requires a unique constraint or primary key on the table).
    """
    rows = list(rows)
    if not rows:
        return []
    sb = get_supabase()
    resp = sb.table(table_name).upsert(rows).execute()
    return resp.data or []


def delete_rows_by_ids(
    table_name: str,
    id_column: str,
    ids: Iterable[Any],
) -> int:
    """
    Delete rows by a list of IDs from `id_column`.
    Returns number of deleted rows (best-effort based on response).
    """
    ids = list(ids)
    if not ids:
        return 0
    sb = get_supabase()
    # Supabase .in_ uses 'in' but Python reserves the keyword, so it's 'in_'
    resp = sb.table(table_name).delete().in_(id_column, ids).execute()
    data = resp.data or []
    return len(data)


# -----------------------------
# Streamlit-friendly utilities
# -----------------------------
def to_df(records: List[Dict[str, Any]], *, rename: Optional[Dict[str, str]] = None):
    """
    Convert a list of dicts to a pandas DataFrame and optionally rename columns.
    """
    import pandas as pd

    df = pd.DataFrame.from_records(records)
    if rename:
        df = df.rename(columns=rename)
    return df


def connection_healthcheck(
    probe_table: str = "ev.trucks",
    *,
    silent: bool = False,
) -> bool:
    """
    Light-touch health check: try a tiny select on a known table.
    Returns True if OK, False otherwise. Emits Streamlit messages unless silent=True.
    """
    try:
        _ = fetch_table(probe_table, select="*", limit=1)
        if not silent:
            st.success("Connected to Supabase ✅")
        return True
    except Exception as e:
        if not silent:
            st.error(f"Supabase connection failed: {e}")
        return False


# -----------------------------
# App-specific shortcuts
# -----------------------------
def load_ev_trucks_df() -> "pd.DataFrame":
    """
    Load trucks master data from 'ev.trucks' into a DataFrame.
    """
    records = fetch_table("ev.trucks", order_by="plate")
    return to_df(records)


def load_ev_trips_df() -> "pd.DataFrame":
    """
    Load trips from 'ev.trips' into a DataFrame.
    Normalizes a few common column-name variations → 'plate_number'.
    """
    records = fetch_table("ev.trips", order_by="trip_date")
    df = to_df(records)

    # Normalize plate column for downstream code
    if "plate_number" not in df.columns:
        for alt in ("plate", "truck_plate", "plate_no"):
            if alt in df.columns:
                df = df.rename(columns={alt: "plate_number"})
                break
    return df
