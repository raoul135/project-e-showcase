# Safe job-reader demonstration

This directory documents the contract used by Project-E without publishing or
running the private browser automation used by the operational prototype.

`api_contract.py` accepts only fictional `jobs.example.invalid` URLs and returns
deterministic sample data. It performs no outbound network requests and does not
use browser profiles, cookies, OAuth data, or third-party credentials.

Run locally after installing the requirements:

```powershell
uvicorn api_contract:app --app-dir services/job-reader --host 127.0.0.1 --port 8000
```

The production browser adapter is deliberately excluded. See
`docs/UPWORK_POLICY_NOTICE.md`.
