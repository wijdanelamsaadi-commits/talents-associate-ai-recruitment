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
Use `VITE_API_BASE_URL=http://localhost:8001` when local port `8000` is occupied.

Public candidate portal:

- Job list: `http://localhost:5173/portal`
- Job details and CV application form: `http://localhost:5173/portal/jobs/{jobId}`
- Candidate account creation: `http://localhost:5173/portal/register`
- Candidate login/profile: `http://localhost:5173/portal/login`, then `http://localhost:5173/portal/profile`
- Candidate applications: `http://localhost:5173/portal/applications`

## Intégration avec le site Talents Associate

Le portail candidat est conçu comme une extension légère du site actuel Talents Associate et du formulaire de recrutement existant.

- Le site actuel peut rediriger vers `/portal/register` pour créer un compte candidat réutilisable.
- Les pages carrières ou opportunités peuvent rediriger vers `/portal/jobs` pour afficher les offres disponibles.
- Une URL `/portal/apply` reste prévue comme point d'entrée intégrable depuis le site existant, avec redirection vers les offres.
- Le formulaire actuel `talentsag.ma/formulaire-de-recrutement` peut être remplacé progressivement ou relié à ce portail.
- Après connexion, `/portal/profile` permet au candidat de compléter son profil, déposer ou remplacer son CV, puis postuler aux offres.
- Le back-office recruteur reste séparé sous `/login`, `/dashboard`, `/candidates`, `/jobs`, `/matching`, `/interviews` et `/evaluations`.

Build the frontend with:

```bash
npm run build
```

## Parsing CV avec LLM

Le backend peut utiliser un LLM pour extraire les informations structurées des CV, tout en conservant le parser heuristique existant en fallback.

Configuration dans `backend/.env` :

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key
LLM_MODEL=gpt-4o-mini
LLM_ENABLED=true
```

Quand `LLM_ENABLED=false`, quand `OPENAI_API_KEY` est vide, ou si l'appel LLM échoue, le backend utilise automatiquement le parsing heuristique local.
La sortie structurée contient notamment `prenom`, `nom`, `email`, `phone`, `linkedin_url`, `current_company`, `current_title`, `total_experience_years`, `detailed_experience`, `education`, `skills`, `languages`, `soft_skills`, `gender`, `parser_used` et `parser_confidence`.
Le prompt interdit explicitement l'invention d'informations : les champs absents du CV doivent rester à `null` ou `[]`.

## Notes

- Outlook CV attachments can be handled first with a VBA macro that saves attachments locally, then those CV files can be imported into the platform. Microsoft Graph integration can remain optional for a later version. See [docs/outlook-cv-extraction.md](docs/outlook-cv-extraction.md).
