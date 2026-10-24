CREATE TABLE IF NOT EXISTS _meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

INSERT INTO _meta (key, value)
VALUES ('schema_version', '0.3.0')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('issuer', 'broker', 'verifier', 'admin')),
  hedera_account_id TEXT NOT NULL,
  display_name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name TEXT;

CREATE TABLE IF NOT EXISTS filings (
  id UUID PRIMARY KEY,
  doc_sha256 TEXT UNIQUE NOT NULL,
  issuer TEXT NOT NULL,
  period DATE NOT NULL,
  sector TEXT NOT NULL,
  unit TEXT NOT NULL,
  consolidation TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('submitted', 'extracted', 'validated', 'sealed', 'failed')),
  topic_id TEXT,
  token_id TEXT,
  serial BIGINT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS values (
  id UUID PRIMARY KEY,
  filing_id UUID REFERENCES filings(id) ON DELETE CASCADE,
  line_item TEXT NOT NULL,
  label_raw TEXT NOT NULL,
  value NUMERIC(24, 0) NOT NULL,
  page INT NOT NULL,
  snippet TEXT NOT NULL,
  unit TEXT NOT NULL,
  period TEXT NOT NULL,
  confidence NUMERIC(4, 3) NOT NULL,
  bbox JSONB
);

CREATE TABLE IF NOT EXISTS ratios (
  id UUID PRIMARY KEY,
  filing_id UUID REFERENCES filings(id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  year INT NOT NULL,
  value NUMERIC(18, 6),
  formula_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id UUID PRIMARY KEY,
  filing_id UUID REFERENCES filings(id) ON DELETE CASCADE,
  hcs_sequence BIGINT NOT NULL,
  event TEXT NOT NULL,
  actor TEXT NOT NULL,
  role TEXT NOT NULL,
  payload JSONB NOT NULL,
  prev_hash TEXT NOT NULL,
  hash TEXT NOT NULL,
  consensus_ts TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_values_filing ON values (filing_id);
CREATE INDEX IF NOT EXISTS idx_ratios_filing ON ratios (filing_id);
CREATE INDEX IF NOT EXISTS idx_events_filing_seq ON events (filing_id, hcs_sequence);

INSERT INTO users (id, email, password_hash, role, hedera_account_id, display_name)
VALUES
  ('11111111-1111-4111-8111-111111111111', 'issuer@lilas.tn',
   'pbkdf2_sha256$260000$6973737565722d73616c742d32303236$16126b7cded7ba25cd6cc5dd03d6b73dca5b29c8b6b7e1ff4bfcd0e55a7de57a',
   'issuer', '0.0.11060814', 'Direction financière LILAS'),
  ('22222222-2222-4222-8222-222222222222', 'broker@veda.tn',
   'pbkdf2_sha256$260000$62726f6b65722d73616c742d32303236$257d176fa395c1f353aadd5bb045ab05e72c57eee7ed5db9c0cf845c218f846d',
   'broker', '0.0.11060814', 'Desk marchés Veda'),
  ('33333333-3333-4333-8333-333333333333', 'verifier@veda.tn',
   'pbkdf2_sha256$260000$76657269666965722d73616c742d32303236$6c77d3f8e2c890b5f90b6a1b51eba73516db3d55d54c2e13d830f28a3ab5dfc8',
   'verifier', '0.0.11060814', 'Audit & conformité Veda'),
  ('44444444-4444-4444-8444-444444444444', 'admin@veda.tn',
   'pbkdf2_sha256$260000$61646d696e2d73616c742d32303236$84ab6573a5e1d8eb303093aa36d30b7acd45642745fe6c68cfadf77e21f012b4',
   'admin', '0.0.11060814', 'Administrateur Veda')
ON CONFLICT (email) DO UPDATE
SET display_name = COALESCE(users.display_name, EXCLUDED.display_name);
