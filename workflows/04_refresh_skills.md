# Workflow 04: Refresh Skills Analysis

## Trigger
Prompt: **`/refresh-skills`** (Claude Code slash command, see `.claude/commands/refresh-skills.md`). Run after any batch of `/extract-curate` runs (new curated rows to fold in), or after editing `profile/career_profile.md` (to refresh My Proficiency against your latest skill levels).

## Objective
Rebuild the Skills Raw and Skills Freq tabs from the current state of Curated Listings, so skill frequency and proficiency gaps stay current. Then process any Skills Freq **Review Notes** into approved `career_profile.md` (or alias-table) edits, so gaps you've decided to close actually close.

## Prerequisites
- At least one row in Curated Listings with Listing Status="extracted" (or later)
- `.env` populated: `GOOGLE_SHEET_ID`
- `pyyaml` installed (`pip install pyyaml`) — the profile front matter is parsed via `tools/profile_common.py` and will crash with `ModuleNotFoundError: No module named 'yaml'` if missing
- Sheet structure and the note→diff governance pattern: see `workflows/README.md` (Skills tabs are created on first run)

## Phase 1: Rebuild
1. Run:
   ```bash
   python3 tools/build_skills_sheet.py
   ```
2. This rebuilds two tabs from scratch, reading both Curated Listings (skills, role/domain/mode) and Raw Listings (Interest Rating, joined by URL):
   - **Skills Raw** — long-format, one row per skill × listing
   - **Skills Freq** — aggregated, one row per unique skill with frequency, proficiency, and average interest rating

   **Skills Freq is a full rewrite every run** (not an append) — but the manual **Review Notes** column survives it: the tool reads the existing tab first, keys any non-blank notes by normalised Skill/Term, and carries them onto the matching row in the rebuilt tab. New skills get a blank Review Notes cell; skills you've already reviewed keep their note (including any `✓ applied` prefix) no matter how their row position or frequency shifts.

## Phase 2: Process Skill Review Notes
The **Review Notes** column on Skills Freq is where you flag a blank-`My Proficiency` (or any) skill for action — see `workflows/README.md`'s governance section for the general pattern. Specifics for this one:

1. Read Skills Freq rows where Review Notes is non-blank and doesn't start with `✓ applied`
2. Interpret the note and draft the concrete edit:
   - **"add [at proficiency]"** (e.g. "add - Working", "add, Familiar") → a new entry in `career_profile.md`'s `skills:` YAML block. Place it under whichever existing category key best fits — `languages`, `ml_and_ai`, `generative_ai_and_llms`, `computer_vision`, `nlp`, `data_science`, `backend_and_databases`, `devops_and_tools`, `gis_and_geospatial`, `software_engineering`, or `currently_learning` (no proficiency level needed there) — following the naming convention already used in that category (e.g. `New_Skill_Name: Working`). If the note gives no proficiency, ask rather than guess.
   - **"already covered as X" / "same as X"** (an aliasing gap — the skill exists in the profile under different wording than the listings use) → propose an addition to the `ALIASES` list in `tools/build_skills_sheet.py` instead, mapping the listing term to the existing profile key. Don't touch the profile for this case.
   - **"skip" / "not relevant" / "not adding"** → no file edit; just mark it reviewed so it stops needing attention
3. **Show the proposed diff and get explicit approval before editing** — same governance as every other profile-touching step in this system; the profile drives fit scoring and every generated document, so accuracy risk lives here
4. On approval: apply the edit, then prefix the Review Notes cell with `✓ applied YYYY-MM-DD — `:
   ```bash
   python3 tools/write_to_sheet.py --tab "Skills Freq" --update-url "<Skill / Term value>" --set "Review Notes=✓ applied YYYY-MM-DD — <original note>"
   ```
   (Skills Freq's key column is `Skill / Term`, not a URL — `--update-url` just means "row key" generically here, per `schema/sheets.yaml`)
5. If any profile edits were applied, **re-run Phase 1** (`python3 tools/build_skills_sheet.py`) so My Proficiency reflects the change immediately — the Review Notes you just marked will carry forward correctly

## Output

### Skills Raw
Long-format table — one row per skill × listing. Headers:
`Skill / Term | Category | Job Title | Company | Role Family | ML Domain | Work Mode | Source URL`

- **Skill / Term**: exact string extracted from the listing (e.g. "PyTorch", "stakeholder management")
- **Category**: one of `Tool / Framework`, `Concept / Practice`, or `Soft Skill` — inferred from which column (J/K/L) the skill appeared in

### Skills Freq
Aggregated frequency table — one row per unique skill, sorted descending by frequency. Headers:
`Skill / Term | Category | My Proficiency | Frequency | Avg Interest Rating | Role Families | ML Domains | Work Modes | Appears In (Job Titles) | Review Notes`

- **My Proficiency**: cross-referenced against `profile/career_profile.md` YAML front matter.
  - `Expert` — production-level, go-to tool
  - `Working` — solid day-to-day use
  - `Familiar` — used in projects, not daily
  - `Learning` — currently building fluency
  - *(blank)* — skill is not in your profile (a gap to consider)
  - Matching uses normalised lookup (lowercase + collapsed whitespace) plus an alias table that maps listing terminology to profile YAML keys (e.g. "TensorFlow" → `TensorFlow_Keras`, "RAG" / "LLM" → `LLM_RAG`, "sklearn" → `Scikit_Learn`)
- **Frequency**: number of listings that mention the skill
- **Avg Interest Rating**: mean of Raw Listings' `Interest Rating` (1-5, see `schema/sheets.yaml`'s `interest_rating:` block) across the listings mentioning this skill that have actually been rated — joined by URL (Raw Listings' `Input URL` == Curated Listings' `URL`). Blank if none of the listings mentioning it have been rated yet; unrated listings are excluded from the average, not treated as 0.
- **Role Families / ML Domains / Work Modes**: pipe-separated unique values from all listings containing the skill
- **Appears In**: comma-separated job titles

## Edge Cases
- **No new listings since last run**: safe to re-run anyway — it's a full rebuild, not incremental
- **Career profile edited but no new listings**: still worth running to refresh My Proficiency
- **Raw Listings rows with no Interest Rating set**: excluded from `Avg Interest Rating` entirely (not counted as 0) — a skill only appearing in unrated listings shows a blank average, not a low one. Rate more Raw Listings rows and re-run to sharpen the picture.
- **A skill's row disappears from Skills Freq**: only happens if every listing containing it is later excluded from Curated Listings — its Review Note (even `✓ applied`) is lost with it, since there's nothing left to carry it forward to. Rare; the note's effect (the profile/alias edit) already persisted regardless.
- **Ambiguous "add" note with no proficiency stated**: ask rather than guess — proficiency claims feed directly into what generated resumes and cover letters say about you
