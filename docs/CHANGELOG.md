# Changelog

## 1.4 — 2026-10-22

- Added the filing registry (`/depots`): role-aware hero and actions, KPI cards,
  five-year revenue chart, latest proof panel and filing rows.
- Added the filing dossier (`/depots/:id`): summary, 45 extracted values,
  grouped ratios, HCS timeline, NFT credential, 12-check verification and
  authenticated Excel download.
- Added the deposit wizard (`/depots/nouveau`): submit, extract, seal.
- Added the verifier workspace (`/verification`): sealed-filing queue with
  per-filing verification results, restricted to analyst/auditor/admin.
- Added the admin operations screen (`/operations`): service and cache health,
  chain inventory, and cache rebuild from Hedera.
- `FilingSummary` now exposes nullable `topic_id` in list and detail responses.
- Fixed a session refresh race by setting the access token in a layout effect.

## 1.3 — 2026-10-22

- Added `display_name` to users and `UserOut`; seeded French demo names.
- Added `PATCH /auth/me` (display name) and `POST /auth/change-password`
  (PBKDF2-SHA256, current password required).
- Added the React interface: login with one-click demo accounts, role-aware
  shell, deposits overview, account page, and light/dark/system theme.
- API version `0.4.0`.

## 1.2 — 2026-10-21

- Added `POST /filings/{id}/seal` (issuer/admin): deterministic Excel report,
  HFS metadata with compact extracted values, one NFT serial per
  `(issuer, period)`, and the `sealed` event.
- HFS properties now include `report_sha256` and `values` (≤ 4096 bytes).
- `GET /filings/{id}/report.xlsx` returns the same deterministic bytes that
  were anchored at seal time.
- Cache rebuild rehydrates sealed values/ratios from the HFS file and recomputes
  ratios, so `POST /system/rebuild` no longer depends on local-only data for
  sealed filings.
- Added `report_hash_match` to the verifier.
- Mirror reader reassembles HCS chunked messages (`chunk_info`) so the hash
  chain survives messages above 1024 bytes.
- The Excel report is byte-deterministic (fixed core properties and zip
  timestamps); the download hash equals the anchored `report_sha256`.
- Validation details are compact so a passing `validated` event fits in one
  1024-byte HCS message.

## 1.1 — 2026-10-21

- Added `POST /filings/{id}/extract` (issuer/admin): re-uploads the PDF,
  verifies `doc_sha256`, runs the deterministic extractor, writes `extracted`
  and `validated` events, and returns the verdict + checks.
- `extracted.model` is now `deterministic:pymupdf` (no model produces figures).
- Added `variation_stocks` to the line-item registry (section 7).
- Ratio engine (`section 8`) and the seven coherence checks are implemented
  with tolerance `max(1 dinar, 0.01 %)`.

## 1.0 — frozen

- Initial HCS envelope, NFT/HFS schema, verification algorithm, API, database,
  and French line-item registry.
