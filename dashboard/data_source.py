"""Select the dashboard data source without changing production database behavior."""

import os


DASHBOARD_MODE = os.getenv("PROJECT_E_DASHBOARD_MODE", "database").strip().lower()

if DASHBOARD_MODE == "demo":
    try:
        from demo_backend import (  # noqa: F401
            get_human_review_history, get_latest_reports, get_report_archive,
            get_report_archive_count, get_report_html, reset_demo_state,
            set_human_review_status, test_connection,
        )
    except ModuleNotFoundError:  # Supports module-based test runners.
        from dashboard.demo_backend import (  # noqa: F401
            get_human_review_history, get_latest_reports, get_report_archive,
            get_report_archive_count, get_report_html, reset_demo_state,
            set_human_review_status, test_connection,
        )
elif DASHBOARD_MODE == "database":
    try:
        from db import (  # noqa: F401
            get_human_review_history, get_latest_reports, get_report_archive,
            get_report_archive_count, get_report_html, set_human_review_status,
            test_connection,
        )
    except ModuleNotFoundError:  # Supports module-based test runners.
        from dashboard.db import (  # noqa: F401
            get_human_review_history, get_latest_reports, get_report_archive,
            get_report_archive_count, get_report_html, set_human_review_status,
            test_connection,
        )

    def reset_demo_state() -> None:
        """No-op kept so the UI can expose a demo-only reset control safely."""

else:
    raise RuntimeError(
        "PROJECT_E_DASHBOARD_MODE must be either 'database' (the default) or 'demo'."
    )


IS_DEMO_MODE = DASHBOARD_MODE == "demo"
