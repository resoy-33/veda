"""Signed French number parsing from PDF tokens."""
from __future__ import annotations

from app.extraction.numbers import is_numeric, parse_number


def test_plain_groups():
    assert parse_number(["1", "234", "567"]) == 1234567


def test_parentheses_negative():
    assert parse_number(["(1", "234)"]) == -1234


def test_angle_negative():
    assert parse_number(["<1", "234>"]) == -1234


def test_split_brackets():
    assert parse_number(["<", "55", "433", "568>"]) == -55433568


def test_dash_is_zero():
    assert parse_number(["-"]) == 0


def test_decimal_comma():
    assert parse_number(["12,5"]) == 12.5


def test_empty():
    assert parse_number([]) is None


def test_punctuation_tokens_are_numeric():
    for token in ("(", ")", "<", ">", "-"):
        assert is_numeric(token)


def test_labels_are_not_numeric():
    assert not is_numeric("III.9")
    assert not is_numeric("Revenus")
