# Limitations

- This repository is a curated showcase, not a turnkey product or full
  production source release.
- Seven production workflows are documented but intentionally omitted.
- Representative workflow credentials, IDs, service addresses, model names,
  collection names, pinned data, and downstream links are removed or disabled.
- The fictional demo does not call Gmail, Upwork, PostgreSQL, Qdrant, an
  embedding model, or a language model.
- The browser scraper and authenticated profile handling are not published.
- No Qdrant ingestion implementation is included because none existed in the
  inspected source repository.
- No Docker Compose or infrastructure definition is included because none
  existed in the inspected source repository.
- The dashboard requires PostgreSQL and is not a multi-user secured web product.
- The migration rebuild test requires an explicitly supplied empty disposable
  PostgreSQL database and otherwise skips.
- Model quality, extraction accuracy, latency, cost, accessibility, load,
  recovery, and commercial compliance are not certified by this showcase.
