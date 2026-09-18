# Contributing to InfraTrack

## Prerequisites
- Python 3.11+ (CI covers 3.11 and 3.14)
- Node.js 20.19+ or 22.12+ (Vite 8 requirement)

## Run

```bash
cd infratrack/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.seed
uvicorn app.main:app --reload     # :8000  (docs at /docs)
```

```bash
cd infratrack/frontend
npm install
npm run dev                       # :5173, proxies /api
```

## Tests

```bash
cd infratrack/backend
pip install -r requirements.txt -r requirements-dev.txt
pytest                            # 34 on SQLite; 5 Postgres-only tests skip
ruff check app scripts tests
ruff format --check app scripts tests
```

Against Postgres — this also activates the schema-parity tests, which apply
`db/schema.sql` and diff it against the ORM models:

```bash
cd infratrack && docker compose up -d
cd backend
TEST_DATABASE_URL=postgresql+psycopg2://infratrack:infratrack@localhost:5432/infratrack pytest
```

CI (`.github/workflows/ci.yml`) runs lint, format, the suite on Python 3.11 and
3.14, the suite again on Postgres 16, a smoke test of the offline jobs, and the
frontend typecheck and build. Please keep it green.

## Conventions

- Tests live in `backend/tests/`, named for the module under test. A bug fix
  ships with a test that fails without it — see `test_budget.py` for the shape.
- `ruff.toml` and `pytest.ini` pin lint and test config so local runs match CI.
- Spend is always derived from `usage_snapshots` (`app/spend.py`), never stored
  on `budgets`. A cached total that no writer invalidates is how this project's
  worst bug happened.

## Environment

Everything has a working default; see `backend/.env.example`. `DATABASE_URL` is
the only knob — omit it for SQLite, set it to a Postgres URL to switch.

Don't commit `.env`, API keys, database files, or personal recordings.
