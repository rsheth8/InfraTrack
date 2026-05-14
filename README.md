# InfraTrack

**Cloud-spend dashboard for engineering teams.** Track daily AWS usage per
service, watch month-to-date spend against a configurable monthly budget,
and trigger email alerts when a team crosses a percentage threshold.

Full-stack TypeScript + Python project — **FastAPI + SQLAlchemy + Postgres
(or SQLite) on the back, React + Vite + recharts on the front**, with a
seed script that produces 90 days of realistic synthetic usage data so the
dashboard works end-to-end out of the box.

---

## What it does

- **Per-team dashboard** with monthly budget, month-to-date spend, and a
  visual percent-used bar that flips red past 100%
- **Time-series line chart** of daily spend over the selected window
  (day / week / month / quarter)
- **Per-service bar chart** showing the dominant cost lines (EC2, RDS,
  S3, CloudFront, Lambda, DynamoDB, CloudWatch)
- **Alerts CRUD** — create / list / delete budget-threshold alerts per team,
  each backed by a database row and evaluatable from a cron-style job

---

## Architecture

```
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  React + Vite    │   /api  │  FastAPI         │         │  SQLite (default)│
│  recharts UI     │ ──────► │  + SQLAlchemy 2  │ ──────► │  or Postgres     │
└──────────────────┘         └──────────────────┘         └──────────────────┘
        ▲                            ▲
        │                            │ scheduled (cron)
        │                       ┌──────────────────┐
        │                       │ scripts/         │
        │                       │  fetch_usage.py  │  ← samples synthetic-cost model
        │                       │  send_alerts.py  │  ← evaluates % thresholds
        │                       │  seed.py         │  ← 90 days of demo data
        │                       └──────────────────┘
```

Defaults to **SQLite** so the project runs with zero external services. Set
`DATABASE_URL` to the Postgres URL exposed by `docker-compose.yml` to swap
backends — the SQLAlchemy layer is identical either way.

---

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Populate 4 teams, 90 days of usage, budgets, and one alert each
python -m scripts.seed

# Boot the API on :8000
uvicorn app.main:app --reload
```

Hit `http://localhost:8000/docs` for the Swagger UI.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite serves on `http://localhost:5173` and proxies `/api/*` to the backend.

### 3. Optional: Postgres instead of SQLite

```bash
docker compose up -d                              # boots Postgres on :5432
export DATABASE_URL=postgresql+psycopg2://infratrack:infratrack@localhost:5432/infratrack
psql "$DATABASE_URL" -f db/schema.sql              # one-time
cd backend && python -m scripts.seed               # re-seed against Postgres
```

---

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/teams` | List all teams |
| `GET` | `/api/usage?team_id=&period=` | Daily spend points + by-service rollup. `period` ∈ `day`, `week`, `month`, `quarter`. |
| `GET` | `/api/budget?team_id=` | Current month's budget + spend + percent used |
| `GET` | `/api/alerts?team_id=` | List alerts |
| `POST` | `/api/alerts` | Create alert (body: `team_id`, `threshold`, `email`) |
| `DELETE` | `/api/alerts/{id}` | Delete alert |
| `GET` | `/health` | Liveness probe |

All schemas live in [`backend/app/models.py`](backend/app/models.py) as
Pydantic models and are documented automatically at `/docs`.

---

## Project layout

```
infratrack/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS + router wiring
│   │   ├── db.py                # SQLAlchemy engine (SQLite default, Postgres opt-in)
│   │   ├── entities.py          # ORM: Team, Budget, Alert, UsageSnapshot
│   │   ├── models.py            # Pydantic API contracts
│   │   └── routes/
│   │       ├── teams.py         # GET /teams
│   │       ├── usage.py         # GET /usage  (period rollup + by_service)
│   │       ├── budget.py        # GET /budget
│   │       └── alerts.py        # GET/POST/DELETE /alerts
│   ├── scripts/
│   │   ├── seed.py              # 90 days of synthetic usage, budgets, alerts
│   │   ├── fetch_usage.py       # daily cron: write today's snapshots
│   │   └── send_alerts.py       # evaluate thresholds, log triggered alerts
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── vite.config.ts           # /api → :8000 proxy
│   ├── tsconfig.json
│   ├── package.json
│   └── src/
│       ├── App.tsx              # team + period selectors, layout grid
│       ├── utils/api.ts         # typed fetch client
│       └── components/
│           ├── Dashboard.tsx    # budget bar + MTD stats
│           ├── UsageCharts.tsx  # recharts line + bar
│           ├── TeamSelector.tsx
│           └── AlertsSettings.tsx  # alerts CRUD UI
├── db/schema.sql                # Postgres-flavored DDL (mirrors entities.py)
└── docker-compose.yml           # Postgres 16
```

---

## Synthetic data — why and what

There's no real AWS account behind this. The seed in
[`backend/scripts/seed.py`](backend/scripts/seed.py) generates costs from a
service-level daily mean (`SERVICE_DAILY_MEANS`), then applies three
multiplicative effects to make the result look like a real bill:

1. **Per-team multiplier** drawn from `Uniform(0.6, 1.8)` so totals vary
2. **Weekly seasonality** — weekends scaled to 0.78× of weekday cost
3. **Mild upward drift** over the 90-day window (~+15%)
4. **Gaussian jitter** (`σ = 0.12`) per service-day

`fetch_usage.py` reuses the same model so subsequent cron runs continue to
write plausible new rows. To wire to **real AWS Cost Explorer**, replace the
sampling block in `fetch_usage.py` with a `boto3` call to `get_cost_and_usage`
and map services + dates onto `UsageSnapshot` — nothing else changes.

---

## Stack

| Layer | Stack |
|---|---|
| Backend | FastAPI · SQLAlchemy 2.x ORM · Pydantic v2 · uvicorn |
| Database | SQLite (default) · Postgres 16 (opt-in via Docker) |
| Frontend | React 18 · Vite · TypeScript · recharts |
| Dev | python-dotenv · CORS middleware · Vite dev-server proxy |

---

## Notes

- Real AWS integration is intentionally one swap away: replace the sampler in
  `fetch_usage.py` with `boto3.client("ce").get_cost_and_usage(...)` and the
  rest of the pipeline (DB, API, charts) keeps working unchanged.
- Auth is omitted on purpose — adding it would be SSO or JWT depending on
  deployment, and the alert routes already validate team existence. Wrap the
  app in your usual auth dependency before exposing it publicly.
- For production, swap SQLite for Postgres (the docker-compose Postgres is
  ready) and run `fetch_usage.py` + `send_alerts.py` on a scheduler
  (Kubernetes CronJob, GitHub Actions schedule, or systemd timer).
