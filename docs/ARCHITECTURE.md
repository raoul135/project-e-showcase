# Architecture

## System boundary

The operational Project-E design joins six components:

1. n8n for orchestration and validation gates.
2. A job-reading adapter for turning a notification URL into structured data.
3. PostgreSQL schema `upwork` for jobs, analysis, reports, logical-run claims,
   and human-review state.
4. An embedding service and Qdrant for hybrid evidence retrieval.
5. Language-model calls for analysis, reranking, decision support, strategy,
   drafting, and auditing.
6. A Streamlit dashboard for human review and lifecycle state.

```text
Notification intake -> job adapter -> PostgreSQL
                           |
                           v
Analysis -> opportunity score -> evidence retrieval -> personal fit
   -> final decision -> strategy -> proposal -> audit -> report delivery
                                                   |
                                                   v
                                      PostgreSQL + review dashboard
```

The production graph consists of ten n8n workflows. Only three representative
exports are published here. `WORKFLOW_MAP.md` documents the complete graph.

## Reliability model

- Each stage validates its input before handing work downstream.
- Deterministic calculations are used where repeatability is more valuable than
  model discretion.
- Model output is parsed and checked against authoritative upstream identity.
- A logical-run claim prevents concurrent processing of the same job/input hash.
- The Stage 2 completion checkpoint is deferred until the downstream chain
  succeeds.
- Stage 5 report persistence uses a logical-run key for idempotency.
- Deployment tooling compares source and live definitions, credential
  references, workflow references, and recorded live versions before Apply.

## Published examples

- `deterministic-opportunity-scoring.json` demonstrates deterministic scoring
  and briefing construction.
- `hybrid-evidence-retrieval.json` demonstrates multi-query embedding, hybrid
  dense/sparse retrieval, reranking, and bounded evidence packaging.
- `proposal-auditor.json` demonstrates an isolated proposal-audit contract.
- `fictional-end-to-end-demo.json` is the only intentionally self-contained and
  immediately runnable workflow in this repository.
