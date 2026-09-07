# Product tour

Project-E's Streamlit application is a local review control center. It is organized around the state of an opportunity rather than around model output.

## The navigation map

The sidebar exposes **Job Inbox**, **Approved**, **Reviewing**, **Applied**, **Skipped**, quick filters and **Report Archive**. Counts reflect the current review buckets. Search, sorting and pagination narrow the visible set without changing the underlying report.

![Dashboard](../assets/screenshots/01-main-opportunity-dashboard.png)

Each opportunity card surfaces the title, job identifier, recommendation, opportunity score, personal-fit score, warning state and the next review action. **Review job** opens the richer workspace; legacy or report-only records use **Open report**.

## Review workspace

The workspace is divided into summary, evidence, proposal, history and report tabs. The summary provides the decision context; evidence shows the material behind fit and positioning; proposal shows generated copy and checks; history shows recorded review actions; report opens the complete Stage 5 record.

![Evidence](../assets/screenshots/02-evidence-view.png)

The **Open Upwork Job** control is an external navigation aid. It does not submit an application. The public system stops at a human-controlled boundary.

## State transitions

| Control | What changes | Where the job appears next | Reversible path |
| --- | --- | --- | --- |
| **APPROVE** | Records `approved` human review status | Approved | Reopen the job and choose another available review action |
| **KEEP REVIEWING** | Records `reviewing` status | Reviewing | Reopen and change status |
| **SKIP** | Records `skipped` status | Skipped | Reopen and change status |
| **Open report** | Selects a saved report | Report view | Close report |
| **Report Archive** | Selects a persisted report version | Archive detail | Close report |

The application records the state transition in PostgreSQL through the dashboard data facade. It does not perform a marketplace submission, send an email, or mutate evidence when a review button is clicked.

## Reports and audit

![Proposal and audit](../assets/screenshots/03-proposal-and-audit.png)

The proposal panel keeps generated text beside audit and validation output. A clean model response is not sufficient by itself: deterministic checks and upstream safety warnings remain visible. The report view exposes executive summary, job summary, opportunity assessment, personal fit, recommendation, strategy, proposal metadata, validation and warnings.

## Archive

![Report](../assets/screenshots/04-full-intelligence-report.png)

Report Archive preserves saved Stage 5 versions with report ID and version number. Pagination keeps the archive usable as it grows. The archive is a review surface, not a second source of truth.

## Demo navigation

Run `tools/run_dashboard_demo.ps1` to launch a fictional, local-only dataset. The demo uses the same interaction vocabulary while keeping production databases, credentials and live job content outside the public repository.
