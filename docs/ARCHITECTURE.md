# Architecture

![Architecture layers](../assets/diagrams/architecture-layers.svg)

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

The stage vocabulary is explicit: Stage 1 Intake, Stage 2 Job Intelligence,
Stage 3A Opportunity Assessment, Stage 3.5 Evidence Retrieval, Stage 3B
Personal Fit, Stage 3C Final Decision, Stage 3.6 Proposal Strategy, Stage 4A
Proposal Writer, Stage 4B Proposal Auditor and Stage 5 Report & Delivery.

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

![Pipeline](../assets/diagrams/project-e-pipeline.svg)

- `deterministic-opportunity-scoring.json` demonstrates deterministic scoring
  and briefing construction.
- `hybrid-evidence-retrieval.json` demonstrates multi-query embedding, hybrid
  dense/sparse retrieval, reranking, and bounded evidence packaging.
- `proposal-auditor.json` demonstrates an isolated proposal-audit contract.
- `fictional-end-to-end-demo.json` is the only intentionally self-contained and
  immediately runnable workflow in this repository.
