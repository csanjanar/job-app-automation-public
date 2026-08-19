# Workflow 02: Extract & Curate Listings

## Trigger
Prompt: **`/extract-curate`** (Claude Code slash command, see `.claude/commands/extract-curate.md`)

## Objective
Batch pipeline:
1. **Scrape** whatever Raw Listings didn't already arrive fully-scraped from workflow 01 (Scrape Status="new" rows only — prefetched rows skip straight to step 2)
2. **Extract & curate** all Scrape Status="scraped" rows → populate Curated Listings with structured fields plus an advisory Fit Score/Fit Rationale, using any gather-time-known fields as authoritative rather than re-deriving them (skipping URLs already curated)
3. **Process Pre-Comments** → propose `profile/career_profile.md` edits for approval, mark applied
4. **Sync Tracker** → append any newly-`apply` rows (URL-keyed)

## Prerequisites
- Workflow 01 complete: Raw Listings has rows awaiting processing
- `.env` populated: `ANTHROPIC_API_KEY`, `FIRECRAWL_API_KEY`, `GOOGLE_SHEET_ID`
- Sheet structure and the note→diff governance pattern: see `workflows/README.md`

Behavioral notes specific to this workflow (beyond what's in the schema): mark unwanted Raw Listings rows `skip` rather than deleting them — a kept row is dedupe memory that stops the listing being re-gathered. Curated's `App Status`/`Posted`/`Closing` are formula columns and `Pre-Comments` is yours; everything else on that tab is tool-written.

---

## Phase 1: Scrape (Scrape Status="new" → "scraped" or "unable to scrape")

1. Read all Scrape Status="new" rows:
   ```bash
   python3 tools/read_from_sheet.py --tab "Raw Listings" --status new
   ```
   Rows workflow 01 already wrote at `Scrape Status="scraped"` (MCF-sourced, or Path B with capture) simply never appear here — nothing to do for them, skip straight to Phase 2.
2. For each row's `input_url`:
   ```bash
   python3 tools/scrape_listing.py <url>
   ```
   - Output: JSON in `.tmp/` with `url` and `markdown`
   - Auto-retries up to 3x with backoff on MyCareersFuture's un-hydrated app shell (`shell_page_detected: true`) — a single call may take ~60s worst case; not a hang
3. Update the row:
   ```bash
   python3 tools/write_to_sheet.py --tab "Raw Listings" --update-url <url> --data <path_to_json> --status scraped
   ```
   - Fills Text Scraped, Date Scraped (today), Scrape Status; cells truncate at ~49.5k chars (Sheets 50k cap) with a stderr warning
4. On scrape failure (still `shell_page_detected`, or empty/error `markdown`): same command with `--status "unable to scrape"`

### Manual-scrape path (for "unable to scrape" rows)
Don't paste text into the sheet by hand — multi-line paste splits across cells. Instead:
1. Copy the full job description from the browser
2. Save to `.tmp/manual/<anything>.txt`, or paste it to Claude with the URL
3. `python3 tools/write_to_sheet.py --tab "Raw Listings" --update-url <url> --data .tmp/manual/<file>.txt --status scraped`
4. Picked up in Phase 2 of the next run

## Phase 2: Extract & Curate (Scrape Status="scraped" → Curated Listings)

1. Read all Scrape Status="scraped" rows:
   ```bash
   python3 tools/read_from_sheet.py --tab "Raw Listings" --status scraped
   ```
   Each row you already have in hand — check whether `job_title`/`company`/`salary`/`date_posted`/`date_closing` are non-blank (gather-time prefetch); if so, pass them through in step 2 below rather than letting Haiku re-derive them.
2. **Skip URLs already in Curated Listings** (check with `read_from_sheet.py --tab "Curated Listings"`) to avoid extraction calls that will only be skipped at write time. For the rest, save the text to `.tmp/<slug>.txt` and run, passing the row's `date_scraped` so relative dates ("3d ago") resolve against the day the text was captured, plus any non-blank prefetched fields as overrides:
   ```bash
   python3 tools/extract_fields.py --input <path> --url <input_url> --scraped-date <date_scraped> \
     [--override-job-title "<row's job_title>"] [--override-company "<row's company>"] \
     [--override-salary "<row's salary>"] [--override-date-posted "<row's date_posted>"] \
     [--override-application-deadline "<row's date_closing>"]
   ```
   Haiku still runs — it's still the only source for `role_family`/`ml_domain`/`work_mode`/`industry_vertical`/`employer_type`, the skills breakdown, `recruiter_hr_contact`, and fit scoring — but any override replaces its guess for that field rather than trusting it. Output: `.tmp/<slug>_fields.json`.
3. Write to Curated Listings:
   ```bash
   python3 tools/write_to_sheet.py --tab "Curated Listings" --fields-json <path>
   ```
   Appends with Listing Status="extracted"; dedupe: an already-curated URL prints `Skipped (already curated at row N)` and exits cleanly. To force re-extraction, delete the Curated row first (safe — the Tracker is URL-keyed and unaffected).

   This also backfills any still-blank Job Title/Company/Salary/Date Posted/Date Closing/Source cells on the matching Raw Listings row (`backfill_raw_from_fields()` in `write_to_sheet.py`) — these are the same gather-time prefetch columns Path A/B fill directly; listings that went through scrape-then-extract (Path C, or Path B without capture) get them filled in here instead, once Haiku has derived them (Source is filled deterministically from the URL, not from Haiku). Blank-only: never overwrites a cell that's already set (real prefetch data, or a hand-edit). Never touches `Found` — that's set only at gather time, not here.
4. After a batch, run **`/refresh-skills`** (see `workflows/04_refresh_skills.md`)

## Phase 3: Process Pre-Comments → profile updates
The **Pre-Comments** column on Curated Listings is where a listing reveals a profile gap — see `workflows/README.md`'s governance section for the general pattern. Specifics for this one:
1. Read rows where Pre-Comments is non-blank and not already `✓ applied`
2. Draft the precise profile edit each comment calls for; show the diff, get approval, apply, prefix `✓ applied YYYY-MM-DD — `
3. If any edits landed: `/refresh-skills` is now stale (My Proficiency), and **Fit Scores of already-curated rows reflect the old preferences**

## Phase 4: Sync Tracker
```bash
python3 tools/sync_tracker.py
```
Appends any Curated rows newly marked `apply` to the Tracker (URL-keyed static values + seeded defaults). Idempotent; run it even if you don't think anything changed.

## Decision Point (Manual)
Open **Curated Listings**, sort by **Fit Score** if useful, and review each Listing Status="extracted" row:
- Read **Fit Rationale** as a starting point — it cites which of your preferences matched/clashed; the decision is yours
- **Listing Status → "apply"** to pursue, **"skip"** to dismiss
- Edit any extracted field that looks wrong before marking
- Note profile gaps in **Pre-Comments** — processed next run via Phase 3

Rows marked `apply` here sync to the Tracker on the *next* `/extract-curate` or `/generate-docs` run (both call Phase 4 / `sync_tracker.py`). For same-session effect, run **`/sync-tracker`** right after marking rows — this gets the row onto Tracker (with seeded defaults) so you can review/adjust it before running `/generate-docs`.

## Output
- **Curated Listings**: one row per unique URL, structured fields + Fit Score/Rationale populated, `Listing Status` awaiting your decision
- **Raw Listings**: rows stay at Scrape Status="scraped" after extraction (listing state lives in Curated, not here)
- **Tracker**: gains a row for every newly-`apply` Curated listing (URL-keyed, seeded with defaults)
- **`profile/career_profile.md`**: possibly updated if Pre-Comments were approved this run

## Edge Cases
- **LinkedIn / paywalled sites**: will fail to scrape — use the manual-scrape path
- **MCF app-shell / hydration failures**: auto-retried (3x, backoff + fresh proxy); if still failing it's transient/session — manual path, not a hard paywall
- **Rate limits**: Firecrawl free tier is 500 pages/month; batches of 10–15 stay well within
- **Missing fields**: Haiku returns null for fields not found — expected; fill manually if important
- **Raw Listings prefetch backfill is one-way and blank-only**: it fills Raw Listings from Curated's extraction, never the reverse, and never touches a cell that already has something in it. If Raw Listings' prefetch value is wrong (bad Path A/B capture) but Curated's Haiku-derived value is right, fix Raw Listings by hand — the backfill won't overwrite it once occupied.
- **Long listings**: trim company boilerplate before extracting; cells hard-truncate at ~49.5k chars
- **Extraction JSON errors**: re-run with `--retry` (a second failure exits cleanly); if it fails again, clean up the text format
- **Relative dates ("16 days ago", "3d ago")**: resolved against `--scraped-date` (fixed 2026-07-06; upgraded 2026-07-07 to use scrape date rather than extraction day) — moot for prefetched rows, whose dates come from the source directly
- **Google OAuth `invalid_grant`**: tools fall back to browser re-auth automatically (fixed 2026-07-07)
- **Dates crossing tabs** (Curated → Tracker): handled as ISO internally (fixed 2026-07-14 — formatted strings like `26-06-26` are locale-ambiguous and used to land as text → `#VALUE!`)

## Notes
- Extraction (incl. fit scoring) uses `claude-haiku-4-5` — ~$0.001 per listing
- Machine-set statuses are lowercase (`new`, `scraped`, `extracted`); filters are case-insensitive
