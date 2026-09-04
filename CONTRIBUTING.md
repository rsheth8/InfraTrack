# Contributing to InfraTrack

## Prerequisites
- Python 3.11+
- Node.js (frontend)

## Run
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.seed
uvicorn app.main:app --reload     # :8000  (docs at /docs)
```

```bash
cd frontend
npm install
npm run dev                       # :5173, proxies /api
```

Demo data is synthetic. Swap `scripts/fetch_usage.py` for AWS Cost Explorer if you wire a real account.

No auth on purpose — don't expose this on the public internet as-is.
