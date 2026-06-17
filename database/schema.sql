-- Talents Associate AI Recruitment Platform
-- PostgreSQL database schema

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'recruiter'
        CHECK (role IN ('admin', 'recruiter', 'hiring_manager')),
    status VARCHAR(30) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'invited', 'suspended', 'deleted')),
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    location VARCHAR(255),
    linkedin_url TEXT,
    portfolio_url TEXT,
    current_title VARCHAR(150),
    source VARCHAR(50) NOT NULL DEFAULT 'manual'
        CHECK (source IN ('manual', 'cv_upload', 'linkedin_csv', 'candidate_portal', 'referral', 'other')),
    status VARCHAR(40) NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'active', 'shortlisted', 'interviewing', 'offered', 'hired', 'rejected', 'archived')),
    consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT candidates_email_unique UNIQUE (email)
);

CREATE TABLE cv_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    uploaded_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    mime_type VARCHAR(100),
    file_size_bytes BIGINT CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
    checksum_sha256 CHAR(64),
    parsing_status VARCHAR(30) NOT NULL DEFAULT 'pending'
        CHECK (parsing_status IN ('pending', 'processing', 'parsed', 'failed')),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE extracted_cv_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cv_file_id UUID NOT NULL UNIQUE REFERENCES cv_files(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    raw_text TEXT,
    parsed_json JSONB,
    summary TEXT,
    total_years_experience NUMERIC(4, 1) CHECK (total_years_experience IS NULL OR total_years_experience >= 0),
    highest_degree VARCHAR(150),
    language_codes TEXT[],
    parser_model VARCHAR(100),
    confidence_score NUMERIC(5, 4) CHECK (confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1),
    status VARCHAR(30) NOT NULL DEFAULT 'parsed'
        CHECK (status IN ('parsed', 'needs_review', 'approved', 'failed')),
    reviewed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL UNIQUE,
    normalized_name VARCHAR(120) NOT NULL UNIQUE,
    category VARCHAR(80),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE candidate_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    proficiency_level VARCHAR(30)
        CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    years_experience NUMERIC(4, 1) CHECK (years_experience IS NULL OR years_experience >= 0),
    source VARCHAR(40) NOT NULL DEFAULT 'cv_parsing'
        CHECK (source IN ('cv_parsing', 'manual', 'linkedin_csv', 'candidate_portal', 'ai_inference')),
    confidence_score NUMERIC(5, 4) CHECK (confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT candidate_skills_unique UNIQUE (candidate_id, skill_id)
);

CREATE TABLE experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    company_name VARCHAR(180) NOT NULL,
    job_title VARCHAR(180) NOT NULL,
    location VARCHAR(180),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    source VARCHAR(40) NOT NULL DEFAULT 'cv_parsing'
        CHECK (source IN ('cv_parsing', 'manual', 'linkedin_csv', 'candidate_portal')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

CREATE TABLE education (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    institution_name VARCHAR(180) NOT NULL,
    degree VARCHAR(180),
    field_of_study VARCHAR(180),
    start_date DATE,
    end_date DATE,
    grade VARCHAR(80),
    description TEXT,
    source VARCHAR(40) NOT NULL DEFAULT 'cv_parsing'
        CHECK (source IN ('cv_parsing', 'manual', 'linkedin_csv', 'candidate_portal')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

CREATE TABLE job_offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(180) NOT NULL,
    department VARCHAR(120),
    location VARCHAR(180),
    employment_type VARCHAR(40) NOT NULL DEFAULT 'full_time'
        CHECK (employment_type IN ('full_time', 'part_time', 'contract', 'internship', 'temporary')),
    work_mode VARCHAR(30) NOT NULL DEFAULT 'onsite'
        CHECK (work_mode IN ('onsite', 'remote', 'hybrid')),
    description TEXT NOT NULL,
    requirements TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'open', 'paused', 'closed', 'archived')),
    opened_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_offer_id UUID NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    cv_file_id UUID REFERENCES cv_files(id) ON DELETE SET NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'recruiter'
        CHECK (source IN ('recruiter', 'candidate_portal', 'linkedin_csv', 'referral', 'other')),
    status VARCHAR(40) NOT NULL DEFAULT 'submitted'
        CHECK (status IN ('submitted', 'screening', 'shortlisted', 'interviewing', 'offer', 'hired', 'rejected', 'withdrawn')),
    current_stage VARCHAR(80),
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT applications_candidate_job_unique UNIQUE (candidate_id, job_offer_id)
);

CREATE TABLE ai_matching_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_offer_id UUID NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    score NUMERIC(5, 4) NOT NULL CHECK (score BETWEEN 0 AND 1),
    rank_position INTEGER CHECK (rank_position IS NULL OR rank_position > 0),
    explanation TEXT,
    matched_skills JSONB,
    missing_skills JSONB,
    embedding_version VARCHAR(100),
    status VARCHAR(30) NOT NULL DEFAULT 'generated'
        CHECK (status IN ('generated', 'reviewed', 'accepted', 'dismissed')),
    reviewed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    scheduled_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    interviewer_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    interview_type VARCHAR(40) NOT NULL DEFAULT 'screening'
        CHECK (interview_type IN ('screening', 'technical', 'hr', 'manager', 'final')),
    status VARCHAR(30) NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'completed', 'cancelled', 'rescheduled', 'no_show')),
    scheduled_start_at TIMESTAMPTZ NOT NULL,
    scheduled_end_at TIMESTAMPTZ,
    meeting_url TEXT,
    location VARCHAR(180),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (scheduled_end_at IS NULL OR scheduled_end_at > scheduled_start_at)
);

CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE,
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    evaluator_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating IS NULL OR rating BETWEEN 1 AND 5),
    recommendation VARCHAR(30) NOT NULL DEFAULT 'hold'
        CHECK (recommendation IN ('strong_yes', 'yes', 'hold', 'no', 'strong_no')),
    strengths TEXT,
    weaknesses TEXT,
    notes TEXT,
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE candidate_timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL
        CHECK (event_type IN ('note', 'email', 'call', 'status_change', 'cv_uploaded', 'interview_scheduled', 'evaluation_added', 'ai_match_generated', 'portal_update')),
    title VARCHAR(180) NOT NULL,
    description TEXT,
    metadata JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_status ON users (status);

CREATE INDEX idx_candidates_name ON candidates (last_name, first_name);
CREATE INDEX idx_candidates_email ON candidates (email);
CREATE INDEX idx_candidates_status ON candidates (status);
CREATE INDEX idx_candidates_source ON candidates (source);
CREATE INDEX idx_candidates_owner_user_id ON candidates (owner_user_id);

CREATE INDEX idx_cv_files_candidate_id ON cv_files (candidate_id);
CREATE INDEX idx_cv_files_uploaded_by_user_id ON cv_files (uploaded_by_user_id);
CREATE INDEX idx_cv_files_parsing_status ON cv_files (parsing_status);
CREATE INDEX idx_cv_files_checksum_sha256 ON cv_files (checksum_sha256);

CREATE INDEX idx_extracted_cv_data_candidate_id ON extracted_cv_data (candidate_id);
CREATE INDEX idx_extracted_cv_data_status ON extracted_cv_data (status);
CREATE INDEX idx_extracted_cv_data_parsed_json ON extracted_cv_data USING GIN (parsed_json);

CREATE INDEX idx_skills_normalized_name ON skills (normalized_name);
CREATE INDEX idx_skills_category ON skills (category);

CREATE INDEX idx_candidate_skills_candidate_id ON candidate_skills (candidate_id);
CREATE INDEX idx_candidate_skills_skill_id ON candidate_skills (skill_id);
CREATE INDEX idx_candidate_skills_source ON candidate_skills (source);

CREATE INDEX idx_experiences_candidate_id ON experiences (candidate_id);
CREATE INDEX idx_experiences_company_name ON experiences (company_name);
CREATE INDEX idx_experiences_job_title ON experiences (job_title);

CREATE INDEX idx_education_candidate_id ON education (candidate_id);
CREATE INDEX idx_education_institution_name ON education (institution_name);

CREATE INDEX idx_job_offers_status ON job_offers (status);
CREATE INDEX idx_job_offers_created_by_user_id ON job_offers (created_by_user_id);
CREATE INDEX idx_job_offers_title ON job_offers (title);

CREATE INDEX idx_applications_candidate_id ON applications (candidate_id);
CREATE INDEX idx_applications_job_offer_id ON applications (job_offer_id);
CREATE INDEX idx_applications_status ON applications (status);
CREATE INDEX idx_applications_applied_at ON applications (applied_at);

CREATE INDEX idx_ai_matching_results_application_id ON ai_matching_results (application_id);
CREATE INDEX idx_ai_matching_results_candidate_job ON ai_matching_results (candidate_id, job_offer_id);
CREATE INDEX idx_ai_matching_results_score ON ai_matching_results (score DESC);
CREATE INDEX idx_ai_matching_results_status ON ai_matching_results (status);

CREATE INDEX idx_interviews_application_id ON interviews (application_id);
CREATE INDEX idx_interviews_candidate_id ON interviews (candidate_id);
CREATE INDEX idx_interviews_interviewer_user_id ON interviews (interviewer_user_id);
CREATE INDEX idx_interviews_status ON interviews (status);
CREATE INDEX idx_interviews_scheduled_start_at ON interviews (scheduled_start_at);

CREATE INDEX idx_evaluations_interview_id ON evaluations (interview_id);
CREATE INDEX idx_evaluations_application_id ON evaluations (application_id);
CREATE INDEX idx_evaluations_evaluator_user_id ON evaluations (evaluator_user_id);
CREATE INDEX idx_evaluations_recommendation ON evaluations (recommendation);

CREATE INDEX idx_candidate_timeline_events_candidate_id ON candidate_timeline_events (candidate_id);
CREATE INDEX idx_candidate_timeline_events_application_id ON candidate_timeline_events (application_id);
CREATE INDEX idx_candidate_timeline_events_event_type ON candidate_timeline_events (event_type);
CREATE INDEX idx_candidate_timeline_events_occurred_at ON candidate_timeline_events (occurred_at DESC);

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_candidates_updated_at
BEFORE UPDATE ON candidates
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_cv_files_updated_at
BEFORE UPDATE ON cv_files
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_extracted_cv_data_updated_at
BEFORE UPDATE ON extracted_cv_data
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_skills_updated_at
BEFORE UPDATE ON skills
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_candidate_skills_updated_at
BEFORE UPDATE ON candidate_skills
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_experiences_updated_at
BEFORE UPDATE ON experiences
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_education_updated_at
BEFORE UPDATE ON education
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_job_offers_updated_at
BEFORE UPDATE ON job_offers
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_applications_updated_at
BEFORE UPDATE ON applications
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_ai_matching_results_updated_at
BEFORE UPDATE ON ai_matching_results
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_interviews_updated_at
BEFORE UPDATE ON interviews
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_evaluations_updated_at
BEFORE UPDATE ON evaluations
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_candidate_timeline_events_updated_at
BEFORE UPDATE ON candidate_timeline_events
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
