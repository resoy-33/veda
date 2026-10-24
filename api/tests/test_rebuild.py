"""Cache rebuild helpers (offline): state derivation from chain events."""
from __future__ import annotations

from app.rebuild import derive_state


def _event(name: str, payload: dict | None = None) -> dict:
    return {"event": name, "payload": payload or {}}


def test_submitted_only():
    assert derive_state([_event("filing_submitted")]) == ("submitted", None, None)


def test_extracted_then_validated_pass():
    events = [
        _event("filing_submitted"),
        _event("extracted"),
        _event("validated", {"verdict": "pass"}),
    ]
    assert derive_state(events) == ("validated", None, None)


def test_validation_fail_marks_failed():
    events = [_event("filing_submitted"), _event("validated", {"verdict": "fail"})]
    assert derive_state(events) == ("failed", None, None)


def test_sealed_carries_credential():
    events = [
        _event("filing_submitted"),
        _event("extracted"),
        _event("validated", {"verdict": "pass"}),
        _event(
            "sealed",
            {"credential": {"token_id": "0.0.42", "serial": 7}},
        ),
    ]
    assert derive_state(events) == ("sealed", "0.0.42", 7)
