-- 06_add_project_e_logical_run_claims.sql
-- BE-02C: prevent concurrent processing of the same Project-E logical run.

CREATE TABLE IF NOT EXISTS upwork.project_e_logical_run_claims (
    job_id text NOT NULL,
    analysis_input_hash text NOT NULL,
    claim_owner text NOT NULL,
    claimed_at timestamptz NOT NULL DEFAULT NOW(),
    lease_expires_at timestamptz NOT NULL,
    completed_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_project_e_logical_run_claims
        PRIMARY KEY (job_id, analysis_input_hash),

    CONSTRAINT fk_project_e_logical_run_claims_job
        FOREIGN KEY (job_id)
        REFERENCES upwork.upwork_jobs (job_id)
        ON DELETE CASCADE,

    CONSTRAINT ck_project_e_logical_run_claims_hash
        CHECK (length(btrim(analysis_input_hash)) > 0),

    CONSTRAINT ck_project_e_logical_run_claims_owner
        CHECK (length(btrim(claim_owner)) > 0),

    CONSTRAINT ck_project_e_logical_run_claims_lease
        CHECK (lease_expires_at > claimed_at),

    CONSTRAINT ck_project_e_logical_run_claims_completion
        CHECK (completed_at IS NULL OR completed_at >= claimed_at)
);

CREATE INDEX IF NOT EXISTS ix_project_e_logical_run_claims_active_lease
    ON upwork.project_e_logical_run_claims (lease_expires_at)
    WHERE completed_at IS NULL;

COMMENT ON TABLE upwork.project_e_logical_run_claims IS
    'PostgreSQL-backed leases for Project-E logical runs keyed by job_id and analysis_input_hash.';

COMMENT ON COLUMN upwork.project_e_logical_run_claims.claim_owner IS
    'Traceable n8n execution owner that acquired or reclaimed the logical-run lease.';

COMMENT ON COLUMN upwork.project_e_logical_run_claims.lease_expires_at IS
    'Abandoned claims become reclaimable after this timestamp.';
