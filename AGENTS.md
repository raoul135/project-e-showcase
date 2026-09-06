# Repository Instructions

## Git and Change Management

1. One logical, meaningful change = one Git commit.

2. Normal workflow: change → validate/test → inspect Git diff → verify no unrelated files → commit → report commit hash.

3. Do not commit failing changes, half-finished work, temporary debug edits, unrelated files, or backup/snapshot files unless explicitly approved.

4. Before every commit, run relevant tests/validation, run `git diff --check`, inspect the files being committed, confirm no secrets or credentials are included, and confirm the change is limited to the intended logical task.

5. After every successful meaningful change, create a Git commit automatically once validation passes using a concise descriptive message, then report the commit hash, files included, tests/validation performed, and remaining working-tree changes.

6. Never push automatically. A push requires explicit user instruction.

7. Never combine unrelated work into one commit.

8. If unrelated pre-existing changes are present, leave them untouched, do not stage them, and clearly report them.

9. n8n changes made only inside the UI are not preserved by Git. When a live workflow is intentionally changed, update and validate its repository workflow export before considering the change complete or committing it.

10. If repository workflow JSON and the live n8n workflow appear different, warn explicitly and do not silently overwrite either side.

11. Git/code maintenance must not modify production PostgreSQL data, Qdrant data, credentials, or live service state unless explicitly requested.

12. Each commit should represent a working checkpoint that can reasonably be reverted independently.

13. Before starting a new logical task, confirm the previous successful task has been committed unless explicitly told not to commit.

14. Explicit instructions to not commit, not push, review only, or show proposed changes first override the automatic commit rule.

15. Never commit obvious backup files such as `(last)`, `.bak`, or temporary copies unless explicitly approved.
