# Project-E PostgreSQL setup

Apply every numbered SQL file in this directory in lexical order to an empty
PostgreSQL database. The migration role must be `n8n` (or a superuser must
create that role first), because the schema and core objects are owned by it.

Example from the repository root:

```powershell
Get-ChildItem database/migrations/*.sql | Sort-Object Name | ForEach-Object {
    psql -v ON_ERROR_STOP=1 -f $_.FullName
}
```

The numbered chain is the complete setup. The older dashboard migration files
under `dashboard/` are retained only as historical artifacts and are not an
additional setup step.

All setup files are safe to apply again to the schema produced by this chain.
They are forward migrations: they do not remove tables, columns, or data.
