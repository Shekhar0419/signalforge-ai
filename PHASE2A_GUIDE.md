# Phase 2A — Persistent Dataset History

Copy these files into your existing `signalforge-ai` folder and replace matching files.

Run:

```powershell
pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
pytest -q
uvicorn app.main:app --reload
```

Test in Swagger:

1. `POST /api/v1/datasets/profile`
2. `GET /api/v1/datasets`
3. `GET /api/v1/datasets/{dataset_id}`

Commit:

```powershell
git add .
git commit -m "Add persistent dataset history with SQLAlchemy and Alembic"
git push
```
