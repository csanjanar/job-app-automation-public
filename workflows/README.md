# Workflows

Markdown SOPs that define how to accomplish a goal. Each workflow should cover: **Objective** (what we're trying to do), **Inputs** (what's needed to start), **Steps** (which tools to call and in what order), **Outputs** (what gets produced and where it goes), and **Edge Cases** (known failure modes and how to handle them). Written in plain language — the same way you'd brief a teammate. Don't create or overwrite workflow files without being asked.

## Trigger Map

These are Claude Code custom slash commands defined in `.claude/commands/` — typing the command (e.g. `/gather-listings`) invokes the workflow directly, so it can't be mistaken for ordinary conversation.

| Prompt | Workflow | Objective |
|---|---|---|
| `/gather-listings` | [01_gather_listings.md](01_gather_listings.md) | Find candidate job URLs (profile-driven targeting), write them to Raw Listings already fully scraped where the source allows it; process Gather Notes feedback |
| `/extract-curate` | [02_extract_and_curate.md](02_extract_and_curate.md) | Scrape whatever Raw Listings didn't already arrive with → extract structured fields + Fit Score into Curated Listings; process Pre-Comments; sync Tracker |
| `/sync-tracker` | [02_extract_and_curate.md](02_extract_and_curate.md) Phase 4 | Sync newly-'apply' Curated Listings rows into Tracker on demand (also runs automatically at the end of /extract-curate and start of /generate-docs) |
| `/generate-docs` | [03_generate_documents.md](03_generate_documents.md) | Build a batch manifest for Tracker rows whose trigger columns request docs; the deterministic driver generates, compiles, pushes, and writes back |
| `/refresh-skills` | [04_refresh_skills.md](04_refresh_skills.md) | Rebuild Skills Raw / Skills Freq tabs from Curated Listings; process Review Notes feedback |
| `/review-outcomes` | [05_review_outcomes.md](05_review_outcomes.md) | Monthly: aggregate outcomes, check fit calibration, promote recurring directives/manual edits into templates & prompts (approved diffs only) |

Read the matching workflow file for whichever command was invoked — plus this file once (it's short, and the two sections below are shared mechanics every workflow assumes you've read, not duplicated in each one). You don't need to scan the *other* workflow files.

## Sheet Structure

`schema/sheets.yaml` is the single source of truth for every tab: headers, whether each is `tool`-written / `manual` / `formula`, status vocabularies, and classification vocabularies (also feeds the extraction prompt directly, so the sheet and the LLM never disagree on categories). Tools resolve columns **by header name** against the live sheet (`tools/sheets_common.py`) — never by letter — so reordering or adding your own columns never breaks anything; a column that isn't in the schema is simply ignored by tools.

`python3 tools/check_schema.py` diffs the schema against the live sheet and is step 0 of every workflow (`--fix` appends any headers missing from the sheet). To change sheet structure: edit `schema/sheets.yaml`, bump `schema_version` + add a changelog entry, run `check_schema.py`, in the same commit as whatever tool/workflow change needed it.

**Caution**: if the live sheet has drifted from the schema (renamed/removed columns not yet reflected there), run `check_schema.py` scoped to just the tab you're changing (`--tab "X"`) rather than bare `--fix` against the whole sheet — an unscoped `--fix` will re-append every other tab's missing headers too, which is exactly wrong when drift is being deliberately left unresolved.

## Governance: Notes → Approved Diffs

Three places in this system use the same pattern: a manual column where Alex leaves a freeform note, which a workflow phase turns into a **proposed diff** against a target file, shown for **explicit approval** before anything is edited, then applied and the note prefixed `✓ applied YYYY-MM-DD — <original>` so it's never reprocessed. Never auto-apply — these all touch files that drive fit scoring, targeting, or generated documents, so accuracy risk lives here.

| Note column | Tab | Target file | Workflow |
|---|---|---|---|
| Gather Notes | Raw Listings | `profile/career_profile.md` (`search_targeting`) | 01 |
| Pre-Comments | Curated Listings | `profile/career_profile.md` (skills/preferences) | 02 Phase 3 |
| Review Notes | Skills Freq | `profile/career_profile.md` (skills) or `tools/build_skills_sheet.py` (`ALIASES`) | 04 Phase 2 |

Each workflow section for these covers only what's specific to it (which column, which file, how to interpret its notes) — the approve-then-apply mechanics above aren't restated per-file.
