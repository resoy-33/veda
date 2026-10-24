"""Seed the LILAS 2021-2024 filings through the public API."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import pymupdf

API = os.environ.get("VEDA_API", "http://127.0.0.1:8000/api/v1")
ISSUER = os.environ.get("VEDA_ISSUER", "SAH")
EMAIL = os.environ.get("VEDA_ISSUER_EMAIL", "issuer@lilas.tn")
PASSWORD = os.environ.get("VEDA_ISSUER_PASSWORD", "demo1234")
YEARS = (2021, 2022, 2023, 2024)
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "lilas"


def fail(message: str, response: httpx.Response | None = None) -> None:
    print(f"ERROR: {message}")
    if response is not None:
        print(f"{response.status_code}: {response.text}")
    raise SystemExit(1)


def login(client: httpx.Client) -> dict[str, str]:
    response = client.post(
        "/auth/login", json={"email": EMAIL, "password": PASSWORD}
    )
    if response.status_code != 200:
        fail("login failed", response)
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def sealed_years(client: httpx.Client, headers: dict[str, str]) -> set[int]:
    response = client.get("/filings", params={"limit": 200}, headers=headers)
    if response.status_code != 200:
        fail("cannot list filings", response)
    return {
        int(item["period"][:4])
        for item in response.json()["items"]
        if item["issuer"] == ISSUER and item["status"] == "sealed"
    }


def seed_year(
    client: httpx.Client, headers: dict[str, str], year: int
) -> dict:
    path = DATA / f"LILAS {year}.pdf"
    if not path.exists():
        fail(f"missing source PDF: {path}")
    pages = pymupdf.open(path).page_count

    with path.open("rb") as handle:
        response = client.post(
            "/filings",
            headers=headers,
            data={
                "issuer": ISSUER,
                "period": f"{year}-12-31",
                "sector": "industrial",
                "unit": "TND",
                "consolidation": "individuel",
                "pages": str(pages),
            },
            files={"file": (path.name, handle, "application/pdf")},
        )
    if response.status_code != 202:
        fail(f"submission failed for {year}", response)
    filing_id = response.json()["filing_id"]
    print(f"{year}: submitted {filing_id}")

    with path.open("rb") as handle:
        response = client.post(
            f"/filings/{filing_id}/extract",
            headers=headers,
            files={"file": (path.name, handle, "application/pdf")},
        )
    if response.status_code != 200:
        fail(f"extraction failed for {year}", response)
    extracted = response.json()
    print(
        f"{year}: extracted {extracted['line_count']} values, "
        f"verdict={extracted['verdict']}"
    )

    response = client.post(f"/filings/{filing_id}/seal", headers=headers)
    if response.status_code != 200:
        fail(f"sealing failed for {year}", response)
    sealed = response.json()
    print(
        f"{year}: sealed serial={sealed['serial']} "
        f"topic_sequence={sealed['hcs_sequence']}"
    )
    return sealed


def main() -> int:
    with httpx.Client(base_url=API, timeout=240) as client:
        headers = login(client)
        done = sealed_years(client, headers)
        for year in YEARS:
            if year in done:
                print(f"{year}: already sealed, skipping")
                continue
            seed_year(client, headers, year)

        response = client.get("/filings", params={"limit": 200}, headers=headers)
        items = [
            item
            for item in response.json()["items"]
            if item["issuer"] == ISSUER and int(item["period"][:4]) in YEARS
        ]
        for item in sorted(items, key=lambda row: row["period"]):
            print(
                f"{item['period'][:4]}: {item['status']} "
                f"token={item['token_id']} serial={item['serial']}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
