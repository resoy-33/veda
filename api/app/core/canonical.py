"""Canonical serialization and hashing (the basis of every proof)."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal


def _default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def canonical_json(value) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8 friendly."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_default,
    )


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
