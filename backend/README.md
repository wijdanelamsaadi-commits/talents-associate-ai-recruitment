# Backend

FastAPI backend skeleton for the Talents Associate AI Recruitment Platform.

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

The API will run at `http://localhost:8000`.

## Available Endpoints

- `GET /api/health`: project health and status.
- `POST /api/candidates`: create a candidate.
- `GET /api/candidates`: list candidates.
- `GET /api/candidates/{id}`: get one candidate by ID.
- `GET /api/cv-upload`: CV upload module placeholder.
- `GET /api/jobs`: jobs module placeholder.
- `GET /api/matching`: AI matching module placeholder.
- `GET /api/interviews`: interviews module placeholder.

## Database Migrations

Configure PostgreSQL in `.env`, then run:

```bash
alembic upgrade head
```

To create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe migration"
```

Authentication and AI parsing will be added in later iterations.
