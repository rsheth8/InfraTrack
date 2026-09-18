CREATE TABLE IF NOT EXISTS teams (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS budgets (
  id SERIAL PRIMARY KEY,
  team_id INTEGER NOT NULL REFERENCES teams(id),
  month TEXT NOT NULL,
  budget_usd NUMERIC(12, 2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
  id SERIAL PRIMARY KEY,
  team_id INTEGER NOT NULL REFERENCES teams(id),
  threshold NUMERIC(5, 2) NOT NULL,
  email TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usage_snapshots (
  id SERIAL PRIMARY KEY,
  team_id INTEGER NOT NULL REFERENCES teams(id),
  service TEXT NOT NULL,
  cost_usd NUMERIC(12, 2) NOT NULL,
  snapshot_date DATE NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- One row per team/service/day. Makes fetch_usage re-runs safe, and the
-- (team_id, snapshot_date) prefix is the index dashboard reads need.
CREATE UNIQUE INDEX IF NOT EXISTS uq_usage_team_date_service
  ON usage_snapshots (team_id, snapshot_date, service);
