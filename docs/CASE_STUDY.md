# Case study: one opportunity, six decisions

This walkthrough uses the repository's fictional opportunity fixture. It is intentionally sanitized and demonstrates the shape of a run rather than claiming a real client outcome.

## 1 · Intake

A job notification becomes a normalized record with title, description, budget, client signals and source URL metadata. The intake stage establishes identity and an input hash so retries can be recognized.

## 2 · Job intelligence

The system extracts deliverables, constraints, requested technologies, collaboration expectations and commercial signals. This turns a long brief into a structured decision surface.

## 3 · Opportunity and personal fit

Deterministic components calculate opportunity and personal-fit scores. AI interpretation adds context, but the score components remain inspectable. The final decision stage combines them with warnings and evidence availability.

## 4 · Evidence retrieval

The retrieval stage issues focused queries, combines dense and sparse signals, applies reciprocal-rank fusion and packages source metadata. Evidence is selected for the claim it can support, not merely because it is semantically nearby.

## 5 · Strategy and claim boundaries

Proposal strategy separates mandatory client/commercial obligations from selectable writing priorities. Unsupported high-risk positioning becomes a critical downstream constraint. The strategy can recommend a cautious path without inventing experience.

## 6 · Write, audit, validate

Stage 4A drafts the proposal. Stage 4B audits it independently. Deterministic validation keeps unresolved upstream critical warnings visible, checks required content and flags excessive length, repetition or questions. The resulting report is persisted for review.

## 7 · Human decision

The dashboard shows the job, evidence, proposal, audit and warnings. The human chooses **APPROVE**, **KEEP REVIEWING** or **SKIP**, then may open Upwork and act externally. Project-E does not auto-submit.
