# RAG and data

Project-E uses different stores because the questions are different.

## Qdrant for evidence retrieval

Professional material is chunked and embedded with BGE-M3-compatible vectors. Dense similarity finds conceptual matches; sparse/BM25-style signals preserve exact technology and phrase matches. Reciprocal-rank fusion combines the rankings, then metadata and provenance constrain the evidence package passed to strategy and proposal stages.

Qdrant is the retrieval index, not the authoritative job record. It answers “which source passages may help?” and returns provenance so a reviewer can inspect the basis.

## PostgreSQL for state

PostgreSQL stores normalized jobs, analysis, reports, report versions, logical-run claims and dashboard review status. Ordered migrations make the schema reproducible. The database is the durable state machine for processing and human review; it is not used as a vector search substitute.

## Data movement

`job reader → n8n intake → PostgreSQL → analysis/scoring → Qdrant retrieval → strategy/writer/auditor → validation → report + dashboard state`.

Every boundary keeps identity and validation context. Public fixtures show the contracts without publishing populated private knowledge or production records.
