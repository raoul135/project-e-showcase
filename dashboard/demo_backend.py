"""In-memory, fixture-backed dashboard data source for the public demo mode.

It intentionally imports neither the production database module nor any external client.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, MutableMapping

import pandas as pd
import streamlit as st


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "examples"
STATUS_VALUES = {"unreviewed", "reviewing", "approved", "applied", "skipped"}
_STATUS_KEY = "project_e_demo_review_status"
_HISTORY_KEY = "project_e_demo_review_history"


def _load_json(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _opportunity() -> dict[str, Any]:
    return _load_json("fictional-opportunity.json")


def _report() -> dict[str, Any]:
    return _load_json("fictional-report.json")


def _html_report() -> str:
    return (FIXTURE_ROOT / "fictional-report.html").read_text(encoding="utf-8")


class DemoRepository:
    """Small testable repository whose state is confined to one Streamlit session."""

    def __init__(self, state: MutableMapping[str, Any]):
        self.state = state

    def _status(self) -> str:
        return str(self.state.get(_STATUS_KEY, _opportunity()["human_review_status"]))

    def latest_reports(self) -> pd.DataFrame:
        row = deepcopy(_opportunity())
        row["human_review_status"] = self._status()
        row["human_reviewed_at"] = None
        row["human_review_updated_at"] = None
        row["report_json"] = json.dumps(_report())
        return pd.DataFrame([row])

    def archive(self, offset: int = 0, limit: int = 50) -> pd.DataFrame:
        return self.latest_reports().iloc[offset : offset + limit].copy()

    def set_status(self, job_id: str, status: str) -> bool:
        if job_id != _opportunity()["job_id"] or status not in STATUS_VALUES:
            return False
        previous = self._status()
        if previous == status:
            return True
        self.state[_STATUS_KEY] = status
        history = list(self.state.get(_HISTORY_KEY, []))
        history.append(
            {
                "id": len(history) + 1,
                "job_id": job_id,
                "previous_status": previous,
                "new_status": status,
                "changed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.state[_HISTORY_KEY] = history
        return True

    def history(self, job_id: str) -> pd.DataFrame:
        rows = [item for item in self.state.get(_HISTORY_KEY, []) if item["job_id"] == job_id]
        return pd.DataFrame(
            rows,
            columns=["id", "job_id", "previous_status", "new_status", "changed_at"],
        )

    def reset(self) -> None:
        self.state.pop(_STATUS_KEY, None)
        self.state.pop(_HISTORY_KEY, None)


def _repository() -> DemoRepository:
    return DemoRepository(st.session_state)


def test_connection() -> bool:
    """Demo readiness means local fixture files loaded successfully; no network is used."""
    _opportunity()
    _report()
    _html_report()
    return True


def get_latest_reports() -> pd.DataFrame:
    return _repository().latest_reports()


def get_report_archive(offset: int = 0, limit: int = 50) -> pd.DataFrame:
    return _repository().archive(offset, limit)


def get_report_archive_count() -> int:
    return 1


def get_report_html(report_id: int) -> str:
    return _html_report() if int(report_id) == int(_opportunity()["id"]) else ""


def set_human_review_status(job_id: str, status: str) -> bool:
    return _repository().set_status(job_id, status)


def get_human_review_history(job_id: str) -> pd.DataFrame:
    return _repository().history(job_id)


def reset_demo_state() -> None:
    _repository().reset()
