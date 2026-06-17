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
- `GET /api/candidates`: candidates module placeholder.
- `GET /api/cv-upload`: CV upload module placeholder.
- `GET /api/jobs`: jobs module placeholder.
- `GET /api/matching`: AI matching module placeholder.
- `GET /api/interviews`: interviews module placeholder.

Business logic, models, migrations, authentication, and AI parsing will be added in later iterations.
