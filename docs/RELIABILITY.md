# Reliability and failure hardening

The most useful engineering evidence is often the failure that became a guardrail.

| Observed failure | Root cause | Engineering fix | Regression protection |
| --- | --- | --- | --- |
| Large local-model context fell back unexpectedly | Context and output configuration exceeded the local runtime envelope | Bound stage context and correct model configuration | Stage simulations and fallback routing tests |
| Stage 4B output stopped at an earlier ceiling | Auditor completion budget was too small | Raise the appropriate output budget and keep the audit contract bounded | Fallback and output-contract tests |
| Unsupported high-risk positioning survived into proposal text | An upstream warning was advisory instead of binding | Propagate unresolved critical warnings as explicit downstream constraints | Production regression fixtures for unsupported real-time and expert claims |
| HTML comparison rejected a valid proposal containing apostrophes | Raw text was compared with escaped rendered HTML | Compare through the same escaping representation used for persistence | Stage 5 failure-path tests |
| `$750` broke generated SQL | n8n interpreted a quoted dollar-number as a positional parameter | Render dollar-number strings as concatenated SQL fragments while preserving apostrophes and NULL | SQL-generation tests for `$1`, `$750`, `$1800`, apostrophes and NULL |

The pattern is consistent: observed behavior becomes a small contract, the contract is tested, and the production path keeps a deterministic gate around model discretion.

## Deployment safety

Source/live comparison, backups, identity checks, credential-reference checks, workflow-call checks and final NO-OP verification are part of the managed deployment process. Public examples deliberately omit the live IDs and state required to operate that process.
