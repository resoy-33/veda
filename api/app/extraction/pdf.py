"""PDF extraction: coordinates -> French line items (no model, deterministic)."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pymupdf

from .numbers import is_numeric, parse_number
from .registry import (
    canonical_label,
    is_section_header,
    map_label,
    normalize,
    note_to_key,
)

DATE_TOKEN = re.compile(r"^\d{2}[./]\d{2}[./](\d{4})$")
NOTE_TOKEN = re.compile(r"^[IVX]+\.\d+$")
ROW_TOLERANCE = 3
SOURCE_PRIORITY = {"note": 0, "label": 1, "net": 2}
NET_KEYS = {
    "ecarts_acquisition",
    "immobilisations_incorporelles",
    "immobilisations_corporelles",
    "autres_actifs_non_courants",
}
ACCUMULATE_KEYS = {"autres_gains_pertes"}
EDGE_MIN_COUNT = 4


def _rows(words: list[tuple], after_y: float) -> dict[int, list[tuple]]:
    rows: dict[int, list[tuple]] = {}
    for word in words:
        if word[1] <= after_y + 2:
            continue
        rows.setdefault(round(word[1] / ROW_TOLERANCE), []).append(word)
    return rows


def _is_amortization(label: str) -> bool:
    normalized = normalize(label)
    return normalized.startswith("moins") and any(
        fragment in normalized
        for fragment in ("amortissements", "provisions", "depreciations")
    )


def extract_values(path: str | Path, year: int) -> list[dict]:
    document = pymupdf.open(str(path))
    found: dict[str, dict] = {}

    for page_index in range(1, min(len(document), 7)):
        page = document[page_index]
        words = [tuple(word) for word in page.get_text("words")]
        date_tokens = [
            word
            for word in words
            if DATE_TOKEN.match(word[4])
            and word[1] < page.rect.height * 0.45
        ]
        headers = [
            word for word in date_tokens if int(word[4][-4:]) == year
        ]
        if not headers:
            continue
        current = min(headers, key=lambda word: word[0])
        prior_candidates = [
            word for word in date_tokens if word[0] > current[2] + 5
        ]
        prior = min(prior_candidates, key=lambda word: word[0]) if prior_candidates else None

        notes = [word for word in words if NOTE_TOKEN.match(word[4])]
        boundary = max(word[2] for word in notes) + 5 if notes else current[0] - 20

        edge_counts = Counter(
            round(word[2])
            for word in words
            if word[0] >= boundary - 2
            and is_numeric(word[4])
            and any(char.isdigit() for char in word[4])
            and not DATE_TOKEN.match(word[4])
            and current[1] + 2 < word[1] < page.rect.height * 0.92
        )
        ceiling = prior[0] - 5 if prior is not None else current[2] + 45
        candidates = [
            (count, edge)
            for edge, count in edge_counts.items()
            if count >= EDGE_MIN_COUNT and edge <= ceiling
        ]
        if candidates:
            best_count = max(count for count, _ in candidates)
            current_right = (
                max(edge for count, edge in candidates if count == best_count) + 2
            )
        else:
            current_right = current[2] + 4

        pending_label = ""
        pending_note = ""
        last_key: str | None = None
        after_amortization = False
        row_map = _rows(words, current[1])
        rows = [sorted(row_map[key], key=lambda word: word[0]) for key in sorted(row_map)]

        def _parts(row: list[tuple]) -> tuple[list[str], str, list[str]]:
            label_parts = [
                word[4]
                for word in row
                if word[2] < boundary
                and not is_numeric(word[4])
                and not NOTE_TOKEN.match(word[4])
            ]
            note = next(
                (word[4] for word in row if NOTE_TOKEN.match(word[4])), ""
            )
            tokens = [
                word[4]
                for word in row
                if word[0] >= boundary - 2
                and is_numeric(word[4])
                and word[2] <= current_right
            ]
            return label_parts, note, tokens

        index = 0
        while index < len(rows):
            row = rows[index]
            label_parts, note, current_tokens = _parts(row)
            value = parse_number(current_tokens) if current_tokens else None
            label_text = " ".join(label_parts)

            if value is None:
                if note:
                    pending_note = note
                if label_text:
                    if is_section_header(label_text):
                        pending_label = ""
                        pending_note = ""
                    else:
                        pending_label = (
                            f"{pending_label} {label_text}".strip()
                        )
                index += 1
                continue

            full_label = (
                f"{pending_label} {label_text}".strip()
                if label_text
                else pending_label
            )
            note_id = pending_note or note
            pending_label = ""
            pending_note = ""

            item_key, confidence = map_label(full_label, note_id)
            source = "label" if item_key else ""
            if (
                not item_key
                and after_amortization
                and last_key
                and not full_label
                and (
                    last_key in NET_KEYS
                    or canonical_label(last_key).endswith(("(nets)", "(nettes)"))
                )
            ):
                item_key, confidence, source = last_key, 0.8, "net"
            if not item_key and note_id:
                mapped = note_to_key(note_id)
                if mapped:
                    item_key, confidence, source = mapped, 0.95, "note"

            consumed_next = False
            if not item_key and index + 1 < len(rows):
                next_parts, next_note, next_tokens = _parts(rows[index + 1])
                next_label = " ".join(next_parts)
                if (
                    not next_tokens
                    and not next_note
                    and next_label
                    and not is_section_header(next_label)
                ):
                    combined = f"{full_label} {next_label}".strip()
                    combined_key, combined_confidence = map_label(combined, note_id)
                    if combined_key:
                        item_key = combined_key
                        confidence = combined_confidence
                        source = "label"
                        consumed_next = True

            if not item_key:
                after_amortization = _is_amortization(full_label)
                index += 2 if consumed_next else 1
                continue

            after_amortization = False
            last_key = item_key
            existing = found.get(item_key)
            if (
                existing is not None
                and item_key in ACCUMULATE_KEYS
                and source == "label"
            ):
                existing["value"] += value
                existing["snippet"] = (
                    f"{existing['snippet']} | " + " ".join(word[4] for word in row)
                )[:500]
            elif existing is None or (
                SOURCE_PRIORITY[source] > SOURCE_PRIORITY[existing["source"]]
            ):
                value_words = [
                    word
                    for word in row
                    if word[0] >= boundary - 2
                    and is_numeric(word[4])
                    and word[2] <= current_right
                ]
                found[item_key] = {
                    "line_item": item_key,
                    "label_raw": canonical_label(item_key),
                    "value": value,
                    "page": page_index + 1,
                    "snippet": " ".join(word[4] for word in row)[:500],
                    "unit": "TND",
                    "period": f"{year}-12-31",
                    "confidence": confidence,
                    "bbox": {
                        "x0": min(word[0] for word in value_words),
                        "top": min(word[1] for word in value_words),
                        "x1": max(word[2] for word in value_words),
                        "bottom": max(word[3] for word in value_words),
                    },
                    "source": source,
                }

            index += 2 if consumed_next else 1

    document.close()
    return list(found.values())
