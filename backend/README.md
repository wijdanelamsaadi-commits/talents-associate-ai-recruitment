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
- `POST /api/cv/upload`: upload a candidate CV and extract raw text.
- `GET /api/cv/files`: list uploaded CV files.
- `GET /api/cv/files/{id}`: get one uploaded CV file by ID.
- `GET /api/cv/files/{id}/text`: get extracted raw CV text.
- `POST /api/cv/{id}/parse`: parse extracted text into structured candidate JSON.
- `GET /api/cv/{id}/parsed`: get parsing status, confidence score, and structured JSON.
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

## CV Upload Test

Supported formats:

- PDF
- DOCX
- DOC upload is recognized, but text extraction is not supported yet.

Maximum file size: 5MB.

Create a candidate first:

```powershell
$candidate = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/candidates" `
  -ContentType "application/json" `
  -Body '{"first_name":"Test","last_name":"Candidate","email":"test.candidate@example.com"}'
```

Upload a PDF or DOCX:

```powershell
$form = @{
  candidate_id = $candidate.id
  file = Get-Item "C:\path\to\cv.pdf"
}

$cv = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/cv/upload" `
  -Form $form
```

Read extracted text:

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/cv/files/$($cv.id)/text"
```

Parse extracted text into structured JSON:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/cv/$($cv.id)/parse"
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/cv/$($cv.id)/parsed"
```

The first parser version uses regex and section heuristics only. It does not call any LLM API yet.
