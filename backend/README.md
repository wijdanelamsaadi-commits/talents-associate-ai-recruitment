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
- `POST /api/jobs`: create a job offer.
- `GET /api/jobs`: list job offers.
- `GET /api/jobs/{id}`: get one job offer.
- `PUT /api/jobs/{id}`: update one job offer.
- `DELETE /api/jobs/{id}`: delete one job offer.
- `POST /api/matching/candidate/{candidate_id}/job/{job_id}`: match a parsed candidate against a job.
- `GET /api/matching/results`: list matching results.
- `GET /api/matching/candidate/{candidate_id}`: list matching results for one candidate.
- `GET /api/interviews`: interviews module placeholder.
- `POST /api/portal/auth/register`: create a candidate portal account.
- `POST /api/portal/auth/login`: login as a candidate.
- `GET /api/portal/profile`: read the authenticated candidate profile.
- `PUT /api/portal/profile`: update the authenticated candidate profile.
- `PUT /api/portal/profile/cv`: upload or replace the authenticated candidate CV.
- `GET /api/portal/applications`: list authenticated candidate applications and matching scores.
- `POST /api/portal/jobs/{id}/apply-auth`: apply to a public job with the authenticated candidate profile and latest CV.

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

## Matching Test

Create a job offer:

```powershell
$job = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/jobs" `
  -ContentType "application/json" `
  -Body '{
    "title":"Backend Developer",
    "company_name":"TalentCo",
    "location":"Casablanca",
    "contract_type":"full_time",
    "required_skills":["Python","FastAPI","PostgreSQL"],
    "preferred_skills":["React","Docker"],
    "required_experience_years":2,
    "education_level":"master",
    "description":"Backend role requiring English and French.",
    "status":"open"
  }'
```

Run matching after uploading and parsing a CV:

```powershell
$match = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/matching/candidate/$($candidate.id)/job/$($job.id)"

Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/matching/candidate/$($candidate.id)"
```

The first matching engine uses weighted heuristics: 50% skills, 25% experience, 15% education, and 10% language match.
