# Tools

Python scripts that do the actual work — API calls, web scraping, data transformations, file operations, Google Workspace writes. Each script is self-contained, accepts inputs via CLI args or stdin, and prints results to stdout or writes to `.tmp/`. Scripts load secrets from `.env` via `python-dotenv`. Never put decision logic here — that's the agent's job.

**Column addressing:** all sheet tools resolve columns **by header name** against `schema/sheets.yaml` + the live header row (via `sheets_common.py`) — never by letter. Formula columns and columns not in the schema are refused; user-added columns are ignored. Date cells crossing tabs are handled as ISO internally (formatted date strings are locale-ambiguous).

## Inventory

| Tool | Purpose |
|---|---|
| `sheets_common.py` | Shared library: OAuth (incl. re-auth fallback), schema loading, header-name column resolution, write protection |
| `profile_common.py` | Shared library: profile front-matter loader + fit-preference block renderer |
| `naming.py` | Shared library: path-component sanitizer (all artifact naming goes through this) |
| `generate_common.py` | Shared library: CLI plumbing for the four doc generators — load listing JSON, validate profile path, load a `--revise` doc, resolve the output directory. The prompt/API-call logic stays in each generator; only the fixed-data retrieval is shared |
| `check_schema.py` | Diff `schema/sheets.yaml` vs live sheet headers; `--fix` appends missing headers. Step 0 of every workflow. If the live sheet has known unresolved drift, scope with `--tab` rather than fixing blind |
| `search_mcf.py` | MCF API search using `search_targeting` from the profile front matter; writes each qualifying job as a fully-scraped Raw Listings row (description + structured fields already known from the API — no redundant re-scrape downstream) |
| `scrape_listing.py` | Firecrawl scrape of one listing URL → `.tmp/*.json` (auto-retries MCF app-shell pages) |
| `extract_fields.py` | Haiku extraction of structured fields + advisory Fit Score/Rationale (vs profile preferences) → `.tmp/*_fields.json`; `--override-*` flags let known-authoritative fields (from a prefetched Raw Listings row) take precedence over Haiku's own guess |
| `read_from_sheet.py` | Read any tab as JSON (snake_cased header keys); filters by status/url/company/role |
| `write_to_sheet.py` | Append/update rows; `--set "Header=value"` cell writes; URL dedupe; `--fields-json` maps a fields object onto a tab's schema-mapped headers (Curated Listings extraction output, or a Raw Listings gather-time prefetch payload). Every Raw Listings append stamps `Found="gather-listings"`. A Curated Listings write also blank-only-backfills the matching Raw Listings row's Job Title/Company/Salary/Date Posted/Date Closing/Source from the same extraction output (Source deterministically from the URL, not Found) |
| `sync_tracker.py` | Append Curated `apply` rows missing from Tracker (URL-keyed) + seed blank defaults. Replaces the old live QUERY |
| `build_skills_sheet.py` | Rebuild Skills Raw / Skills Freq from Curated Listings, cross-referencing profile proficiencies; also reads Raw Listings' Interest Rating (joined by URL) to compute Skills Freq's Avg Interest Rating; carries the manual Review Notes column forward across the rebuild |
| `generate_resume.py` | Sonnet generation (prompt-cached profile + LaTeX template); `--revise` + `--comments` for revisions |
| `generate_cover_letter.py` / `generate_followup.py` | Sonnet generation, plain text (no template); `--revise` + `--comments` for revisions |
| `generate_app_questions.py` | Sonnet generation, plain text Q&A markdown (no template) answering an employer's free-form application questions from the profile only; unlike the other generators, `--comments` (the question text itself) is **required on every run**, not just `--revise` |
| `compile_pdf.py` | tectonic LaTeX → PDF (resume only) |
| `save_local_copy.py` | Copy resume PDFs to `applications/` as `{Company}_Alex_{JobTitle}_Resume.pdf` (company-first, easy to pick the right one to submit); `--clear` once per batch. The PDF lives here **only** — it is not pushed to GitHub |
| `push_docs_to_github.py` | Stage/commit/push artifacts to the private docs repo; prints `FOLDER_URL=`/`FOLDER_DATE=` for write-back. Resume pushes only `.tex` (source), never the compiled `.pdf` |
| `run_doc_batch.py` | Deterministic driver for workflow 03: executes an agent-built manifest (generate→compile→check→save→stage→push→write-back), checkpointed + `--resume`-safe |
| `outcomes_report.py` | Workflow 05 report: funnel, breakdowns by dimension/template/fit, consumed directives, manual-edit commits. Reads the result from **Outcome** (App Status is lifecycle-only since schema v4; "applied+" = `Applied` or `Completed` since v11) |

## Tools by workflow

Cross-reference view of the Inventory above, grouped by which workflow calls each tool — not a new categorization, and `tools/` itself stays flat.

| Workflow | Tools used |
|---|---|
| [01 – Gather Listings](../workflows/01_gather_listings.md) | `search_mcf.py`, `write_to_sheet.py` |
| [02 – Extract & Curate](../workflows/02_extract_and_curate.md) | `scrape_listing.py`, `extract_fields.py`, `read_from_sheet.py`, `write_to_sheet.py`, `sync_tracker.py` |
| [03 – Generate Documents](../workflows/03_generate_documents.md) | `check_schema.py`, `sync_tracker.py`, `read_from_sheet.py`, `run_doc_batch.py` (drives `generate_resume.py`, `generate_cover_letter.py`, `generate_followup.py`, `generate_app_questions.py`, `compile_pdf.py`, `save_local_copy.py`, `push_docs_to_github.py`) |
| [04 – Refresh Skills](../workflows/04_refresh_skills.md) | `build_skills_sheet.py`, `write_to_sheet.py`, `profile_common.py` |
| [05 – Review Outcomes](../workflows/05_review_outcomes.md) | `outcomes_report.py`, `generate_resume.py` |
| Shared across workflows | `sheets_common.py`, `profile_common.py`, `naming.py`, `generate_common.py`, `check_schema.py` |

## Legacy / one-off — not a pattern to follow

Already ran, already did their job, kept for reference rather than reuse. No workflow calls any of these.

| Tool | Why it's here |
|---|---|
| `update_action_req_find_contact.py` | One-off (post-v11, 2026-08-07): live formula tweak to the Tracker `Action Req.` ARRAYFORMULA — added a 'Find Contact' rung to the Applied branch (Follow-up Contact empty → prompt) and stopped Follow-Up 'Not Required' from short-circuiting the follow-up nudge. No schema/vocab change. Idempotent — unlike the other migrations here, safe to re-run. |
| `migrate_tracker.py` | One-time: froze the Tracker's old live QUERY to static values during the 2026-07-14 rewrite. Refuses to re-run once migrated. |
| `migrate_outcome_split.py` | One-time (schema v3→v4, 2026-07-16): split App Status (lifecycle) from Outcome (result status), moved the old Outcome date into new `Outcome Date`, renamed `Days > Post`→`Apply Lag` / `Follow-Up Date`→`Follow-Up Due`, added `Salary (mo)` + `Action Req.` formulas, and applied dropdowns/conditional formatting. Snapshot-first, dry-run by default, refuses to re-run once migrated. |
| `remove_follow_up_due.py` | One-time (schema v8→v9, 2026-08-04): deleted the `Follow-Up Due` column, rewrote `Action Req.`'s ARRAYFORMULA to compute the same due-date reminder inline from `Date Applied` instead, and removed the column's orphaned conditional-format rule. Snapshot-first, dry-run by default, refuses to re-run once migrated. |
| `migrate_doc_trigger_rename.py` | One-time (schema v9→v10, 2026-08-05): relabelled the doc-trigger vocabulary (`Generate`→`Required`, `Change > Generate`→`Revise`) in the four trigger columns' cell values + dropdowns, and rewrote `Action Req.`'s trigger comparisons to match. Snapshot-first, dry-run by default, refuses to re-run once migrated. |
| `migrate_action_req_v11.py` | One-time (schema v10→v11, 2026-08-06): redesigned `Action Req.` into a phase-gated ladder; retired App Status `Responded`, made `Completed` official; added the manual `Follow-up Date` column and the Follow-Up `No Contact` sentinel (`follow_up_trigger` vocab); added Option-A assumed dates to the `Posted`/`Closing` display formulas (missing date inferred as `EDATE(other, ∓1 month)`, italicised); and rebuilt all Tracker conditional formatting into one harmonised palette shared by `Action Req.` and every status/trigger dropdown. Snapshot-first (values + row-2 formulas + conditional-format rules), dry-run by default, refuses to re-run once migrated. |
| `backfill_categories.py` | One-off: backfilled classification columns for the first handful of Curated Listings rows, predating the header-name-addressing rewrite (uses hardcoded `E:I` letter ranges and its own duplicated OAuth block rather than `sheets_common.py`). Don't copy its patterns into new tools. |
