# Security and privacy boundaries

## Excluded sensitive material

This showcase intentionally excludes credentials, credential references,
workflow/version IDs, deployment state, execution history, workflow backups,
browser profiles, cookies, OAuth data, real notifications, scraped job data,
customer details, generated proposals, and populated knowledge-base content.

## Trust boundaries

- The dashboard is designed as a trusted local operator interface and has no
  application-level login or role model.
- The safe mock job-reader binds to localhost in the documented command and
  makes no outbound requests.
- The production architecture depends on third-party credentials, but none are
  provided here.
- Model and job-derived HTML must be treated as untrusted content before any
  internet-facing dashboard deployment.
- Production SQL builders should be migrated to parameterized queries before a
  multi-user commercial deployment.

## Public-repository checks

Before publishing any revision:

1. Parse every workflow JSON file.
2. Syntax-check every embedded JavaScript field.
3. Assert that credentials, pinned data, instance metadata, and live IDs are
   absent.
4. Scan tracked files for emails, keys, tokens, password-bearing URLs, private
   keys, absolute personal paths, and execution/customer data.
5. Review screenshots and media manually before adding them to `assets/`.
6. Use fictional data only in `examples/`.
