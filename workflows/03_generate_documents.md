# Workflow 03: Generate Application Documents

## Trigger
Prompt: **`/generate-docs`** (Claude Code slash command, see `.claude/commands/generate-docs.md`)

## Objective
For Tracker rows whose per-document trigger columns request work, generate/revise exactly those documents and let the deterministic driver (`tools/run_doc_batch.py`) handle everything mechanical: compile + 1-page check + local review copy (resume only — cover letters and follow-ups are plain text pushed as-is), one batch push to the private GitHub docs repo, and the Tracker write-back. The agent's job is **judgment only**: pick the resume template, interpret comments, build the manifest, triage failures.

## Prerequisites
- `profile/career_profile.md`, `templates/*.tex` (see Template Selection Guide)
- `.env` populated: `ANTHROPIC_API_KEY`, `GOOGLE_SHEET_ID`, `GITHUB_DOCS_REPO`
- `tectonic` installed (`brew install tectonic`); `gh` installed and authenticated; repo `alex-tan-demo/job-app-docs` (private) exists

## Sheet structure
See `workflows/README.md` for the general schema/header-addressing mechanics. Specific to this workflow:

- **Trigger columns** `Resume` / `Cover Letter` / `App Qns`: `Required` | `Revise` | `Generated` | `Submitted` | `Not Required` (blank = ignored). Only the first two trigger work; the driver sets `Generated`; you set `Submitted` when actually sent.
- **`Follow-Up`** shares that vocab plus one extra value — **`No Contact`** — which you set only when there's genuinely no one to reach; it parks the row's Action Req. at "No contact — revisit" (silent, never nudged). Note the seeded default `Not Required` **no longer silences** the follow-up nudge: on an `Applied` row with a `Follow-up Contact` present it falls through to the ≥3-day **Follow-up due** prompt. To intentionally stop chasing a role, set `App Status = Completed` (not `Follow-Up = Not Required`).
- **`Follow-up Contact` empty on an `Applied` row** → Action Req. shows **Find Contact** (amber) immediately, prompting you to line up someone to reach out to. It clears once you fill the contact in (or set `Follow-Up = No Contact`).
- **`App Status`** is lifecycle only (`To Apply` → `Applied` → `Completed`) — it never triggers doc generation.
- **Comment columns** (`Resume - Comments` etc.): consumed **verbatim** at generation time (fresh *and* revise), then prefixed `✓ applied YYYY-MM-DD — ` by the driver. Comments can only draw on what `career_profile.md` already contains — generators are forbidden from fabricating. A comment revealing a **profile gap** belongs in Curated Listings **Pre-Comments** instead (workflow 02 Phase 3).
- **`Follow-Up - Comments` also carries medium/purpose/variant requests**: there's no separate schema field for this, so specify the desired medium and purpose directly in this column. Free text works (the generator infers medium/purpose from context), but an optional `[medium] {purpose}: "..."` tag convention keeps multi-variant requests unambiguous:
  - `[medium]` = one or more of `email` / `linkedin-connect` / `linkedin-message` / `whatsapp`, `+`-joined if more than one — each medium listed produces its own variant (medium is what forks variants).
  - `{purpose}` is optional; its only defined value is `personal` (networking interest in the person, not a job pitch). `{personal + job}` blends both into the same message rather than forking extra variants — purpose changes tone/content, not variant count.
  - Each variant lands under its own heading, in the order mediums are listed.

  Example — 2 variants (one per medium), the second blending both purposes:
  ```
  [linkedin-connect] {job}: "keep it to the connection request, mention the FYP overlap"
  [linkedin-message] {personal + job}: "once connected, ask about her move from data science into MLE, but still flag interest in the role"
  ```
  Untagged text still works exactly as before.
- **`App Qns - Comments` is different**: for the other three doc types the comment is optional tailoring feedback — the doc is generatable from profile + listing alone. For `App Qns`, the comment **is** the employer's actual free-form question text (paste it verbatim); there's no other source for it, so it's required before setting `App Qns=Required` (the driver's `--validate` rejects a manifest row missing it). `Revise` on App Qns works like any other revise — the new comment is feedback on the previously generated answers, not a fresh question list.

## Phase 0: Sync + schema check
```bash
python3 tools/check_schema.py
python3 tools/sync_tracker.py
```
Sync appends any new Curated `apply` rows to the Tracker (URL-keyed, static values) and seeds defaults (`App Status=To Apply`, `Resume=Required`, CL/Follow-Up=`Not Required`) into blank cells. There is no QUERY and no positional alignment anymore — deleting Curated rows can't corrupt the Tracker.

**New in v11:** the manual `Follow-up Date` column resets the staleness clock and drives the "Follow-up due" nudge — set it when you contact an employer or plan to. Action Req. measures "Awaiting response" age from the later of `Date Applied` / `Follow-up Date`.

## Phase 1: Read the batch, build the manifest
```bash
python3 tools/read_from_sheet.py --tab Tracker --out .tmp/tracker.json
```
Action rows = any of `resume` / `cover_letter` / `follow_up` / `app_questions` equal to `Required` or `Revise`.

Build `.tmp/doc_batch_manifest.json` (shape documented at the top of `tools/run_doc_batch.py`). Judgment calls per row/doc:
- **Template** (resume only): use the Template Selection Guide below.
- **`folder_date`**: the row's `docs_gen_date` if non-blank (set `docs_gen_date_was_blank: false`), else today as `DD-MM` (set `true`). Revisions must land in the row's original folder so the Docs (Link) stays valid.
- **Comments**: copy un-✓'d comment text **verbatim** into `comments`, with the matching `comment_header` (e.g. `"Resume - Comments"`). For `app_questions`, comments are required on **every** run (fresh or revise) — it's the question text itself, not optional feedback; refuse to build a manifest row for `app_questions` with a blank `App Qns - Comments`.
- **`Revise`** → `mode: revise` with `revise_path` pointing into the repo clone `.tmp/job_app_docs_repo/{folder_date}_{Company}_{JobTitle}/Alex_{Doc}_{role}.ext` (`.tex` for resume, `.md` for cover letter/follow-up/app questions; pull first: `git -C .tmp/job_app_docs_repo pull`). Comments are **required** for a revise. If nothing was ever pushed (blank `docs_gen_date` / missing folder), fall back to `mode: fresh` with the comments folded in — and say so.

Then pre-flight and report to Alex **before any paid call**:
```bash
python3 tools/run_doc_batch.py --manifest .tmp/doc_batch_manifest.json --validate
```
State which rows/docs will generate and the cost estimate; get a go-ahead.

## Phase 2: Run the driver
```bash
python3 tools/run_doc_batch.py --manifest .tmp/doc_batch_manifest.json
```
Resume: generate → compile → 1-page check → save to `applications/`. Cover letter / follow-up / app questions: generate only — plain text, no compile or local copy. Then every doc gets staged in the repo clone; **one** batch push and the per-row write-back (`Generated` statuses, `Docs (Link)`, `Docs Gen Date`, `Template`, ✓-applied comment prefixes). Progress is checkpointed in the manifest after every step.

**On failures**: the driver marks the failed doc, keeps going with other rows, and exits 1. Fix the cause (see Edge Cases), then:
```bash
python3 tools/run_doc_batch.py --manifest .tmp/doc_batch_manifest.json --resume
```
`--resume` retries from the failed step — it never re-fires a completed paid generation call and never re-consumes a comment. **Never rebuild a manifest for a partially-run batch** — that's what causes double paid calls.

## Phase 3: Report + manual review
- Report per row: docs generated, folder URL, and (resume only) local PDF in `applications/` (named `{Company}_Alex_{JobTitle}_Resume.pdf`).
- Review the pushed docs via each row's Docs (Link) — cover letters/follow-ups are plain text, read directly in the repo; resumes also get a local PDF.
- When you actually submit a document, set its trigger cell to `Submitted` and progress `App Status` yourself.

### Manual-tweak path (small changes — prefer this over `Revise`)
For wording/typo-level edits, skip the paid revise call:
1. Edit the file **in the repo clone** `.tmp/job_app_docs_repo/<folder>/` (pull first)
2. Resume only: `python3 tools/compile_pdf.py --tex <edited>.tex`, re-save via `save_local_copy.py`. Cover letter/follow-up/app questions: no compile step — the edited `.md` is already the final artifact.
3. Commit + push in the clone (or ask Claude to "recompile and push")

Hand-edits must land in the git clone — it's the source of truth a future `Revise` starts from, and workflow 05 mines these commits for recurring preferences. Reserve `Revise` for substantive rework.

## Output
```
GitHub repo: alex-tan-demo/job-app-docs
└── {DD-MM}_{Company}_{JobTitle}/            ← DD-MM = row's Docs Gen Date, fixed on first push
    ├── Alex_Resume_{JobTitle}.tex        ← source only; the compiled PDF is NOT pushed
    ├── Alex_CoverLetter_{JobTitle}.md
    ├── Alex_FollowUp_{JobTitle}.md
    └── Alex_AppQuestions_{JobTitle}.md

applications/                                 (local-only resume PDFs, cleared and rebuilt each batch)
└── {Company}_Alex_{JobTitle}_Resume.pdf   ← company-first naming so the right file to submit is easy to spot
```
Scratch dirs in `.tmp/applications/` are deleted after successful write-back; the clone persists. The resume PDF exists **only** in `applications/` — recompile from the repo's `.tex` (`tools/compile_pdf.py`) if you need it again later.

## Template Selection Guide
Pick the template closest to the role's domain; record it in the manifest (the driver writes it to the Tracker `Template` column for outcome analysis).

| Template | Use for |
|----------|---------|
| `templates/resume_ml_research.tex` | Applied ML Research, NLP Engineer, Research Engineer, Applied Scientist, Generative AI, Agentic AI — leads with FYP benchmark + NLP + GenAI projects; includes WITCircle mentorship |
| `templates/resume_data_cv.tex` | Data Scientist, ML Engineer, Computer Vision Engineer, Data Analyst — leads with FYP CV pipeline, EUI data science, fake news ML |
| `templates/resume_geospatial.tex` | Spatial Data Scientist, GIS Analyst, Urban Analytics, Sustainability/Climate Tech — leads with CIPA GIS work, EUI built environment project |
| `templates/resume_base.tex` | General SWE, Full-Stack, Backend — when none of the above fit clearly |

When in doubt between two, pick the one whose projects list most closely matches the listing's `key_tools_skills`. Cover letters, follow-ups, and app questions have no template — they're generated as plain text directly from the profile + listing (app questions also take the pasted question text), matching the salutation → body → sign-off structure in `tools/generate_cover_letter.py`'s system prompt (app questions instead produces `**Q: ...**` / answer pairs — see `tools/generate_app_questions.py`).

## Edge Cases
- **LaTeX compile errors**: check the raw `.tex` — Claude sometimes hallucinates LaTeX commands. Fix the file in the scratch dir, then `--resume`.
- **Resume >1 page**: the driver fails that doc with the page count. Trim the weakest bullets in the scratch `resume.tex`, then `--resume` (it re-compiles without regenerating). (Fixed 2026-07-30: `--resume` used to skip straight to re-checking the stale, un-recompiled PDF — the page-count checkpoint was persisted as `status="compiled"` before the check ran, so `--resume` restarted past the compile step. The compile and page-check are now one atomic step gated on `status="generated"`, so a page-count failure always leaves `status="generated"` and `--resume` recompiles against your edited `.tex`.) A single trim is often not enough to drop a page — recompile and recheck page count after each edit rather than assuming one cut suffices.
- **`fontawesome5` crashes tectonic** (SIGABRT/exit 134): tectonic's bundle lacks Font Awesome — resume templates use plain-text labels. Don't introduce `fontawesome5`. (`templates/cover_letter_base.tex`/`.pdf` were removed 2026-07-16 — unreferenced since cover letters generate as plain text.)
- **`\input{glyphtounicode}` + `\pdfgentounicode=1`**: pdfTeX-only; already removed from all templates — don't reintroduce.
- **No recruiter contact**: cover letter falls back to "Dear Hiring Manager,"; follow-up becomes a general outreach message.
- **Follow-up medium/purpose/multi-variant requests**: driven entirely by `Follow-Up - Comments` free text — e.g. "WhatsApp, casual, just want to catch up about her move into ML" or "LinkedIn connection request + a longer follow-up for after she accepts". If the comment doesn't specify a medium, the message defaults to the original general email/LinkedIn-suitable style (~100-150 words).
- **No matching Curated row**: the driver fails the row with "run /extract-curate first".
- **Curated Listings `Job Title` column desynced from `Company`/`URL`** (found 2026-08-14): if a column in Curated Listings ever gets sorted/pasted independently of the rest of the row, `job_title` can silently point at the wrong listing while `company`/`url`/`role_family`/etc. stay correct — since `generate_followup.py` (and the other generators) read `job_title` straight from `listing.json`, the generated doc references the wrong role even though the manifest's own `company`/`job_title` (correct, Tracker-sourced) are right. Tracker's `job_title` is a reliable cross-check: `sync_tracker.py` never overwrites an existing row's cells, so for any row already in the Tracker, its `job_title` reflects what Curated held at first-sync time. Before trusting a batch, spot-check a few Curated rows' `job_title` against the Tracker's for the same URL; if desynced, fix with `write_to_sheet.py --tab "Curated Listings" --update-url <url> --set "Job Title=<correct title>"` for every affected row, then regenerate any docs already produced from bad data via `mode: revise`.
- **"nothing to commit" during staging**: a revision produced an identical file — the driver treats this as staged and moves on.
- **Flaky `git push`** (`Failed to connect to github.com port 443 …`): commits exist locally — `python3 tools/push_docs_to_github.py --push-only`, then `--resume` for the write-back.
- **Push succeeded but write-back failed** (e.g. OAuth hiccup): just `--resume` — the manifest knows the push happened and only the write-back remains. Never regenerate.
- **Google OAuth `invalid_grant`**: sheet tools fall back to browser re-auth automatically; complete the sign-in and the run continues.

## Cost Notes
- Generation uses `claude-sonnet-4-6` with prompt caching on the profile (+ template); typical cost per application set ~$0.05–0.10; revise calls similar. `--validate` prints the estimate.
- **Check with Alex before re-running paid generation after a failure** — though note `--resume` re-fires only the step that failed, which for compile/page/staging failures costs nothing.
