-- 07_create_dashboard_review_tables.sql
-- Project-E dashboard human-review state and permanent audit history.

CREATE TABLE IF NOT EXISTS upwork.upwork_job_reviews (
    job_id TEXT PRIMARY KEY,
    review_status TEXT NOT NULL DEFAULT 'unreviewed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,

    CONSTRAINT upwork_job_reviews_status_check
        CHECK (
            review_status IN (
                'unreviewed',
                'reviewing',
                'approved',
                'applied',
                'skipped'
            )
        )
);

CREATE TABLE IF NOT EXISTS upwork.upwork_job_review_history (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL,
    previous_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT upwork_job_review_history_previous_status_check
        CHECK (
            previous_status IN (
                'unreviewed',
                'reviewing',
                'approved',
                'applied',
                'skipped'
            )
        ),

    CONSTRAINT upwork_job_review_history_new_status_check
        CHECK (
            new_status IN (
                'unreviewed',
                'reviewing',
                'approved',
                'applied',
                'skipped'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_upwork_job_review_history_job_id_changed_at
    ON upwork.upwork_job_review_history (job_id, changed_at DESC);
