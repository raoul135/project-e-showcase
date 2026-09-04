# Ten-workflow map

The names below describe the production architecture. Seven complete production
exports are intentionally not included in this public showcase.

| Order | Stage | Responsibility | Public artifact |
|---:|---|---|---|
| 1 | Email intake | Select a notification, extract a job link, invoke the job adapter, validate and store the job, and acquire a logical-run claim. | Documentation only |
| 2 | Job intelligence | Read the stored job, produce structured model analysis, validate it, persist it, and defer completion until all descendants succeed. | Documentation only |
| 3 | Deterministic opportunity scoring | Calculate repeatable opportunity scores and construct a briefing. | Sanitized representative export |
| 4 | Hybrid evidence retrieval | Generate six evidence-query families, embed them, run dense/sparse retrieval with reciprocal-rank fusion, rerank results, and create a bounded evidence package. | Sanitized representative export |
| 5 | Deterministic personal-fit scoring | Score evidence-backed personal fit without asking a model to invent experience. | Documentation only |
| 6 | Final decision | Combine upstream scores and model judgment while enforcing the authoritative job identity. | Documentation only |
| 7 | Proposal strategy | Generate and validate the proposed positioning, required points, boundaries, and questions. | Documentation only |
| 8 | Proposal writer | Draft the proposal from validated strategy and evidence, then send it to the auditor. | Documentation only |
| 9 | Proposal auditor | Check the proposal for unsupported claims, omissions, contradictions, and safety issues. | Sanitized representative export |
| 10 | Report and delivery | Build deterministic report data and HTML, validate the report, persist by logical-run key, and deliver it. | Documentation only |

## Production connections

```text
Email intake
  -> Job intelligence
  -> Deterministic opportunity scoring
  -> Hybrid evidence retrieval
  -> Deterministic personal-fit scoring
  -> Final decision
  -> Proposal strategy
  -> Proposal writer
       -> Proposal auditor
       -> Report and delivery
```

The published representative files have no production workflow IDs. Downstream
call nodes are disabled and contain `CONFIGURE_DOWNSTREAM_WORKFLOW_ID`. The
example mapping file is illustrative only and contains no live identifiers.

## Evidence retrieval contract

The production-derived representative demonstrates six query groups:
technical, capability, engineering, business problem, similar project, and
confidence boundary. It was designed around a named dense vector and BM25 sparse
vector, candidate normalization, conservative reranking, and a bounded final
evidence set. Public endpoints, model names, credential references, and
collection names are placeholders.
