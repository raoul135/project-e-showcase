# Database setup

The canonical schema is defined by the seven SQL files in
`database/migrations/`. Apply them to an empty PostgreSQL database in lexical
order. They are designed to be rerunnable and forward-only.

The migrations assume role `n8n` exists or that a privileged migration operator
can provide it. This role name is an architectural default, not a credential.

The integration test in `tests/test_database_rebuild.py` is opt-in. Point
`BE03_DATABASE_DSN` only at an empty disposable database. The test applies the
chain twice and performs writes before rolling its test transaction back.

Do not point the rebuild test at a database containing required data.
