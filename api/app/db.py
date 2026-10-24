"""Postgres access. The database is a cache, rebuildable from the chain."""
from __future__ import annotations

import json
import os
from contextlib import contextmanager

import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL", "")


@contextmanager
def connect():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL missing")
    with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
        yield conn


def check_db() -> str:
    if not DATABASE_URL:
        return "not_configured"
    try:
        with connect() as conn:
            conn.execute("SELECT 1").fetchone()
        return "ok"
    except Exception:
        return "error"

def register_topic(conn, filing_id: str, topic_id: str) -> None:
    row = conn.execute("SELECT value FROM _meta WHERE key = 'topics'").fetchone()
    known = json.loads(row[0]) if row else {}
    known[str(filing_id)] = topic_id
    conn.execute(
        "INSERT INTO _meta (key, value) VALUES ('topics', %s) "
        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
        (json.dumps(known),),
    )