-- 04_create_upwork_job_reports.sql
-- Project-E Stage 5 HTML Reports

CREATE TABLE IF NOT EXISTS upwork.upwork_job_reports (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL,
    html_report TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    report_json JSONB
);

-- Repair databases created by the original version of this setup file, where
-- the workflow-added structured report payload was an undocumented live step.
ALTER TABLE upwork.upwork_job_reports
ADD COLUMN IF NOT EXISTS report_json JSONB;

CREATE INDEX IF NOT EXISTS idx_upwork_job_reports_job_id
ON upwork.upwork_job_reports (job_id);

CREATE INDEX IF NOT EXISTS idx_upwork_job_reports_created_at
ON upwork.upwork_job_reports (created_at DESC);
