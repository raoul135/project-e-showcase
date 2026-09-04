-- 05_add_stage5_report_logical_run_key.sql
-- BE-02A: make new Stage 5 report persistence idempotent per logical run.

ALTER TABLE upwork.upwork_job_reports
ADD COLUMN IF NOT EXISTS logical_run_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS uq_upwork_job_reports_logical_run_key
ON upwork.upwork_job_reports (logical_run_key);
