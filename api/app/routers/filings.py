"""Filings API: submit, list, detail, timeline."""
from __future__ import annotations

import json
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel
from psycopg.types.json import Jsonb

from app.auth import get_current_user, require_roles
from app.core.canonical import sha256_bytes
from app.core.messages import GENESIS_HASH, build_message, message_hash
from app.core.payloads import (
    extracted_payload,
    filing_submitted_payload,
    sealed_payload,
    validated_payload,
)
from app.db import connect, register_topic
from app.extraction.eval import CORE
from app.extraction.pdf import extract_values
from app.hedera import mirror
from app.hedera.client import HederaService
from app.ratios import compute_ratios, ratios_digest
from app.rebuild import sync_consensus
from app.report import build_report, preview_report, report_filename, report_sha256
from app.sealing import build_hfs_metadata, hfs_bytes
from app.validation import extraction_digest, validate
from app.verifier import verify_filing, verify_messages

router = APIRouter(prefix="/filings", tags=["filings"])

MAX_BYTES = 25 * 1024 * 1024


class FilingSummary(BaseModel):
    id: str
    issuer: str
    period: str
    sector: str
    status: str
    doc_sha256: str
    topic_id: str | None = None
    token_id: str | None = None
    serial: int | None = None
    created_at: str


class ValueOut(BaseModel):
    line_item: str
    label_raw: str
    value: float
    page: int
    snippet: str
    unit: str
    period: str
    confidence: float


class RatioOut(BaseModel):
    code: str
    name: str
    year: int
    value: float | None
    formula_version: str


class FilingDetail(FilingSummary):
    unit: str
    consolidation: str
    values: list[ValueOut]
    ratios: list[RatioOut]
    timeline_count: int


class EventOut(BaseModel):
    sequence: int
    event: str
    actor: str
    role: str
    ts: str
    hash: str
    prev_hash: str
    payload: dict


class FilingList(BaseModel):
    items: list[FilingSummary]
    total: int


def _summary(row, topic_id=None) -> FilingSummary:
    return FilingSummary(
        id=str(row[0]),
        issuer=row[1],
        period=row[2].isoformat(),
        sector=row[3],
        status=row[4],
        doc_sha256=row[5],
        topic_id=topic_id,
        token_id=row[6],
        serial=row[7],
        created_at=row[8].isoformat(),
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def submit_filing(
    file: UploadFile = File(...),
    issuer: str = Form(...),
    period: str = Form(...),
    sector: str = Form("industrial"),
    unit: str = Form("TND"),
    consolidation: str = Form("individuel"),
    pages: int = Form(0),
    user: dict = Depends(require_roles("issuer", "admin")),
) -> dict:
    raw = file.file.read()
    if not raw:
        raise HTTPException(422, "Empty file")
    if len(raw) > MAX_BYTES:
        raise HTTPException(422, "File too large (max 25 MB)")
    name = (file.filename or "").lower()
    if not name.endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(422, "Only PDF filings are accepted")
    if not issuer.strip():
        raise HTTPException(422, "issuer is required")
    try:
        period_date = date.fromisoformat(period)
    except ValueError:
        raise HTTPException(422, "period must be an ISO date (YYYY-MM-DD)") from None

    digest = sha256_bytes(raw)
    with connect() as conn:
        duplicate = conn.execute(
            "SELECT id FROM filings WHERE doc_sha256 = %s", (digest,)
        ).fetchone()
    if duplicate is not None:
        raise HTTPException(409, "This document has already been submitted")

    filing_id = str(uuid4())
    payload = filing_submitted_payload(
        issuer=issuer.strip(),
        period=period_date.isoformat(),
        doc_sha256=digest,
        mime=file.content_type or "application/pdf",
        pages=pages,
    )
    try:
        hedera = HederaService()
        topic_id = hedera.create_topic(f"veda:{issuer.strip()}:{period_date.isoformat()}")
        message = build_message(
            event="filing_submitted",
            filing_id=filing_id,
            actor=user["hedera_account_id"],
            role="issuer",
            sector=sector,
            payload=payload,
            prev_hash=GENESIS_HASH,
        )
        receipt = hedera.submit_message(topic_id, message)
    except Exception as exc:
        raise HTTPException(502, "Hedera submission failed") from exc

    with connect() as conn:
        conn.execute(
            "INSERT INTO filings (id, doc_sha256, issuer, period, sector, unit, "
            "consolidation, status, topic_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                filing_id,
                digest,
                issuer.strip(),
                period_date,
                sector,
                unit,
                consolidation,
                "submitted",
                topic_id,
            ),
        )
        conn.execute(
            "INSERT INTO events (id, filing_id, hcs_sequence, event, actor, role, "
            "payload, prev_hash, hash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                str(uuid4()),
                filing_id,
                receipt["sequence"],
                "filing_submitted",
                user["hedera_account_id"],
                "issuer",
                Jsonb(payload),
                GENESIS_HASH,
                message_hash(message),
            ),
        )
        register_topic(conn, filing_id, topic_id)

    return {"filing_id": filing_id, "status": "submitted"}


def _last_event_hash(conn, filing_id: str) -> str | None:
    row = conn.execute(
        "SELECT hash FROM events WHERE filing_id = %s "
        "ORDER BY hcs_sequence DESC LIMIT 1",
        (filing_id,),
    ).fetchone()
    return row[0] if row else None


def _prior_values(conn, issuer: str, year: int) -> dict[str, float]:
    rows = conn.execute(
        "SELECT v.line_item, v.value FROM values v "
        "JOIN filings f ON f.id = v.filing_id "
        "WHERE f.issuer = %s AND EXTRACT(YEAR FROM f.period) = %s "
        "ORDER BY f.created_at",
        (issuer, year - 1),
    ).fetchall()
    return {row[0]: float(row[1]) for row in rows}


def _filing_record(conn, filing_id: str) -> dict | None:
    row = conn.execute(
        "SELECT id, issuer, period, sector, unit, consolidation, status, "
        "doc_sha256, topic_id, token_id, serial FROM filings WHERE id = %s",
        (filing_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "id": str(row[0]),
        "issuer": row[1],
        "period": row[2],
        "sector": row[3],
        "unit": row[4],
        "consolidation": row[5],
        "status": row[6],
        "doc_sha256": row[7],
        "topic_id": row[8],
        "token_id": row[9],
        "serial": row[10],
    }


def _event_payload(conn, filing_id: str, event: str) -> dict | None:
    row = conn.execute(
        "SELECT payload FROM events WHERE filing_id = %s AND event = %s "
        "ORDER BY hcs_sequence DESC LIMIT 1",
        (filing_id, event),
    ).fetchone()
    return row[0] if row else None


def _filing_values(conn, filing_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT line_item, label_raw, value, page, confidence FROM values "
        "WHERE filing_id = %s ORDER BY line_item",
        (filing_id,),
    ).fetchall()
    return [
        {
            "line_item": row[0],
            "label_raw": row[1],
            "value": int(row[2]),
            "page": row[3],
            "confidence": float(row[4]),
        }
        for row in rows
    ]


def _filing_ratios(conn, filing_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT code, name, year, value, formula_version FROM ratios "
        "WHERE filing_id = %s ORDER BY code",
        (filing_id,),
    ).fetchall()
    return [
        {
            "code": row[0],
            "name": row[1],
            "year": row[2],
            "value": None if row[3] is None else float(row[3]),
            "formula_version": row[4],
        }
        for row in rows
    ]


def _nft_token(conn, hedera: HederaService) -> str:
    row = conn.execute(
        "SELECT value FROM _meta WHERE key = 'nft_token'"
    ).fetchone()
    if row:
        return row[0]
    token_id = hedera.create_nft_collection()
    conn.execute(
        "INSERT INTO _meta (key, value) VALUES ('nft_token', %s) "
        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
        (token_id,),
    )
    return token_id


@router.post("/{filing_id}/extract")
def extract_filing(
    filing_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(require_roles("issuer", "admin")),
) -> dict:
    raw = file.file.read()
    if not raw:
        raise HTTPException(422, "Empty file")
    if len(raw) > MAX_BYTES:
        raise HTTPException(422, "File too large (max 25 MB)")
    name = (file.filename or "").lower()
    if not name.endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(422, "Only PDF filings are accepted")

    with connect() as conn:
        row = conn.execute(
            "SELECT doc_sha256, issuer, period, sector, unit, status, topic_id "
            "FROM filings WHERE id = %s",
            (filing_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(404, "Filing not found")
        doc_sha256, issuer, period, sector, unit, current_status, topic_id = row
        if current_status != "submitted":
            raise HTTPException(409, "Filing already extracted")
        if not topic_id:
            raise HTTPException(409, "Filing is not anchored on Hedera")
        prev_hash = _last_event_hash(conn, filing_id)
        if prev_hash is None:
            raise HTTPException(409, "Filing has no submission event")
        prior = _prior_values(conn, issuer, period.year)

    if sha256_bytes(raw) != doc_sha256:
        raise HTTPException(422, "Document hash does not match the filing")

    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "filing.pdf"
            path.write_bytes(raw)
            items = extract_values(path, period.year)
    except Exception as exc:
        raise HTTPException(422, "PDF extraction failed") from exc

    values = {item["line_item"]: item["value"] for item in items}
    missing = [key for key in CORE if key not in values]
    if missing:
        raise HTTPException(422, "Extraction incomplete: " + ", ".join(missing))

    ratio_rows = compute_ratios(values, period.year, prior)
    result = validate(values)
    extraction_sha = extraction_digest(items)
    ratios_sha = ratios_digest(ratio_rows)
    grounded = sum(
        1 for item in items if item.get("bbox") and item.get("snippet")
    )
    extracted = extracted_payload(
        extraction_sha256=extraction_sha,
        model="deterministic:pymupdf",
        line_count=len(items),
        grounded_verified=grounded,
        grounded_total=len(items),
    )
    validated = validated_payload(
        extraction_sha256=extraction_sha,
        ratios_sha256=ratios_sha,
        verdict=result["verdict"],
        checks=result["checks"],
    )

    message_extracted = build_message(
        event="extracted",
        filing_id=filing_id,
        actor=user["hedera_account_id"],
        role="agent",
        sector=sector,
        payload=extracted,
        prev_hash=prev_hash,
    )
    message_validated = build_message(
        event="validated",
        filing_id=filing_id,
        actor=user["hedera_account_id"],
        role="agent",
        sector=sector,
        payload=validated,
        prev_hash=message_hash(message_extracted),
    )
    try:
        hedera = HederaService()
        receipt_extracted = hedera.submit_message(topic_id, message_extracted)
        receipt_validated = hedera.submit_message(topic_id, message_validated)
    except Exception as exc:
        raise HTTPException(502, "Hedera submission failed") from exc

    new_status = "validated" if result["verdict"] == "pass" else "failed"
    with connect() as conn:
        conn.execute("DELETE FROM values WHERE filing_id = %s", (filing_id,))
        conn.execute("DELETE FROM ratios WHERE filing_id = %s", (filing_id,))
        for item in items:
            conn.execute(
                "INSERT INTO values (id, filing_id, line_item, label_raw, value, "
                "page, snippet, unit, period, confidence, bbox) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    str(uuid4()),
                    filing_id,
                    item["line_item"],
                    item["label_raw"],
                    item["value"],
                    item["page"],
                    item["snippet"],
                    unit,
                    item["period"],
                    item["confidence"],
                    Jsonb(item["bbox"]),
                ),
            )
        for ratio in ratio_rows:
            conn.execute(
                "INSERT INTO ratios (id, filing_id, code, name, year, value, "
                "formula_version) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    str(uuid4()),
                    filing_id,
                    ratio["code"],
                    ratio["name"],
                    ratio["year"],
                    ratio["value"],
                    ratio["formula_version"],
                ),
            )
        conn.execute(
            "UPDATE filings SET status = %s WHERE id = %s",
            (new_status, filing_id),
        )
        for message, receipt in (
            (message_extracted, receipt_extracted),
            (message_validated, receipt_validated),
        ):
            conn.execute(
                "INSERT INTO events (id, filing_id, hcs_sequence, event, actor, "
                "role, payload, prev_hash, hash) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    message["event_id"],
                    filing_id,
                    receipt["sequence"],
                    message["event"],
                    message["actor"],
                    message["role"],
                    Jsonb(message["payload"]),
                    message["prev_hash"],
                    message_hash(message),
                ),
            )

    return {
        "filing_id": filing_id,
        "status": new_status,
        "verdict": result["verdict"],
        "line_count": len(items),
        "extraction_sha256": extraction_sha,
        "ratios_sha256": ratios_sha,
        "checks": result["checks"],
    }


@router.post("/{filing_id}/seal")
def seal_filing(
    filing_id: str,
    user: dict = Depends(require_roles("issuer", "admin")),
) -> dict:
    with connect() as conn:
        filing = _filing_record(conn, filing_id)
        if filing is None:
            raise HTTPException(404, "Filing not found")
        if filing["status"] != "validated":
            raise HTTPException(409, "Filing must be validated before sealing")
        if not filing["topic_id"]:
            raise HTTPException(409, "Filing is not anchored on Hedera")
        duplicate = conn.execute(
            "SELECT id FROM filings WHERE issuer = %s AND period = %s "
            "AND status = 'sealed' AND id <> %s",
            (filing["issuer"], filing["period"], filing_id),
        ).fetchone()
        if duplicate is not None:
            raise HTTPException(
                409, "A credential already exists for this issuer and period"
            )
        values = _filing_values(conn, filing_id)
        ratios = _filing_ratios(conn, filing_id)
        extracted = _event_payload(conn, filing_id, "extracted")
        validated = _event_payload(conn, filing_id, "validated")
        last = conn.execute(
            "SELECT hcs_sequence, hash FROM events WHERE filing_id = %s "
            "ORDER BY hcs_sequence DESC LIMIT 1",
            (filing_id,),
        ).fetchone()

    if not values or not ratios:
        raise HTTPException(409, "Filing has no extracted values")
    if not extracted or not validated:
        raise HTTPException(409, "Filing has no validated event")
    if validated.get("verdict") != "pass":
        raise HTTPException(409, "Only a passing validation can be sealed")
    checks = validated.get("checks", [])
    if not checks or not all(item["status"] == "pass" for item in checks):
        raise HTTPException(409, "Coherence checks did not pass")
    if last is None:
        raise HTTPException(409, "Filing has no events")

    report = build_report(
        filing=filing,
        values=values,
        ratios=ratios,
        checks=checks,
        extraction_sha256=extracted["extraction_sha256"],
        ratios_sha256=validated["ratios_sha256"],
    )
    report_hash = report_sha256(report)
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    predicted_sequence = int(last[0]) + 1
    metadata = build_hfs_metadata(
        issuer=filing["issuer"],
        period=filing["period"].isoformat(),
        sector=filing["sector"],
        unit=filing["unit"],
        doc_sha256=filing["doc_sha256"],
        extraction_sha256=extracted["extraction_sha256"],
        ratios_sha256=validated["ratios_sha256"],
        report_sha256=report_hash,
        verdict=validated["verdict"],
        topic_id=filing["topic_id"],
        sequence_range=[1, predicted_sequence],
        model=extracted.get("model", "deterministic:pymupdf"),
        created_at=created_at,
        values=values,
    )
    try:
        contents = hfs_bytes(metadata)
    except ValueError as exc:
        raise HTTPException(500, str(exc)) from exc

    try:
        hedera = HederaService()
        with connect() as conn:
            token_id = _nft_token(conn, hedera)
        metadata_file_id = hedera.create_file(contents)
        serial = hedera.mint_nft(token_id, metadata_file_id.encode("utf-8"))
        payload = sealed_payload(
            report_sha256=report_hash,
            token_id=token_id,
            serial=serial,
            metadata_file_id=metadata_file_id,
        )
        message = build_message(
            event="sealed",
            filing_id=filing_id,
            actor=user["hedera_account_id"],
            role="agent",
            sector=filing["sector"],
            payload=payload,
            prev_hash=last[1],
            ts=created_at,
        )
        receipt = hedera.submit_message(filing["topic_id"], message)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "Hedera seal failed") from exc

    with connect() as conn:
        conn.execute(
            "INSERT INTO events (id, filing_id, hcs_sequence, event, actor, role, "
            "payload, prev_hash, hash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                message["event_id"],
                filing_id,
                receipt["sequence"],
                message["event"],
                message["actor"],
                message["role"],
                Jsonb(message["payload"]),
                message["prev_hash"],
                message_hash(message),
            ),
        )
        conn.execute(
            "UPDATE filings SET status = 'sealed', token_id = %s, serial = %s "
            "WHERE id = %s",
            (token_id, serial, filing_id),
        )

    return {
        "filing_id": filing_id,
        "status": "sealed",
        "token_id": token_id,
        "serial": serial,
        "metadata_file_id": metadata_file_id,
        "report_sha256": report_hash,
        "hcs_sequence": receipt["sequence"],
        "hcs_sequence_range": [1, receipt["sequence"]],
    }


@router.get("", response_model=FilingList)
def list_filings(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    issuer: str | None = None,
    user: dict = Depends(get_current_user),
) -> FilingList:
    where = "WHERE issuer = %s" if issuer else ""
    params: tuple = (issuer,) if issuer else ()
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, issuer, period, sector, status, doc_sha256, token_id, serial, created_at, topic_id "
            f"FROM filings {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (*params, limit, offset),
        ).fetchall()
        total = conn.execute(
            f"SELECT count(*) FROM filings {where}", params
        ).fetchone()[0]
    return FilingList(
        items=[_summary(row, row[9]) for row in rows], total=total
    )


@router.get("/{filing_id}", response_model=FilingDetail)
def get_filing(
    filing_id: str, user: dict = Depends(get_current_user)
) -> FilingDetail:
    with connect() as conn:
        row = conn.execute(
            "SELECT id, issuer, period, sector, status, doc_sha256, token_id, serial, "
            "created_at, unit, consolidation, topic_id FROM filings WHERE id = %s",
            (filing_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(404, "Filing not found")
        value_rows = conn.execute(
            "SELECT line_item, label_raw, value, page, snippet, unit, period, confidence "
            "FROM values WHERE filing_id = %s ORDER BY line_item",
            (filing_id,),
        ).fetchall()
        ratio_rows = conn.execute(
            "SELECT code, name, year, value, formula_version FROM ratios "
            "WHERE filing_id = %s ORDER BY code, year",
            (filing_id,),
        ).fetchall()
        event_count = conn.execute(
            "SELECT count(*) FROM events WHERE filing_id = %s", (filing_id,)
        ).fetchone()[0]
    summary = _summary(row, row[11])
    return FilingDetail(
        **summary.model_dump(),
        unit=row[9],
        consolidation=row[10],
        values=[
            ValueOut(
                line_item=r[0],
                label_raw=r[1],
                value=float(r[2]),
                page=r[3],
                snippet=r[4],
                unit=r[5],
                period=r[6],
                confidence=float(r[7]),
            )
            for r in value_rows
        ],
        ratios=[
            RatioOut(
                code=r[0],
                name=r[1],
                year=r[2],
                value=float(r[3]) if r[3] is not None else None,
                formula_version=r[4],
            )
            for r in ratio_rows
        ],
        timeline_count=event_count,
    )


@router.get("/{filing_id}/timeline", response_model=dict)
def get_timeline(
    filing_id: str, user: dict = Depends(get_current_user)
) -> dict:
    with connect() as conn:
        filing = conn.execute(
            "SELECT created_at FROM filings WHERE id = %s", (filing_id,)
        ).fetchone()
        if filing is None:
            raise HTTPException(404, "Filing not found")
        rows = conn.execute(
            "SELECT hcs_sequence, event, actor, role, payload, prev_hash, hash, consensus_ts "
            "FROM events WHERE filing_id = %s ORDER BY hcs_sequence",
            (filing_id,),
        ).fetchall()
    fallback = filing[0].isoformat()
    return {
        "events": [
            EventOut(
                sequence=r[0],
                event=r[1],
                actor=r[2],
                role=r[3],
                ts=r[7].isoformat() if r[7] else fallback,
                hash=r[6],
                prev_hash=r[5],
                payload=r[4],
            ).model_dump()
            for r in rows
        ]
    }


def _report_bundle(filing_id: str) -> tuple[dict, bytes]:
    with connect() as conn:
        filing = _filing_record(conn, filing_id)
        if filing is None:
            raise HTTPException(404, "Filing not found")
        values = _filing_values(conn, filing_id)
        ratios = _filing_ratios(conn, filing_id)
        extracted = _event_payload(conn, filing_id, "extracted")
        validated = _event_payload(conn, filing_id, "validated")
    if not values or not ratios or not extracted or not validated:
        raise HTTPException(409, "Filing has not been extracted and validated")
    data = build_report(
        filing=filing,
        values=values,
        ratios=ratios,
        checks=validated.get("checks", []),
        extraction_sha256=extracted["extraction_sha256"],
        ratios_sha256=validated["ratios_sha256"],
    )
    return filing, data


@router.get("/{filing_id}/report.preview")
def preview_report_route(
    filing_id: str, user: dict = Depends(get_current_user)
) -> dict:
    filing, data = _report_bundle(filing_id)
    return {
        "filename": report_filename(filing["issuer"], filing["period"].year),
        "sha256": report_sha256(data),
        "size": len(data),
        "sheets": preview_report(data),
    }


@router.get("/{filing_id}/report.xlsx")
def download_report(
    filing_id: str, user: dict = Depends(get_current_user)
) -> Response:
    filing, data = _report_bundle(filing_id)
    filename = report_filename(filing["issuer"], filing["period"].year)
    return Response(
        content=data,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report-SHA256": report_sha256(data),
        },
    )


@router.post("/{filing_id}/verify")
def verify_filing_route(
    filing_id: str,
    user: dict = Depends(require_roles("broker", "verifier", "admin")),
) -> dict:
    with connect() as conn:
        row = conn.execute(
            "SELECT topic_id, token_id, serial FROM filings WHERE id = %s",
            (filing_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(404, "Filing not found")
    topic_id, token_id, serial = row
    if not topic_id:
        raise HTTPException(409, "Filing is not anchored on Hedera")

    try:
        if token_id and serial is not None:
            report = verify_filing(topic_id, token_id, int(serial))
        else:
            messages = mirror.topic_messages(topic_id, attempts=3, delay=1.0)
            report = {
                "verified": False,
                "checks": verify_messages(messages),
                "evidence": {
                    "topic_id": topic_id,
                    "message_count": len(messages),
                },
            }
        sync_consensus(filing_id, mirror.topic_messages(topic_id, attempts=3, delay=1.0))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, "Hedera verification failed") from exc
    return report


@router.get("/{filing_id}/credential")
def get_credential(
    filing_id: str, user: dict = Depends(get_current_user)
) -> dict:
    with connect() as conn:
        row = conn.execute(
            "SELECT token_id, serial FROM filings WHERE id = %s", (filing_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(404, "Filing not found")
    token_id, serial = row
    if not token_id or serial is None:
        raise HTTPException(404, "No credential yet (filing not sealed)")

    try:
        metadata_file_id = mirror.nft_metadata_bytes(token_id, int(serial)).decode("utf-8")
        metadata = json.loads(
            HederaService().read_file(metadata_file_id).decode("utf-8")
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, "Hedera credential read failed") from exc
    return {
        "token_id": token_id,
        "serial": int(serial),
        "metadata_file_id": metadata_file_id,
        "metadata": metadata,
    }
