# Project-E local-model and RAG evaluation V2

Import `project-e-local-model-rag-quality-evaluation-v2.json` into n8n 2.31.7. It is inactive and uses a Manual Trigger. It reads Qdrant only and does not call subworkflows, PostgreSQL, or any Project-E operational workflow.

Before the first run, select these existing credentials manually after import:

- `LM Studio API` — **Header Auth** credential, on **Create Dense Embedding** and **Local Model Answer**. Do not add a token to the workflow export.
- `OpenAI account` — **OpenAI API** credential, on **OpenAI Baseline Answer** and **OpenAI Comparison Judge**.

The evaluation uses `http://ai-qdrant:6333`, `professional_knowledge_base`, named dense vector `text-embedding-bge-m3`, sparse vector `bm25`, and Qdrant RRF with two prefetch branches. RRF scores are rank-fusion scores, not similarity percentages.

`Prepare Evaluation Cases` has a `repeat_count` of 3 and temperature `0.1`. Change these only for a deliberate experiment. The 20 complete human-readable cases are also stored in `evaluation-cases.v2.json`; they are never sent to Qdrant for ingestion.

Each normal execution emits one per-attempt report item. Download the execution output as JSON or CSV for separate storage. A release decision requires aggregating all repeated runs: 99% JSON validity and schema compliance, 100% job-ID and citation validity, zero unsupported claims, Hit Rate@5 of at least 90%, and 100% negative-boundary compliance. Any failed criterion makes the stage `NOT_LOCAL_READY`; meet the safety gates but require prompt adjustments gives `LOCAL_READY_WITH_PROMPT_CHANGES`; only all gates and stage simulations passing allow `LOCAL_READY`.

Import `project-e-local-model-stage-simulations-v2.json` alongside the main evaluator to run the six local-only stage simulations. The fixtures cover Stage 2, 3.5, 3C, 3.6, 4A, and 4B. They use only `eval-job-001` and fictional evidence, preserve no production identifiers, and never call a subworkflow or database.

The original attached evaluator had three material flaws: it submitted only one dense prefetch while asking Qdrant for RRF, asked an LLM to estimate deterministic precision/recall, and converted invalid judge JSON into a normal zero-score result. This V2 instead calculates retriever metrics in JavaScript and records invalid answer output as a failure.
