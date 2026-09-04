CREATE TABLE IF NOT EXISTS upwork.upwork_job_analysis
(
    job_id text NOT NULL,
    analysis_version text NOT NULL,
    analysis_status text NOT NULL DEFAULT 'analyzed',
    analysis_json jsonb NOT NULL,
    raw_ai_output text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT upwork_job_analysis_pkey PRIMARY KEY (job_id)
);

ALTER TABLE upwork.upwork_job_analysis
    OWNER TO n8n;
