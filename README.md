# Talents Associate AI Recruitment Platform

AI-powered recruitment platform for CV parsing, candidate centralization, semantic matching, interview management, and candidate CRM.

## Main Modules

1. CV upload and AI parsing
2. Candidate database
3. LinkedIn CSV import
4. AI matching and shortlist
5. Candidate portal
6. Interview management and evaluation
7. Candidate CRM history

## Recommended Stack

- Backend: FastAPI
- Frontend: React + Vite
- Database: PostgreSQL
- AI: LLM API + embeddings
- Versioning: Git/GitHub

## Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/api/health`

Run database migrations from `backend/` after configuring PostgreSQL:

```bash
alembic upgrade head
```

## Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

The React app runs at `http://localhost:5173` and expects the API base URL in `VITE_API_BASE_URL`.

Build the frontend with:

```bash
npm run build
```
