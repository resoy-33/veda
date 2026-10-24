"""Configuration from environment (.env locally, compose env in containers)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if not candidate.exists():
            continue
        for raw in candidate.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        return


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    operator_id: str = os.environ.get("HEDERA_OPERATOR_ID", "")
    operator_key: str = os.environ.get("HEDERA_OPERATOR_KEY", "")
    network: str = os.environ.get("HEDERA_NETWORK", "testnet")
    mirror_url: str = os.environ.get(
        "HEDERA_MIRROR_URL", "https://testnet.mirrornode.hedera.com"
    )

    def require_operator(self) -> tuple[str, str]:
        if not self.operator_id or not self.operator_key:
            raise RuntimeError("HEDERA_OPERATOR_ID / HEDERA_OPERATOR_KEY missing")
        return self.operator_id, self.operator_key


settings = Settings()
