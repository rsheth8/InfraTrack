<p align="center">
  <img src="docs/brand/logo.png" width="128" alt="InfraTrack">
</p>

<h1 align="center">InfraTrack</h1>

<p align="center">
  See the AWS bill before finance does.
</p>

<p align="center">
  <a href="https://github.com/rsheth8/InfraTrack">Source</a>&nbsp;·&nbsp;<a href="CONTRIBUTING.md">Run locally</a>
</p>

<p align="center">
  <a href="https://github.com/rsheth8/InfraTrack/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/rsheth8/InfraTrack/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat-square">
  <img alt="React" src="https://img.shields.io/badge/React-Vite-61DAFB?style=flat-square&logo=react&logoColor=black">
  <img alt="Tests" src="https://img.shields.io/badge/tests-39-brightgreen?style=flat-square">
</p>

<p align="center"><sub>Scaffold with synthetic demo data. Cost Explorer is a one-function swap. No auth — local only.</sub></p>

---

## What this is

Imagine every engineering team at a company shares one AWS bill, and nobody
finds out they overspent until finance emails them at the end of the month.
InfraTrack is a small internal tool that fixes that: each team gets a
dashboard showing what they're spending money on in AWS, day by day, broken
down by service (compute, storage, databases, etc.), compared against a
budget someone set for that month. If spend crosses a threshold — say 80% of
budget — the team can get an email alert instead of a surprise.

There's no real AWS account wired up yet. The project ships with a **realistic
synthetic data generator** so the dashboard is fully populated and usable the
moment you run it, and the one place that would call the real AWS billing API
is clearly marked and swappable.

In short: it's a budgeting and observability dashboard for cloud costs, built
as a working full-stack scaffold rather than a finished product.

---

## Key features

- **Per-team dashboard** — pick a team, see this month's budget, month-to-date
  spend, and a percent-used bar that turns red once spend passes 100%.
- **Time-series spend chart** — daily cost over a selectable window (day /
  week / month / quarter).
- **Per-service breakdown** — a bar chart of which AWS services (EC2, RDS,
  S3, CloudFront, Lambda, DynamoDB, CloudWatch) are driving the bill.
- **Budget alerts** — create, list, and delete threshold-based alerts per
  team (e.g. "email ops@team.com when spend passes 90% of budget"), stored in
  the database and evaluated by a standalone script.
- **Zero-setup demo data** — a seed script fabricates 90 days of plausible
  usage across 4 teams so there's something real to look at immediately.

---

## How it works

1. **Data lands in the database.** A script (`fetch_usage.py`) generates or
   fetches daily cost figures per team/service and writes them as
   `usage_snapshots` rows. Today this is a synthetic cost model; in
   production it would call AWS Cost Explorer instead (see below).
2. **The API reads and aggregates.** The FastAPI backend queries Postgres/SQLite
   through SQLAlchemy and exposes REST endpoints that roll usage up by time
   period and by service, compute budget-vs-spend percentages, and manage
   alert records.
3. **The frontend renders it.** A React app fetches from those endpoints and
   renders the budget bar, line chart, and bar chart with recharts, and
   provides a form to manage alerts.
4. **Alerts are evaluated out-of-band.** A separate script (`send_alerts.py`)
   is meant to run on a schedule (cron, CronJob, etc.), check each enabled
   alert's threshold against current spend, and fire a notification when
   crossed. Nothing in the request path blocks on this — it's decoupled from
   the API.

```mermaid
flowchart LR
    subgraph Frontend["Frontend — React + Vite + recharts"]
        UI[Dashboard UI]
        TeamSel[Team / Period Selector]
        Charts[Usage Charts]
        AlertsUI[Alerts Settings]
    end

    subgraph Backend["Backend — FastAPI"]
        Teams["/api/teams"]
        Usage["/api/usage"]
        Budget["/api/budget"]
        Alerts["/api/alerts"]
    end

    subgraph Data["Data layer"]
        DB[(Postgres or SQLite)]
    end

    subgraph Jobs["Scheduled / offline scripts"]
        Seed["seed.py<br/>fabricates 90 days of demo data"]
        Fetch["fetch_usage.py<br/>writes daily usage_snapshots"]
        Notify["send_alerts.py<br/>evaluates thresholds"]
    end

    UI --> TeamSel
    UI --> Charts
    UI --> AlertsUI

    TeamSel -->|GET| Teams
    Charts -->|GET| Usage
    Charts -->|GET| Budget
    AlertsUI -->|GET / POST / DELETE| Alerts

    Teams --> DB
    Usage --> DB
    Budget --> DB
    Alerts --> DB

    Seed --> DB
    Fetch -->|"synthetic model today,<br/>AWS Cost Explorer swap-in later"| DB
    DB --> Notify
    Notify -->|email, once wired up| Team_Owner[Team owner]
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.x (ORM), Pydantic v2, uvicorn |
| Database | SQLite by default (zero setup); Postgres 16 opt-in via Docker |
| Frontend | React 18, TypeScript, Vite, recharts |
| Testing | pytest (39 tests, run against both SQLite and Postgres), ruff |
| CI | GitHub Actions — lint, format, tests on Python 3.11 + 3.14, Postgres job, frontend build |
| Dev/infra | python-dotenv, CORS middleware, Vite dev-server proxy, Docker Compose |

---

## Project structure

```
.github/workflows/ci.yml         # lint + tests (SQLite & Postgres) + frontend build
infratrack/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, router wiring, /health
│   │   ├── db.py                # SQLAlchemy engine — SQLite default, Postgres via DATABASE_URL
│   │   ├── entities.py          # ORM models: Team, Budget, Alert, UsageSnapshot
│   │   ├── models.py            # Pydantic request/response schemas (API contract)
│   │   ├── spend.py             # month-to-date spend, derived from usage_snapshots
│   │   └── routes/
│   │       ├── teams.py         # GET /api/teams
│   │       ├── usage.py         # GET /api/usage — period rollup + by-service totals
│   │       ├── budget.py        # GET /api/budget — spend vs. budget %
│   │       └── alerts.py        # GET/POST/DELETE /api/alerts
│   ├── scripts/
│   │   ├── seed.py              # generates 90 days of synthetic usage, budgets, alerts
│   │   ├── fetch_usage.py       # writes today's usage snapshots (cron target, idempotent)
│   │   └── send_alerts.py       # evaluates alert thresholds against spend
│   ├── tests/                   # pytest suite — endpoints, jobs, schema parity
│   ├── requirements.txt         # runtime pins (verified on Python 3.11–3.14)
│   └── requirements-dev.txt     # pytest + ruff
├── frontend/
│   ├── index.html
│   ├── vite.config.ts           # proxies /api/* to the backend on :8000
│   ├── package.json
│   └── src/
│       ├── App.tsx              # top-level layout, team + period selection
│       ├── utils/api.ts         # typed fetch client for the backend API
│       └── components/
│           ├── Dashboard.tsx    # budget bar + month-to-date stats
│           ├── UsageCharts.tsx  # recharts line chart + per-service bar chart
│           ├── TeamSelector.tsx
│           └── AlertsSettings.tsx  # alert CRUD form/list
├── db/schema.sql                # Postgres DDL mirroring entities.py (used when running on Postgres)
└── docker-compose.yml           # boots Postgres 16 for local use
```

---

## Setup / running locally

### 1. Backend

```bash
cd infratrack/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Populate 4 teams, 90 days of usage, budgets, and one alert each
python -m scripts.seed

# Boot the API on :8000
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

### 2. Frontend

```bash
cd infratrack/frontend
npm install
npm run dev
```

Vite serves the UI on `http://localhost:5173` and proxies `/api/*` requests
to the backend on `:8000`.

### 3. Optional: use Postgres instead of SQLite

```bash
cd infratrack
docker compose up -d                              # boots Postgres on :5432
export DATABASE_URL=postgresql+psycopg2://infratrack:infratrack@localhost:5432/infratrack
psql "$DATABASE_URL" -f db/schema.sql              # one-time schema creation
cd backend && python -m scripts.seed               # re-seed against Postgres
```

### 4. Tests

```bash
cd infratrack/backend
pip install -r requirements.txt -r requirements-dev.txt
pytest                      # 34 tests on SQLite; 5 Postgres-only tests skip

ruff check app scripts tests
ruff format --check app scripts tests
```

To run the same suite against a real Postgres — which also activates the
schema-parity tests that apply `db/schema.sql` and diff it against the ORM:

```bash
docker compose up -d
TEST_DATABASE_URL=postgresql+psycopg2://infratrack:infratrack@localhost:5432/infratrack pytest
```

CI runs all of it on every push: lint and format, the suite on Python 3.11 and
3.14, the suite again against Postgres 16, a smoke test that runs the offline
jobs end to end, and the frontend typecheck and build.

### API reference

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/teams` | List all teams |
| `GET` | `/api/usage?team_id=&period=` | Daily spend points + per-service totals. `period` is one of `day`, `week`, `month`, `quarter`. |
| `GET` | `/api/budget?team_id=` | Current month's budget, spend, and percent used |
| `GET` | `/api/alerts?team_id=` | List alerts (optionally filtered by team) |
| `POST` | `/api/alerts` | Create an alert (`team_id`, `threshold`, `email`) |
| `DELETE` | `/api/alerts/{id}` | Delete an alert |
| `GET` | `/health` | Liveness probe |

---

## Notable implementation details

- **Spend is derived, never stored.** `budgets` used to carry a `spend_usd`
  column written once at seed time. Nothing updated it afterwards, so the
  moment the daily `fetch_usage` job took over, the dashboard under-reported
  spend and — worse for an alerting tool — threshold alerts silently stopped
  firing. Spend is now summed from `usage_snapshots` on read
  (`app/spend.py`), so it cannot go stale. A cached total needs every writer
  to remember to invalidate it; the one that forgets is a bug you only notice
  from the finance email you built the tool to avoid. Regression tests in
  `tests/test_budget.py` and `tests/test_jobs.py` cover both paths.
- **The daily job is idempotent.** `fetch_usage.py` clears the current day's
  rows before writing them, and a `UNIQUE (team_id, snapshot_date, service)`
  constraint enforces one row per team/service/day at the database level. A
  retried or double-scheduled cron run replaces the day instead of doubling
  it. That constraint's `(team_id, snapshot_date)` prefix doubles as the index
  every dashboard read needs for its date-range filter — one index, two jobs.
- **Aggregation happens in SQL.** `/api/usage` groups and sums in the database
  rather than loading every snapshot row and folding it in Python; the row
  count grows with teams × services × days.
- **Invalid input is rejected, not coerced.** `period` is a `Literal` type, so
  an unrecognised window returns 422 instead of silently falling back to seven
  days. Alert emails are validated as `EmailStr`, and thresholds must be
  positive — a 0% threshold would fire on every evaluation forever.
- **SQLite-first, Postgres-compatible — and proven.** `app/db.py` defaults to a
  local SQLite file with no configuration required; `DATABASE_URL` switches the
  same models to Postgres. Because SQLite is lenient about types and
  constraints, CI runs the whole suite a second time against Postgres 16, plus
  parity tests that apply `db/schema.sql` and diff the result against the ORM
  models — so the hand-maintained DDL cannot quietly drift from `entities.py`.
- **Synthetic-but-plausible cost data.** `scripts/seed.py` generates costs from
  a per-service daily mean, then layers in a per-team multiplier
  (`Uniform(0.6, 1.8)`), weekend seasonality (0.78× on weekends), a mild upward
  drift over the 90-day window, and Gaussian jitter — so the demo data looks
  like a real, slightly noisy AWS bill rather than a flat line. Seeded with a
  fixed RNG, so the demo is reproducible.
- **Real AWS is a one-function swap.** To connect actual billing data, replace
  the sampling logic in `fetch_usage.py` with a `boto3` call to
  `get_cost_and_usage` from AWS Cost Explorer and map the results onto
  `UsageSnapshot` rows — the API, database schema, and frontend need no changes.
- **Alerts are decoupled from the request path.** Creating an alert just writes
  a row; nothing in the API sends email. `send_alerts.py` runs on a schedule
  (cron, Kubernetes CronJob, GitHub Actions), independently evaluating each
  enabled alert's threshold against current spend.
- **No authentication.** The API and frontend are open by design — this is a
  scaffold. Adding SSO or JWT-based auth in front of the FastAPI app is left as
  an integration step for whoever deploys it, since the right choice depends on
  the surrounding infrastructure.
- **CORS is pre-configured** for local development, allowing the Vite dev
  server origins (`localhost:5173` and `localhost:3000`) to call the API.

## Known gaps

Deliberate, not oversights:

- **No auth**, as above — don't expose this on the public internet as-is.
- **No frontend unit tests.** CI typechecks and builds the React app, which
  catches breakage; component tests aren't worth a test-runner dependency for
  four presentational components.
- **No migrations.** Schema changes mean re-running `db/schema.sql`. Alembic is
  the right answer the moment there's data worth preserving.
- **`send_alerts.py` logs instead of emailing.** Wiring SES or a webhook is a
  credentials problem, not a design one.

## Contributing

PRs and issues welcome. How to run tests, env vars, and the expected layout: [CONTRIBUTING.md](CONTRIBUTING.md).

Don't commit `.env`, API keys, or personal recordings.

