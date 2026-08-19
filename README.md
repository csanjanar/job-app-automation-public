# Job Application Automation

An AI-agent-driven pipeline that finds job listings, curates and scores them against your profile, tracks applications end to end, and generates tailored resumes/cover letters — built on a "Workflows, Agents, Tools" (WAT) architecture designed for reliability, not just automation.

> **This is a sanitized public replica.** All personal data — name, contact details, employers, salary figures, project links — is fictional demo content (`Alex Tan`). It exists so the architecture, prompts, and pipeline logic are inspectable and forkable without exposing anyone's real job search.

## Why this exists

Job searching is a five-to-ten-step pipeline repeated dozens of times: find a listing, decide if it's worth pursuing, track it, tailor a resume and cover letter, follow up, learn from the outcome. Handing all of that to a single AI agent sounds appealing, but compounding error rates make it fragile — an agent that's 90% accurate at any one step is only 59% likely to get all five right in sequence. This project instead separates **reasoning** (deciding what to do) from **execution** (doing it), so each stays independently reliable.

## Architecture: Workflows, Agents, Tools

| Layer | What it is | Role |
|---|---|---|
| **Workflows** | Markdown SOPs in [`workflows/`](workflows/) | Define objective, inputs, steps, outputs, and edge cases for each stage — the same way you'd brief a teammate |
| **Agents** | Claude Code, invoked via slash commands | Reads the relevant workflow, calls tools in the right order, handles failures, asks for approval on judgment calls — never does the deterministic work itself |
| **Tools** | Python scripts in [`tools/`](tools/) | API calls, scraping, LLM extraction, sheet reads/writes, LaTeX compilation — deterministic, testable, fast |

Every tool addresses spreadsheet columns **by header name**, resolved against [`schema/sheets.yaml`](schema/sheets.yaml) — the single source of truth for tab structure, status vocabularies, and classification vocabularies. Reordering or adding columns never breaks a tool; a schema change and the tool/workflow change it enables ship in the same commit.

Anywhere the system would otherwise silently rewrite something that drives fit scoring, targeting, or generated documents (profile edits, alias tables), it instead proposes a diff for **explicit approval** first. Nothing auto-applies to files that shape future output.

## Pipeline

| Command | Workflow | What it does |
|---|---|---|
| `/gather-listings` | [01](workflows/01_gather_listings.md) | Find candidate job URLs matching your profile's search targeting; log to Raw Listings |
| `/extract-curate` | [02](workflows/02_extract_and_curate.md) | Scrape, extract structured fields, compute a Fit Score, sync qualifying rows into the Tracker |
| `/generate-docs` | [03](workflows/03_generate_documents.md) | Generate tailored resume/cover letter/follow-up/app-question docs for Tracker rows that need them, compile to PDF, push to a docs repo |
| `/refresh-skills` | [04](workflows/04_refresh_skills.md) | Rebuild skill-frequency analysis from curated listings; surface skill gaps against your profile |
| `/review-outcomes` | [05](workflows/05_review_outcomes.md) | Aggregate application outcomes monthly; check whether Fit Scores are calibrated; promote recurring edits into templates |

All state lives in a Google Sheet (5 tabs: Raw Listings → Curated Listings → Tracker, plus Skills Raw / Skills Freq) so it's inspectable and editable by hand at any point — tools never assume they're the only writer.

## Tech stack

Python · [Anthropic Claude API](https://anthropic.com) · Google Sheets API · [Firecrawl](https://firecrawl.dev) · LaTeX ([tectonic](https://tectonic-typesetting.github.io)) for PDF generation.

## Quickstart

```bash
git clone <this-repo-url>
cd job-app-automation-public
pip install -r requirements.txt
brew install tectonic   # for resume PDF compilation
```

1. Copy `.env.example` → `.env` and fill in your own API keys (Anthropic, Firecrawl) and Google Sheet ID.
2. Set up a Google Cloud OAuth client, download `credentials.json` into the repo root (gitignored — never commit it).
3. Create a Google Sheet matching the tab/header structure in `schema/sheets.yaml`, or run `python3 tools/check_schema.py --fix` against an empty sheet to scaffold headers automatically.
4. The repo ships with a working fictional profile (`profile/career_profile.md`) and resume templates (`templates/*.tex`), so the pipeline runs out of the box as a demo. Replace the profile content with your own details, and adjust `templates/*.tex` to your own resume, before using it for real applications.
5. Run a workflow from Claude Code, e.g. `/gather-listings`.

## Repo structure

```
tools/          Deterministic Python scripts — one per pipeline step
workflows/      Markdown SOPs the agent reads before acting
schema/         sheets.yaml — source of truth for sheet tabs/headers/vocabularies
profile/        career_profile.md — drives targeting, fit scoring, doc generation
templates/      LaTeX resume templates (one per role family)
.claude/        Claude Code slash-command definitions
.env.example    Required environment variables (no real values)
```

`.tmp/` (scraped data, intermediate exports) and `applications/` (compiled resume PDFs) are gitignored — regenerated locally, never committed.

## Design notes

- **Schema as source of truth**: `schema/sheets.yaml` is versioned with a changelog; every structural change to the sheet is a diff to this file first, so the sheet and the LLM extraction prompt never disagree about categories.
- **Notes → approved diffs**: three places in the pipeline let you leave a freeform note in a sheet column (e.g. "skip listings like this"); a workflow phase turns it into a proposed edit to `profile/career_profile.md`, shown for approval before anything changes. Feedback shapes the system without ever silently rewriting it.
- **The self-improvement loop**: every failure — a rate limit, an unexpected API shape, a bad extraction — gets fixed in the tool and then written back into the workflow, so the same failure mode doesn't recur.

## Limitations

- Job search targeting is built around Singapore's [MyCareersFuture](https://www.mycareersfuture.gov.sg/) (MCF) API; adapting to another job board means rewriting `tools/search_mcf.py`'s search path.
- Scraping listings from arbitrary URLs goes through Firecrawl — respect the target site's terms of service.
- Requires your own API keys (Anthropic, Firecrawl, Google Cloud OAuth) — none are provided.
- All sample data in this repo (the profile, resume templates, project links) is fictional.

## License

[MIT](LICENSE)
