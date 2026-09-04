"""Safe public demonstration of the Project-E job-reader contract.

This module never opens a browser or contacts a remote job platform. It accepts
only the reserved ``example.invalid`` domain and returns fictional data.
"""

from dataclasses import asdict, dataclass
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


ALLOWED_DEMO_HOST = "jobs.example.invalid"


class ReadJobRequest(BaseModel):
    url: str


@dataclass(frozen=True)
class FictionalJob:
    job_id: str = "DEMO-001"
    url: str = "https://jobs.example.invalid/jobs/demo-001"
    title: str = "Fictional Inventory Automation"
    description: str = "Build a fictional inventory synchronization workflow."
    budget: int = 1200
    currency: str = "USD"


def validate_demo_url(value: str) -> str:
    candidate = value.strip()
    parsed = urlparse(candidate)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_DEMO_HOST:
        raise ValueError("Only fictional jobs.example.invalid URLs are accepted")
    if parsed.username or parsed.password or not parsed.path.startswith("/jobs/"):
        raise ValueError("The fictional job URL is malformed")
    return candidate


class MockJobProvider:
    """Deterministic provider used for documentation and local demonstrations."""

    def read(self, url: str) -> dict:
        validate_demo_url(url)
        job = FictionalJob(url=url)
        return {
            "success": True,
            "source": "fictional-showcase-provider",
            "job": asdict(job),
        }


app = FastAPI(title="Project-E Showcase Job Reader", version="1.0.0")
provider = MockJobProvider()


@app.get("/")
def health() -> dict:
    return {"status": "ok", "mode": "fictional-demo-only"}


@app.post("/read-job")
def read_job(request: ReadJobRequest) -> dict:
    try:
        return provider.read(request.url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
