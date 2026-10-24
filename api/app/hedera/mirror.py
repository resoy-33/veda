"""Hedera reader: Mirror Node REST (trustless path)."""
from __future__ import annotations

import base64
import json
import time
import urllib.request

from ..config import settings


def _get(path: str, attempts: int = 12, delay: float = 1.5):
    base = settings.mirror_url.rstrip("/")
    url = path if path.startswith("http") else f"{base}{path}"
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - retry on indexing lag
            last_error = exc
            time.sleep(delay)
    raise RuntimeError(f"mirror request failed: {path}: {last_error}")


def _reassemble(items: list[dict]) -> list[dict]:
    slots: list[dict] = []
    groups: dict[str, dict] = {}
    for item in items:
        info = item.get("chunk_info")
        if not info or int(info.get("total", 1)) <= 1:
            slots.append({"kind": "single", "item": item})
            continue
        key = str(info.get("initial_transaction_id") or item.get("transaction_id"))
        slot = groups.get(key)
        if slot is None:
            slot = {"kind": "chunk", "items": [], "total": int(info["total"])}
            groups[key] = slot
            slots.append(slot)
        slot["items"].append(item)

    messages: list[dict] = []
    for slot in slots:
        if slot["kind"] == "single":
            item = slot["item"]
            raw = base64.b64decode(item["message"]).decode("utf-8")
            messages.append(
                {
                    "consensus_timestamp": item.get("consensus_timestamp"),
                    "sequence_number": item.get("sequence_number"),
                    "message": json.loads(raw),
                }
            )
            continue
        if len(slot["items"]) != slot["total"]:
            continue
        chunks = sorted(
            slot["items"], key=lambda item: int(item["chunk_info"]["number"])
        )
        raw = b"".join(base64.b64decode(item["message"]) for item in chunks)
        messages.append(
            {
                "consensus_timestamp": chunks[-1].get("consensus_timestamp"),
                "sequence_number": chunks[0].get("sequence_number"),
                "message": json.loads(raw.decode("utf-8")),
            }
        )
    return messages


def _fetch_topic(topic_id: str) -> list[dict]:
    items: list[dict] = []
    path = f"/api/v1/topics/{topic_id}/messages?order=asc&limit=100"
    while path:
        data = _get(path)
        items.extend(data.get("messages", []))
        path = data.get("links", {}).get("next")
    return _reassemble(items)


def topic_messages(
    topic_id: str,
    expected_min: int | None = None,
    attempts: int = 20,
    delay: float = 1.5,
) -> list[dict]:
    """Read all messages; if expected_min is set, wait for mirror indexing."""
    messages: list[dict] = []
    for _ in range(attempts):
        messages = _fetch_topic(topic_id)
        if expected_min is None or len(messages) >= expected_min:
            return messages
        time.sleep(delay)
    return messages


def nft(token_id: str, serial: int) -> dict:
    data = _get(f"/api/v1/tokens/{token_id}/nfts/{serial}")
    if isinstance(data, dict) and "nfts" in data:
        items = data["nfts"]
        return items[0] if items else {}
    return data


def nft_metadata_bytes(token_id: str, serial: int) -> bytes:
    raw = nft(token_id, serial).get("metadata", "")
    return base64.b64decode(raw)
