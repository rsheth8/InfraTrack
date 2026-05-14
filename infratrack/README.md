# InfraTrack

InfraTrack is a full-stack cloud infrastructure monitoring dashboard for visualizing AWS usage and costs across teams and accounts. This repo includes a FastAPI backend, a React + TypeScript frontend, and a Postgres schema.

## Structure

```
infratrack/
  frontend/
  backend/
  db/
  docker-compose.yml
```

## Quick start

1. Start Postgres:

```
docker compose up -d
```

2. Run the backend (from `infratrack/backend`):

```
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic boto3 psycopg2-binary
uvicorn app.main:app --reload
```

3. Run the frontend (from `infratrack/frontend`):

```
npm install
npm run dev
```

## API

- `GET /api/usage?team_id=1&period=week`
- `POST /api/alerts`
- `GET /api/budget?team_id=1`

## Notes

This is a scaffold. The AWS integrations, auth, and persistence layers are left as TODOs for implementation.
