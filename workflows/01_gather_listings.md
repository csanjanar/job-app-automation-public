# Workflow 01: Gather Job Listings

## Trigger
Prompt: **`/gather-listings`** (Claude Code slash command, see `.claude/commands/gather-listings.md`). Run it **when you're ready to apply** — listings shouldn't sit unattended (recency of application strongly affects visibility and success), so gathering stays manual by design.

## Objective
Find ~5 suitable job listing URLs — strict on recency (`search_targeting.recency_days`, currently 5 days) — and add them to **Raw Listings**. Where the source already provides the full listing text and structured fields (Path A always, Path B when the agent captures them), write them fully-scraped in one shot so workflow 02 has nothing left to do for that row. Then process any Gather Notes feedback into search-targeting updates.

## Prerequisites
- `.env` populated: `GOOGLE_SHEET_ID`, `GOOGLE_CREDENTIALS_PATH`
- `profile/career_profile.md` front matter has `search_targeting` (queries, exclusions, recency, target count) and `search_filters` (salary floor etc.) — the single source of truth for targeting; `tools/search_mcf.py` reads it
- Sheet structure and the note→diff governance pattern: see `workflows/README.md`

## Path A: MCF API search (preferred)
```bash
python3 tools/search_mcf.py
```
Queries the MyCareersFuture API with `search_targeting.mcf_queries`, applies all filters from the profile (experience ≤ max, salary floor, title exclusions, recency, expiry, status=open), and stops once `search_targeting.target_count` (currently 5) qualifying URLs have been added. CLI flags (`--max-exp`, `--recency-days`, `--salary-floor`, `--target-count`, `--dry-run`, `--limit`) override the profile per run.

The MCF API returns each job's **full description** and structured `title`/`company`/`salary`/dates alongside the fields used for filtering — nothing here needs a second fetch later. For each qualifying job, the tool writes a Raw Listings row with `Scrape Status="scraped"` **directly**: Text Scraped = the description (HTML-stripped), plus Job Title/Company/Salary/Date Posted/Date Closing already filled in. Workflow 02 Phase 1 only processes `Scrape Status="new"` rows, so these are simply never in its queue — no redundant Firecrawl scrape, no re-deriving facts already known via a Haiku guess.

Duplicates are skipped automatically (including rows previously marked `skip`).

## Path B: Agent-assisted web search
1. Use WebSearch for candidate URLs matching the profile criteria (sites: MCF, LinkedIn, JobStreet, Glassdoor, company career pages; include "fresh graduate" / "entry level" / "junior" / "associate" terms; collect direct listing URLs, not search pages)
   - **Warning:** Google `site:` searches cache MCF listings that may be years out of date — never trust them without step 2.
2. **Verify each URL via WebFetch:** posted within `search_targeting.recency_days` (currently 5 days — strict, don't round up); closing date in the future; ≤1 year experience required; title passes the exclusion list in `search_targeting`. Stop once you've gathered `search_targeting.target_count` (currently 5) qualifying URLs.
3. The WebFetch read already has everything workflow 02 would otherwise fetch again — capture it instead of discarding it. Write one row via the same prefetch mechanism Path A uses:
   ```bash
   python3 tools/write_to_sheet.py --tab "Raw Listings" --fields-json <path>
   ```
   where the JSON has `url`, `markdown` (the page text), and whichever of `job_title`/`company`/`salary`/`date_posted`/`application_deadline` you read off the page (blank ones just fall back to Haiku's own derivation at extraction time — partial capture is fine). This also sets `Scrape Status="scraped"` directly, same as Path A.

## Path C: Manual addition
Paste a URL into the Input URL column and set Scrape Status to `new`. No prefetch data exists for this path — the full workflow 02 pipeline runs on it. Picked up on the next `/extract-curate`.

## Found: who added this row
Every row a tool appends via `write_to_sheet.py` (Path A, or Path B whether captured or not) gets `Found="gather-listings"` stamped automatically. If you paste a URL straight into the sheet yourself (Path C), `Found` stays blank — fill in your own attribution by hand so it's clear the row didn't come through `/gather-listings`.

## Rate interest
Fill in the **Interest Rating** column (1-5, see `schema/sheets.yaml`'s `interest_rating:` block for scale meaning) on each newly gathered Raw Listings row — either right after gathering or during pre-scrape triage below. This feeds `/refresh-skills`' `Avg Interest Rating` column on Skills Freq (joined by URL), so rating consistently is what makes that signal useful.

## Feedback: process Gather Notes
The **Gather Notes** column on Raw Listings is where you leave why-I-am/am-not-drawn comments against gathered listings (interest *rating* now lives in its own column, above) — see `workflows/README.md`'s governance section for the general pattern. Specifics for this one:
1. Read rows where Gather Notes is non-blank and not already `✓ applied`
2. Distill into targeting edits: add/remove/rephrase `search_targeting.mcf_queries`, extend `excluded_title_words`/`excluded_title_substrings`, adjust the preference sections fit scoring reads
3. Show the diff, get approval, apply, prefix the note `✓ applied YYYY-MM-DD — `

## Pre-scrape triage
Before running `/extract-curate`, skim the new rows. Prefetched rows (Path A, and Path B when captured) now show Job Title/Company/Salary directly in Raw Listings, so you can judge fit without opening each link. Set Scrape Status to **`skip`** for any you don't want pursued. **Never delete a Raw Listings row** — kept rows are URL-dedupe memory that stops the same listing being re-gathered next run.

## Output
Rows in Raw Listings ready for Workflow 02 — some already at `Scrape Status="scraped"` with structured fields filled (Path A/B-with-capture), others at `"new"` awaiting a real scrape (Path B-without-capture, Path C). Targeting updates applied to the profile when Gather Notes warranted them.

## Edge Cases
- **LinkedIn**: blocks scrapers — add the URL anyway (Path C); workflow 02 flags it "unable to scrape" and you paste the text manually
- **MCF API read-timeouts**: transient — the tool skips the query and continues; re-run if too few results (timeout is 30s per query)
- **Aggregator/search-result pages**: only add direct listing URLs
- **Paywalled listings**: skip unless accessible without login
- Google `site:` search cache staleness — see Path B warning
