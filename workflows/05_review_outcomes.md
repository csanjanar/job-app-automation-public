# Workflow 05: Review Outcomes → Improve the System

## Trigger
Prompt: **`/review-outcomes`** (Claude Code slash command, see `.claude/commands/review-outcomes.md`). Run monthly, or on demand after a batch of responses lands.

## Objective
Close the self-improvement loop on **outcomes**, not just failures: learn which role families / employer types / domains / templates actually convert, whether Fit Scores are calibrated, and which recurring per-application directives and manual doc edits deserve promotion into templates, generator prompts, or the profile. All changes ship as **approved diffs only**.

## Prerequisites
- `.env`: `GOOGLE_SHEET_ID`; docs repo clone at `.tmp/job_app_docs_repo` (for the manual-edits section; cloned automatically by workflow 03 runs)
- Tracker rows carry real lifecycle data: `App Status` progressed, `Date Applied` and `Outcome` filled in as things happen — the report is only as good as these

## Phase 1: Generate the report
```bash
python3 tools/outcomes_report.py --out .tmp/outcomes_report.md
```
Sections: funnel (+days-awaiting-response), status breakdowns by Role Family / Employer Type / ML Domain / Template / Fit Score, all consumed ✓-applied comment directives (recurring ones flagged), and docs-repo commits that aren't generation pushes (= manual hand-edits).

## Phase 2: Interpret (agent judgment)
- **Conversion patterns**: any role family / employer type / template with distinctly better or worse response rates? Small samples — present as observations with counts, not conclusions.
- **Fit calibration**: are high Fit Scores actually converting? If 5s get rejected while 3s interview, the profile preference sections (which drive scoring) may be misweighted.
- **Recurring directives**: comments appearing ≥2 times (or prefixed `!general`) are promotion candidates — e.g. a repeated "more formal tone" belongs in the cover-letter SYSTEM_PROMPT, a repeated "lead with X" in the relevant template's default ordering.
- **Manual edits**: for each non-generation commit, `git -C .tmp/job_app_docs_repo show <hash>` and look for *consistent* hand-changes (same phrasing swap, same section reorder across applications) — those are template/prompt candidates too. One-off tweaks are noise; leave them.

## Phase 3: Propose promotions (approval required — never auto-apply)
For each candidate, show a concrete diff against the target file and get explicit approval:
- **Templates** (`templates/*.tex`) — ordering, phrasing, section defaults
- **Generator prompts** (`tools/generate_resume.py` / `generate_cover_letter.py` / `generate_followup.py` SYSTEM_PROMPTs) — durable style/tone rules
- **Profile** (`profile/career_profile.md`) — preference reweighting (affects future Fit Scores), search_targeting changes
- **Search targeting** — retire queries whose listings never get marked `apply`; add queries for patterns that convert

On approval, apply + commit (normal git policy). Note in the commit message which outcome pattern motivated the change.

## Phase 4: Optional hygiene
- Rows stuck at `Applied`/`Completed` with no Outcome past ~3 weeks (Action Req. shows the age in days): suggest follow-ups (set `Follow-Up` to `Required`, or fill `Follow-up Date` to reset the clock) or mark the Outcome `Closed`
- If profile preferences changed: remind that `/refresh-skills` is stale and existing Fit Scores reflect old preferences

## Output
- `.tmp/outcomes_report.md` (regenerable; the durable artifacts are the approved commits it leads to)
- Approved improvements committed to templates / prompts / profile

## Edge Cases
- **Small numbers**: with <20 applications, differences of 1–2 responses are noise — frame everything as "worth watching", not "proven"
- **Blank Template column** on older rows: predates 2026-07-14 (recorded by the batch driver from then on) — exclude those rows from template comparisons
- **Comments classified at review time, not entry time**: job-specific comments stay row-scoped forever unless *this* workflow promotes them; nothing is auto-generalized. `!general` prefix = fast-track flag, still needs approval here
- **Docs repo clone missing**: run `gh repo clone $GITHUB_DOCS_REPO .tmp/job_app_docs_repo` — the report degrades gracefully without it
