# Database ERD

This document describes the PostgreSQL database design for the Talents Associate AI Recruitment Platform.

## Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ candidates : owns
    users ||--o{ cv_files : uploads
    users ||--o{ extracted_cv_data : reviews
    users ||--o{ job_offers : creates
    users ||--o{ ai_matching_results : reviews
    users ||--o{ interviews : schedules
    users ||--o{ interviews : interviews
    users ||--o{ evaluations : evaluates
    users ||--o{ candidate_timeline_events : creates

    candidates ||--o{ cv_files : has
    candidates ||--o{ extracted_cv_data : has
    candidates ||--o{ candidate_skills : has
    candidates ||--o{ experiences : has
    candidates ||--o{ education : has
    candidates ||--o{ applications : submits
    candidates ||--o{ ai_matching_results : receives
    candidates ||--o{ interviews : attends
    candidates ||--o{ candidate_timeline_events : has

    cv_files ||--|| extracted_cv_data : parsed_into
    cv_files ||--o{ applications : supports

    skills ||--o{ candidate_skills : assigned_to

    job_offers ||--o{ applications : receives
    job_offers ||--o{ ai_matching_results : matched_against

    applications ||--o{ ai_matching_results : has
    applications ||--o{ interviews : schedules
    applications ||--o{ evaluations : receives
    applications ||--o{ candidate_timeline_events : logs

    interviews ||--o{ evaluations : has

    users {
        uuid id PK
        varchar full_name
        varchar email UK
        text password_hash
        varchar role
        varchar status
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
    }

    candidates {
        uuid id PK
        varchar first_name
        varchar last_name
        varchar email UK
        varchar phone
        varchar location
        text linkedin_url
        text portfolio_url
        varchar current_title
        varchar source
        varchar status
        boolean consent_given
        uuid owner_user_id FK
        timestamptz created_at
        timestamptz updated_at
    }

    cv_files {
        uuid id PK
        uuid candidate_id FK
        uuid uploaded_by_user_id FK
        varchar original_filename
        text storage_path
        varchar mime_type
        bigint file_size_bytes
        char checksum_sha256
        varchar parsing_status
        timestamptz uploaded_at
        timestamptz created_at
        timestamptz updated_at
    }

    extracted_cv_data {
        uuid id PK
        uuid cv_file_id FK
        uuid candidate_id FK
        text raw_text
        jsonb parsed_json
        text summary
        numeric total_years_experience
        varchar highest_degree
        text_array language_codes
        varchar parser_model
        numeric confidence_score
        varchar status
        uuid reviewed_by_user_id FK
        timestamptz reviewed_at
        timestamptz created_at
        timestamptz updated_at
    }

    skills {
        uuid id PK
        varchar name UK
        varchar normalized_name UK
        varchar category
        timestamptz created_at
        timestamptz updated_at
    }

    candidate_skills {
        uuid id PK
        uuid candidate_id FK
        uuid skill_id FK
        varchar proficiency_level
        numeric years_experience
        varchar source
        numeric confidence_score
        timestamptz created_at
        timestamptz updated_at
    }

    experiences {
        uuid id PK
        uuid candidate_id FK
        varchar company_name
        varchar job_title
        varchar location
        date start_date
        date end_date
        boolean is_current
        text description
        varchar source
        timestamptz created_at
        timestamptz updated_at
    }

    education {
        uuid id PK
        uuid candidate_id FK
        varchar institution_name
        varchar degree
        varchar field_of_study
        date start_date
        date end_date
        varchar grade
        text description
        varchar source
        timestamptz created_at
        timestamptz updated_at
    }

    job_offers {
        uuid id PK
        uuid created_by_user_id FK
        varchar title
        varchar department
        varchar location
        varchar employment_type
        varchar work_mode
        text description
        text requirements
        varchar status
        timestamptz opened_at
        timestamptz closed_at
        timestamptz created_at
        timestamptz updated_at
    }

    applications {
        uuid id PK
        uuid candidate_id FK
        uuid job_offer_id FK
        uuid cv_file_id FK
        varchar source
        varchar status
        varchar current_stage
        timestamptz applied_at
        timestamptz created_at
        timestamptz updated_at
    }

    ai_matching_results {
        uuid id PK
        uuid application_id FK
        uuid candidate_id FK
        uuid job_offer_id FK
        varchar model_name
        numeric score
        integer rank_position
        text explanation
        jsonb matched_skills
        jsonb missing_skills
        varchar embedding_version
        varchar status
        uuid reviewed_by_user_id FK
        timestamptz reviewed_at
        timestamptz created_at
        timestamptz updated_at
    }

    interviews {
        uuid id PK
        uuid application_id FK
        uuid candidate_id FK
        uuid scheduled_by_user_id FK
        uuid interviewer_user_id FK
        varchar interview_type
        varchar status
        timestamptz scheduled_start_at
        timestamptz scheduled_end_at
        text meeting_url
        varchar location
        text notes
        timestamptz created_at
        timestamptz updated_at
    }

    evaluations {
        uuid id PK
        uuid interview_id FK
        uuid application_id FK
        uuid evaluator_user_id FK
        integer rating
        varchar recommendation
        text strengths
        text weaknesses
        text notes
        timestamptz submitted_at
        timestamptz created_at
        timestamptz updated_at
    }

    candidate_timeline_events {
        uuid id PK
        uuid candidate_id FK
        uuid application_id FK
        uuid created_by_user_id FK
        varchar event_type
        varchar title
        text description
        jsonb metadata
        timestamptz occurred_at
        timestamptz created_at
        timestamptz updated_at
    }
```

## Table Summary

- `users`: recruiter, admin, and hiring manager authentication records.
- `candidates`: centralized candidate profiles from manual entry, CV upload, LinkedIn CSV, or portal sources.
- `cv_files`: uploaded CV metadata and parsing lifecycle.
- `extracted_cv_data`: AI parser output, raw text, JSON extraction, summary, and review state.
- `skills`: normalized skill catalog.
- `candidate_skills`: many-to-many candidate skill mapping with source and confidence.
- `experiences`: candidate professional history.
- `education`: candidate academic history.
- `job_offers`: open, draft, paused, closed, and archived job offers.
- `applications`: candidate applications to job offers and recruitment stage tracking.
- `ai_matching_results`: semantic match scores, explanations, matched skills, and missing skills.
- `interviews`: scheduled interview rounds and meeting details.
- `evaluations`: interview/application feedback and hiring recommendations.
- `candidate_timeline_events`: CRM timeline for notes, calls, emails, status changes, uploads, interviews, evaluations, and AI events.

## Design Notes

- UUID primary keys are generated with `gen_random_uuid()` from PostgreSQL `pgcrypto`.
- Every core table includes `created_at` and `updated_at`; triggers keep `updated_at` current.
- Status fields use `CHECK` constraints to keep workflow states predictable.
- Foreign keys use cascading deletes for candidate-owned records and `SET NULL` for user audit references.
- JSONB columns support flexible AI parsing and matching outputs.
- Indexes are included for common lookup paths such as candidate status, application status, job status, match score, interview schedule, and CRM timeline date.
