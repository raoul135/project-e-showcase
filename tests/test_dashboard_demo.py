"""Contracts for the self-contained public dashboard demo."""

from __future__ import annotations

import importlib
import json
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard"
EXAMPLES = ROOT / "examples"
sys.path.insert(0, str(DASHBOARD))


class DashboardDemoTests(unittest.TestCase):
    def test_fixture_files_are_valid_and_privacy_safe(self):
        for name in (
            "fictional-opportunity.json",
            "fictional-evidence.json",
            "fictional-report.json",
            "fictional-workflow-output.json",
        ):
            payload = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
            self.assertTrue(payload["fictional_data_only"], name)

        report = json.loads((EXAMPLES / "fictional-report.json").read_text(encoding="utf-8"))
        self.assertEqual("strong_apply", report["recommendation"]["data"]["final_recommendation"])
        self.assertTrue(report["proposal_audit"]["data"]["passed"])
        self.assertEqual(6, len(report["proposal_audit"]["data"]["checks"]))
        self.assertEqual(4, len(report["retrieved_evidence"]["data"]["items"]))

        fixture_text = "\n".join(path.read_text(encoding="utf-8") for path in EXAMPLES.glob("fictional-*"))
        for forbidden in ("@", "api_key", "postgres://", "upwork.com", "gmail.com", "qdrant.io"):
            self.assertNotIn(forbidden, fixture_text.lower(), forbidden)

    def test_demo_repository_works_without_database_or_network(self):
        import demo_backend

        state = {}
        repository = demo_backend.DemoRepository(state)
        reports = repository.latest_reports()
        self.assertEqual(1, len(reports))
        self.assertEqual("DEMO-OPP-001", reports.iloc[0]["job_id"])
        self.assertIn("strong_apply", reports.iloc[0]["report_json"])
        self.assertTrue(repository.set_status("DEMO-OPP-001", "approved"))
        self.assertEqual("approved", repository.latest_reports().iloc[0]["human_review_status"])
        self.assertEqual(1, len(repository.history("DEMO-OPP-001")))
        self.assertFalse(repository.set_status("DEMO-OPP-001", "not-a-status"))
        self.assertFalse(repository.set_status("other", "approved"))
        repository.reset()
        self.assertEqual("unreviewed", repository.latest_reports().iloc[0]["human_review_status"])

    def test_data_source_selects_demo_without_importing_database_backend(self):
        previous = os.environ.get("PROJECT_E_DASHBOARD_MODE")
        try:
            os.environ["PROJECT_E_DASHBOARD_MODE"] = "demo"
            sys.modules.pop("data_source", None)
            module = importlib.import_module("data_source")
            self.assertTrue(module.IS_DEMO_MODE)
            self.assertEqual("demo", module.DASHBOARD_MODE)
            self.assertEqual("demo_backend", module.test_connection.__module__)
        finally:
            if previous is None:
                os.environ.pop("PROJECT_E_DASHBOARD_MODE", None)
            else:
                os.environ["PROJECT_E_DASHBOARD_MODE"] = previous
            sys.modules.pop("data_source", None)

    def test_demo_launcher_selects_fixture_mode(self):
        script = (ROOT / "tools" / "run_dashboard_demo.ps1").read_text(encoding="utf-8")
        self.assertIn("PROJECT_E_DASHBOARD_MODE = 'demo'", script)
        self.assertIn("streamlit run", script)

    def test_dashboard_renders_the_demo_review_workspace(self):
        previous = os.environ.get("PROJECT_E_DASHBOARD_MODE")
        try:
            os.environ["PROJECT_E_DASHBOARD_MODE"] = "demo"
            from streamlit.testing.v1 import AppTest

            app = AppTest.from_file(str(ROOT / "dashboard" / "app.py")).run(timeout=20)
            self.assertEqual([], list(app.exception))
            self.assertGreaterEqual(len(app.button), 1)
            app.button[-1].click().run(timeout=20)  # The sole inbox card's review action.
            self.assertEqual([], list(app.exception))
            self.assertEqual(5, len(app.tabs))

            source = (ROOT / "dashboard" / "app.py").read_text(encoding="utf-8")
            self.assertIn("PASSED — 6/6 checks", source)
            self.assertIn("0 unsupported claims", source)
            self.assertIn("Copy Proposal", source)
            self.assertIn("Download report HTML", source)
        finally:
            if previous is None:
                os.environ.pop("PROJECT_E_DASHBOARD_MODE", None)
            else:
                os.environ["PROJECT_E_DASHBOARD_MODE"] = previous


if __name__ == "__main__":
    unittest.main()
