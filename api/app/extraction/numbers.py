"""French number parsing from PDF word tokens."""
from __future__ import annotations

import re

NUMERIC_TOKEN = re.compile(r"^[<>()\-]?\d[\d.,]*[<>()]?$")


PUNCTUATION = {"-", "—", "<", ">", "(", ")"}


def is_numeric(token: str) -> bool:
    return token in PUNCTUATION or bool(NUMERIC_TOKEN.match(token))


def parse_number(tokens: list[str]) -> int | float | None:
    text = "".join(tokens).replace("\u00a0", "").replace(" ", "")
    if not text:
        return None
    if text in {"-", "—"}:
        return 0
    negative = False
    if text[0] in "(<" and text[-1] in ")>":
        negative = True
        text = text[1:-1]
    elif text[0] in "(<":
        negative = True
        text = text[1:]
    if text.startswith("-"):
        negative = True
        text = text[1:]
    text = text.rstrip(")>")
    if not re.fullmatch(r"\d+(?:[.,]\d+)?", text):
        return None
    text = text.replace(",", ".")
    value: int | float = float(text) if "." in text else int(text)
    return -value if negative else value
