# Configuration

## Environment variables

The repository includes `.env.example` with placeholders only. Never commit a
real `.env` file.

Dashboard variables:

- `PROJECT_E_DB_HOST`
- `PROJECT_E_DB_PORT`
- `PROJECT_E_DB_NAME`
- `PROJECT_E_DB_USER`
- `PROJECT_E_DB_PASSWORD`

Deployment-tool variable:

- `PROJECT_E_N8N_API_KEY`

Representative workflow settings documented for downstream configuration:

- `PROJECT_E_EMBEDDING_URL`
- `PROJECT_E_EMBEDDING_MODEL`
- `PROJECT_E_QDRANT_URL`
- `PROJECT_E_QDRANT_COLLECTION`
- `PROJECT_E_CHAT_MODEL`

The representative n8n JSON files intentionally use safe placeholders rather
than reading these variables directly. n8n environment-variable access depends
on deployment policy, so configure each node or use a reviewed import templater
for your own instance.

## Credentials

The representative exports contain no credential objects. A private deployment
would have to map these credential types in its own n8n instance:

- PostgreSQL
- OpenAI-compatible model provider
- HTTP-header authentication for a protected embedding service

Gmail credentials are part of the documented production architecture but are
not present in the three published representative workflows or fictional demo.

## Workflow IDs

Production workflow IDs, version IDs, instance metadata, and deployment state
are absent. Importing a workflow causes n8n to assign an ID. Update disabled
downstream calls only after reviewing the destination workflow in your own
instance.
