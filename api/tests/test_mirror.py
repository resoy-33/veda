"""Mirror Node chunk reassembly (HCS messages above 1024 bytes)."""
from __future__ import annotations

import base64
import json

from app.hedera.mirror import _reassemble


def _item(sequence: int, payload: bytes, chunk: dict | None = None) -> dict:
    return {
        "sequence_number": sequence,
        "consensus_timestamp": f"17610000{sequence}.000000000",
        "message": base64.b64encode(payload).decode("ascii"),
        "chunk_info": chunk,
    }


def test_single_messages_are_decoded():
    message = {"event": "filing_submitted"}
    items = [_item(1, json.dumps(message).encode("utf-8"))]
    result = _reassemble(items)
    assert len(result) == 1
    assert result[0]["sequence_number"] == 1
    assert result[0]["message"] == message


def test_chunks_are_joined_in_order():
    message = {"event": "validated", "payload": {"checks": ["a" * 300, "b" * 300]}}
    raw = json.dumps(message).encode("utf-8")
    first, second = raw[:400], raw[400:]
    info = {"initial_transaction_id": "0.0.1@1761000000.000000000", "total": 2}
    items = [
        _item(3, first, {**info, "number": 1}),
        _item(4, second, {**info, "number": 2}),
        _item(5, json.dumps({"event": "sealed"}).encode("utf-8")),
    ]
    result = _reassemble(items)
    assert len(result) == 2
    assert result[0]["sequence_number"] == 3
    assert result[0]["message"] == message
    assert result[1]["message"] == {"event": "sealed"}


def test_incomplete_chunks_are_skipped():
    info = {"initial_transaction_id": "0.0.1@1761000000.000000000", "total": 2}
    items = [_item(3, b'{"event":', {**info, "number": 1})]
    assert _reassemble(items) == []
