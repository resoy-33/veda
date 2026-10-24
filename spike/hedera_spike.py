"""Day-1 Hedera spike: prove topic, message, mirror read, NFT, and HFS all work.

Run:  python spike/hedera_spike.py
Needs HEDERA_OPERATOR_ID and HEDERA_OPERATOR_KEY (testnet) in .env or the env.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from hiero_sdk_python import (
    AccountId,
    Client,
    FileCreateTransaction,
    PrivateKey,
    SupplyType,
    TokenCreateTransaction,
    TokenMintTransaction,
    TokenType,
    TopicCreateTransaction,
    TopicMessageSubmitTransaction,
)

ROOT = Path(__file__).resolve().parents[1]
MIRROR = os.environ.get("HEDERA_MIRROR_URL", "https://testnet.mirrornode.hedera.com")


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def mirror_get(path: str, ready=None, attempts: int = 12, delay: float = 1.5) -> dict:
    url = f"{MIRROR}{path}"
    last: dict = {}
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                last = json.loads(resp.read().decode())
            if ready is None or ready(last):
                return last
        except Exception as exc:  # noqa: BLE001 - retry on indexing lag / 404
            last = {"error": str(exc)}
        time.sleep(delay)
    return last


def main() -> int:
    load_dotenv(ROOT / ".env")
    operator_id = os.environ.get("HEDERA_OPERATOR_ID", "")
    operator_key = os.environ.get("HEDERA_OPERATOR_KEY", "")
    if not operator_id or not operator_key:
        print(
            "Missing HEDERA_OPERATOR_ID / HEDERA_OPERATOR_KEY.\n"
            "Copy .env.example to .env and fill in your testnet account.",
            file=sys.stderr,
        )
        return 2

    account_id = AccountId.from_string(operator_id)
    key = PrivateKey.from_string(operator_key)
    client = Client.for_testnet()
    client.set_operator(account_id, key)
    print(f"[ok] client ready for {account_id}")

    # 1. HCS topic
    topic = (
        TopicCreateTransaction()
        .set_memo("integrity-spike")
        .set_submit_key(key.public_key())
        .execute(client)
        .topic_id
    )
    print(f"[ok] topic {topic}")

    # 2. Submit a message
    payload = json.dumps({"event": "spike", "ts": int(time.time())})
    receipt = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic)
        .set_message(payload)
        .execute(client)
    )
    print(f"[ok] message submitted (topic sequence={receipt.topic_sequence_number})")

    # 3. Read it back from the mirror node (the trustless path)
    data = mirror_get(
        f"/api/v1/topics/{topic}/messages?limit=10&order=desc",
        ready=lambda d: bool(d.get("messages")),
    )
    messages = data.get("messages", [])
    decoded = [base64.b64decode(m["message"]).decode() for m in messages]
    print(f"[ok] mirror returned {len(messages)} message(s)")
    if payload not in decoded:
        print(f"[FAIL] submitted message not found via mirror: {decoded[:3]}", file=sys.stderr)
        return 1

    # 4. Metadata JSON on Hedera File Service (NFT metadata field is only 100 bytes)
    metadata = json.dumps(
        {
            "name": "Verified Filing Spike",
            "type": "application/json",
            "properties": {"doc_sha256": "0" * 64, "topic": str(topic)},
        }
    ).encode()
    file_id = (
        FileCreateTransaction()
        .set_contents(metadata)
        .set_keys([key.public_key()])
        .execute(client)
        .file_id
    )
    print(f"[ok] metadata file {file_id} ({len(metadata)} bytes)")

    # 5. NFT collection + one serial whose metadata points at the file
    token = (
        TokenCreateTransaction()
        .set_token_name("Verified Filing Credential")
        .set_token_symbol("VFC")
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(1000)
        .set_initial_supply(0)
        .set_decimals(0)
        .set_treasury_account_id(account_id)
        .set_supply_key(key.public_key())
        .execute(client)
        .token_id
    )
    print(f"[ok] token {token}")

    serials = (
        TokenMintTransaction()
        .set_token_id(token)
        .set_metadata([str(file_id).encode()])
        .execute(client)
        .serial_numbers
    )
    print(f"[ok] minted serial(s) {serials}")

    # 6. Confirm the NFT via the mirror node
    nft = mirror_get(
        f"/api/v1/tokens/{token}/nfts/{serials[0]}",
        ready=lambda d: "metadata" in d,
    )
    print(f"[ok] mirror nft metadata: {nft.get('metadata')}")

    result = {
        "operator": str(account_id),
        "topic_id": str(topic),
        "token_id": str(token),
        "serial": serials[0],
        "file_id": str(file_id),
        "mirror_url": MIRROR,
    }
    out = ROOT / "spike" / "spike_result.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[done] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
