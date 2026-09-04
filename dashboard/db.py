import os
from contextlib import contextmanager
from typing import Generator

import pandas as pd
import psycopg2
from psycopg2.extensions import connection
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


DB_CONFIG = {
    "host": os.getenv("PROJECT_E_DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("PROJECT_E_DB_PORT", "5432")),
    "database": os.getenv("PROJECT_E_DB_NAME", "postgres"),
    "user": os.getenv("PROJECT_E_DB_USER", "n8n"),
    "password": os.getenv("PROJECT_E_DB_PASSWORD", ""),
    "connect_timeout": 5,
}


ALLOWED_REVIEW_STATUSES = {
    "unreviewed",
    "reviewing",
    "approved",
    "applied",
    "skipped",
}


def require_password() -> None:
    if not DB_CONFIG["password"]:
        raise RuntimeError(
            "PROJECT_E_DB_PASSWORD is not configured. "
            "Set it as a Windows environment variable before starting Streamlit."
        )


def get_connection() -> connection:
    require_password()
    return psycopg2.connect(**DB_CONFIG)


def get_engine():
    require_password()

    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"connect_timeout": DB_CONFIG["connect_timeout"]},
    )


@contextmanager
def database_connection() -> Generator[connection, None, None]:
    connection_object = get_connection()
    try:
        yield connection_object
    finally:
        connection_object.close()


def test_connection() -> bool:
    try:
        with database_connection() as connection_object:
            with connection_object.cursor() as cursor:
                cursor.execute("SELECT 1;")
                return cursor.fetchone() == (1,)
    except psycopg2.Error:
        return False


def get_latest_reports() -> pd.DataFrame:
    """Return exactly one latest report for every job in the active workflow."""
    query = text(
        """
        WITH ranked_reports AS (
            SELECT
                r.*,
                ROW_NUMBER() OVER (
                    PARTITION BY r.job_id
                    ORDER BY r.created_at DESC, r.id DESC
                ) AS latest_rank,
                ROW_NUMBER() OVER (
                    PARTITION BY r.job_id
                    ORDER BY r.created_at ASC, r.id ASC
                ) AS version_number,
                COUNT(*) OVER (
                    PARTITION BY r.job_id
                ) AS versions_for_job
            FROM upwork.upwork_job_reports AS r
        )
        SELECT
            r.id,
            r.job_id,
            COALESCE(NULLIF(j.title, ''), 'Untitled Upwork opportunity') AS title,
            r.created_at,
            r.report_json,

            j.job_type,
            j.url,
            j.canonical_url,
            j.fixed_price,
            j.hourly_min,
            j.hourly_max,
            j.hourly_raw,
            j.posted_time,
            j.client_rating,
            j.client_hires,
            j.proposals,
            j.client_country,
            j.experience_level,
            j.location_country,
            j.location_worldwide,

            COALESCE(hr.review_status, 'unreviewed') AS human_review_status,
            hr.reviewed_at AS human_reviewed_at,
            hr.updated_at AS human_review_updated_at,

            r.version_number,
            r.versions_for_job

        FROM ranked_reports AS r

        LEFT JOIN upwork.upwork_jobs AS j
            ON j.job_id = r.job_id

        LEFT JOIN upwork.upwork_job_reviews AS hr
            ON hr.job_id = r.job_id

        WHERE r.latest_rank = 1
        ORDER BY r.created_at DESC, r.id DESC;
        """
    )

    engine = get_engine()
    try:
        with engine.connect() as connection_object:
            return pd.read_sql_query(query, connection_object)
    finally:
        engine.dispose()


def get_report_archive(page: int = 1, page_size: int = 25) -> pd.DataFrame:
    """Return one complete, ordered page of saved report versions."""
    safe_page = max(1, int(page))
    safe_page_size = max(1, min(int(page_size), 100))
    offset = (safe_page - 1) * safe_page_size

    query = text(
        """
        SELECT
            r.id,
            r.job_id,
            COALESCE(NULLIF(j.title, ''), 'Untitled Upwork opportunity') AS title,
            r.created_at,
            r.report_json,
            j.job_type,
            j.url,
            j.canonical_url,
            j.fixed_price,
            j.hourly_min,
            j.hourly_max,
            j.hourly_raw,
            j.posted_time,
            j.client_rating,
            j.client_hires,
            j.proposals,
            j.client_country,
            j.experience_level,
            j.location_country,
            j.location_worldwide,
            COALESCE(hr.review_status, 'unreviewed') AS human_review_status,
            hr.reviewed_at AS human_reviewed_at,
            hr.updated_at AS human_review_updated_at,
            ROW_NUMBER() OVER (
                PARTITION BY r.job_id
                ORDER BY r.created_at ASC, r.id ASC
            ) AS version_number,
            COUNT(*) OVER (
                PARTITION BY r.job_id
            ) AS versions_for_job
        FROM upwork.upwork_job_reports AS r
        LEFT JOIN upwork.upwork_jobs AS j ON j.job_id = r.job_id
        LEFT JOIN upwork.upwork_job_reviews AS hr ON hr.job_id = r.job_id
        ORDER BY r.created_at DESC, r.id DESC
        LIMIT :limit OFFSET :offset;
        """
    )

    engine = get_engine()
    try:
        with engine.connect() as connection_object:
            return pd.read_sql_query(
                query,
                connection_object,
                params={"limit": safe_page_size, "offset": offset},
            )
    finally:
        engine.dispose()


def get_report_archive_count() -> int:
    """Return the number of all saved report versions."""
    query = text("SELECT COUNT(*) FROM upwork.upwork_job_reports;")
    engine = get_engine()
    try:
        with engine.connect() as connection_object:
            value = connection_object.execute(query).scalar_one()
            return int(value)
    finally:
        engine.dispose()


def get_report_html(report_id: int) -> str:
    with database_connection() as connection_object:
        with connection_object.cursor() as cursor:
            cursor.execute(
                """
                SELECT html_report
                FROM upwork.upwork_job_reports
                WHERE id = %s;
                """,
                (int(report_id),),
            )
            row = cursor.fetchone()

    return row[0] if row and row[0] else ""


def set_human_review_status(job_id: str, status: str) -> None:
    """
    Update the current human decision and permanently log every real status change.
    """
    if status not in ALLOWED_REVIEW_STATUSES:
        raise ValueError(f"Unsupported review status: {status}")

    with database_connection() as connection_object:
        with connection_object.cursor() as cursor:
            # Lock/read the current value so history is reliable.
            cursor.execute(
                """
                SELECT review_status
                FROM upwork.upwork_job_reviews
                WHERE job_id = %s
                FOR UPDATE;
                """,
                (str(job_id),),
            )
            row = cursor.fetchone()

            previous_status = row[0] if row else "unreviewed"

            # Do not create duplicate history rows if user clicks the same state again.
            if previous_status == status:
                return

            cursor.execute(
                """
                INSERT INTO upwork.upwork_job_review_history (
                    job_id,
                    previous_status,
                    new_status,
                    changed_at
                )
                VALUES (%s, %s, %s, NOW());
                """,
                (
                    str(job_id),
                    previous_status,
                    status,
                ),
            )

            cursor.execute(
                """
                INSERT INTO upwork.upwork_job_reviews (
                    job_id,
                    review_status,
                    reviewed_at,
                    updated_at
                )
                VALUES (
                    %s,
                    %s,
                    CASE
                        WHEN %s IN ('approved', 'applied', 'skipped') THEN NOW()
                        ELSE NULL
                    END,
                    NOW()
                )
                ON CONFLICT (job_id)
                DO UPDATE SET
                    review_status = EXCLUDED.review_status,
                    reviewed_at = CASE
                        WHEN EXCLUDED.review_status IN ('approved', 'applied', 'skipped')
                            THEN NOW()
                        ELSE NULL
                    END,
                    updated_at = NOW();
                """,
                (
                    str(job_id),
                    status,
                    status,
                ),
            )

        connection_object.commit()


def get_human_review_history(job_id: str) -> pd.DataFrame:
    """
    Return the complete human decision history for one job, newest first.
    """
    query = text(
        """
        SELECT
            id,
            job_id,
            previous_status,
            new_status,
            changed_at
        FROM upwork.upwork_job_review_history
        WHERE job_id = :job_id
        ORDER BY changed_at DESC, id DESC;
        """
    )

    engine = get_engine()
    try:
        with engine.connect() as connection_object:
            return pd.read_sql_query(
                query,
                connection_object,
                params={"job_id": str(job_id)},
            )
    finally:
        engine.dispose()
