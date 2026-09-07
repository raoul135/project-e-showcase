# Engineering notes

Project-E is designed around explicit boundaries so that a model can be useful without becoming the system of record.

## Contracts before prose

Each stage receives structured JSON and returns a structured contract. Identity, job-derived requirements, evidence provenance, strategy obligations and validation findings travel with the payload. Code nodes normalize model output before downstream use; missing or malformed fields become visible failure states.

## Deterministic where it matters

Opportunity and personal-fit scores are computed from explicit components. Idempotency keys and logical-run claims prevent duplicate work. PostgreSQL migrations define jobs, analysis, reports and dashboard review state in an ordered chain. Stage 5 persistence uses a logical-run key so retries do not create an uncontrolled report fan-out.

## AI where interpretation helps

Models interpret job language, retrieve and rank relevant evidence, form strategy, draft a proposal and audit the draft. They do not decide whether an unsupported claim is safe merely because the wording sounds confident. Deterministic validators and upstream critical warnings remain authoritative.

## Deployment guardrails

The managed PowerShell deployment tool validates source JSON, workflow identity, credential references, workflow-call references and live version drift before Apply. It creates a pre-deployment backup, verifies the published active version afterward and updates deployment state. A final dry-run should report `NO-OP`.

## Public/private boundary

Representative n8n exports are sanitized and disabled. The fictional demo has no credentials or live calls. The public repository contains schemas and contracts, not browser profiles, execution history, private job data or deployment state.
