"""BE-03 integration test for a disposable PostgreSQL database.

Set BE03_DATABASE_DSN to an empty disposable database. The test applies the
complete migration chain twice, compares it with the required Project-E schema,
and exercises the SQL contracts used by the workflows and dashboard.
"""

import os
import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIRECTORY = REPOSITORY_ROOT / "database" / "migrations"
sys.path.insert(0, str(REPOSITORY_ROOT / "dashboard"))

try:
    import psycopg2
except ImportError:  # pragma: no cover - environment-dependent integration test
    psycopg2 = None


EXPECTED_COLUMNS = {
    "project_e_logical_run_claims": {
        "job_id", "analysis_input_hash", "claim_owner", "claimed_at",
        "lease_expires_at", "completed_at", "updated_at",
    },
    "upwork_job_analysis": {
        "job_id", "analysis_version", "analysis_status", "analysis_json",
        "raw_ai_output", "created_at", "updated_at",
    },
    "upwork_job_reports": {
        "id", "job_id", "html_report", "created_at", "report_json",
        "logical_run_key",
    },
    "upwork_job_review_history": {
        "id", "job_id", "previous_status", "new_status", "changed_at",
    },
    "upwork_job_reviews": {
        "job_id", "review_status", "created_at", "updated_at", "reviewed_at",
    },
    "upwork_jobs": {
        "id", "job_id", "url", "canonical_url", "title", "category",
        "subcategory", "description", "summary", "job_type", "fixed_price",
        "hourly_min", "hourly_max", "hourly_raw", "duration", "weekly_hours",
        "experience_level", "posted_time", "contract_to_hire", "project_type",
        "location_raw", "location_country", "location_region",
        "location_worldwide", "location_remote", "client_country",
        "client_timezone_or_city", "client_payment_verified", "client_rating",
        "client_reviews_count", "client_total_spent", "client_hires",
        "client_active_hires", "client_total_hours", "client_company_size",
        "client_industry", "client_member_since", "proposals",
        "last_viewed_by_client", "interviewing", "invites_sent",
        "unanswered_invites", "last_activity", "skills", "requirement_tools",
        "requirement_languages", "requirement_frameworks", "requirement_models",
        "requirement_databases", "requirement_soft_skills",
        "requirement_certifications", "custom_instruction", "ai_allowed",
        "long_term", "urgent", "scraper_source", "scraper_version",
        "page_title", "text_length", "saved_file", "scraped_at",
        "validation_valid", "validation_errors", "raw_json", "created_at",
        "updated_at", "analysis_input_hash", "stage2_processed_hash",
        "stage2_processed_at", "stage2_analysis_version", "first_seen_at",
        "last_seen_at", "last_changed_at", "seen_count",
    },
}

EXPECTED_INDEXES = {
    "idx_upwork_job_reports_created_at",
    "idx_upwork_job_reports_job_id",
    "idx_upwork_job_review_history_job_id_changed_at",
    "ix_project_e_logical_run_claims_active_lease",
    "pk_project_e_logical_run_claims",
    "upwork_job_analysis_pkey",
    "upwork_job_reports_pkey",
    "upwork_job_review_history_pkey",
    "upwork_job_reviews_pkey",
    "upwork_jobs_job_id_key",
    "upwork_jobs_pkey",
    "uq_upwork_job_reports_logical_run_key",
}


class DatabaseRebuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if psycopg2 is None:
            raise unittest.SkipTest("psycopg2 is not installed")
        dsn = os.environ.get("BE03_DATABASE_DSN")
        if not dsn:
            raise unittest.SkipTest("BE03_DATABASE_DSN is not set")
        cls.connection = psycopg2.connect(dsn)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.connection.close()

    def apply_chain(self) -> None:
        migrations = sorted(MIGRATION_DIRECTORY.glob("[0-9][0-9]_*.sql"))
        self.assertEqual(
            [path.name[:2] for path in migrations],
            [f"{number:02d}" for number in range(1, 8)],
        )
        with self.connection.cursor() as cursor:
            for migration in migrations:
                cursor.execute(migration.read_text(encoding="utf-8"))
        self.connection.commit()

    def test_fresh_build_rerun_and_sql_compatibility(self) -> None:
        self.apply_chain()
        self.apply_chain()

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'upwork'
                ORDER BY table_name, ordinal_position
                """
            )
            actual_columns = {}
            for table_name, column_name in cursor.fetchall():
                actual_columns.setdefault(table_name, set()).add(column_name)
            self.assertEqual(actual_columns, EXPECTED_COLUMNS)

            cursor.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'upwork'
                """
            )
            self.assertEqual({row[0] for row in cursor.fetchall()}, EXPECTED_INDEXES)

            cursor.execute(
                """
                SELECT conname, pg_get_constraintdef(oid, true)
                FROM pg_constraint
                WHERE connamespace = 'upwork'::regnamespace
                  AND conname LIKE '%status_check'
                ORDER BY conname
                """
            )
            status_constraints = cursor.fetchall()
            self.assertEqual(len(status_constraints), 3)
            for _, definition in status_constraints:
                self.assertIn("'applied'::text", definition)

            # Minimal Stage 1, Stage 2, Stage 5, claim, and dashboard writes.
            cursor.execute(
                """
                INSERT INTO upwork.upwork_jobs (job_id, raw_json)
                VALUES ('be03-job', '{}'::jsonb)
                RETURNING job_id, analysis_input_hash, stage2_processed_hash
                """
            )
            self.assertEqual(cursor.fetchone()[0], "be03-job")
            cursor.execute(
                """
                INSERT INTO upwork.upwork_job_analysis
                    (job_id, analysis_version, analysis_json)
                VALUES ('be03-job', 'be03', '{}'::jsonb)
                """
            )
            cursor.execute(
                """
                INSERT INTO upwork.upwork_job_reports
                    (job_id, html_report, report_json, logical_run_key)
                VALUES ('be03-job', '<html></html>', '{}'::jsonb, 'be03-run')
                RETURNING id
                """
            )
            report_id = cursor.fetchone()[0]
            cursor.execute(
                """
                INSERT INTO upwork.project_e_logical_run_claims
                    (job_id, analysis_input_hash, claim_owner, lease_expires_at)
                VALUES ('be03-job', 'be03-hash', 'be03-owner', NOW() + INTERVAL '5 minutes')
                """
            )
            cursor.execute(
                """
                INSERT INTO upwork.upwork_job_reviews
                    (job_id, review_status, reviewed_at)
                VALUES ('be03-job', 'applied', NOW())
                """
            )
            cursor.execute(
                """
                INSERT INTO upwork.upwork_job_review_history
                    (job_id, previous_status, new_status)
                VALUES ('be03-job', 'approved', 'applied')
                """
            )

            # Core dashboard query shape, including every previously missing object.
            cursor.execute(
                """
                SELECT r.id, r.job_id, r.report_json, r.html_report,
                       COALESCE(hr.review_status, 'unreviewed'),
                       hr.reviewed_at, hr.updated_at
                FROM upwork.upwork_job_reports AS r
                LEFT JOIN upwork.upwork_jobs AS j ON j.job_id = r.job_id
                LEFT JOIN upwork.upwork_job_reviews AS hr ON hr.job_id = r.job_id
                WHERE r.id = %s
                """,
                (report_id,),
            )
            self.assertEqual(cursor.fetchone()[1], "be03-job")
            cursor.execute(
                """
                SELECT previous_status, new_status
                FROM upwork.upwork_job_review_history
                WHERE job_id = 'be03-job'
                """
            )
            self.assertEqual(cursor.fetchone(), ("approved", "applied"))

        self.connection.rollback()

        # Execute the current dashboard module's real SQL against the rebuild.
        parsed_dsn = urlparse(os.environ["BE03_DATABASE_DSN"])
        os.environ.update(
            {
                "PROJECT_E_DB_HOST": parsed_dsn.hostname or "127.0.0.1",
                "PROJECT_E_DB_PORT": str(parsed_dsn.port or 5432),
                "PROJECT_E_DB_NAME": parsed_dsn.path.lstrip("/"),
                "PROJECT_E_DB_USER": parsed_dsn.username or "n8n",
                "PROJECT_E_DB_PASSWORD": parsed_dsn.password or "",
            }
        )
        import db

        self.assertTrue(db.test_connection())
        self.assertTrue(db.get_latest_reports().empty)
        self.assertTrue(db.get_report_archive().empty)
        self.assertEqual(db.get_report_archive_count(), 0)
        self.assertTrue(db.get_human_review_history("missing").empty)


if __name__ == "__main__":
    unittest.main(verbosity=2)
