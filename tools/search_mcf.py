#!/usr/bin/env python3
"""
Search MyCareersFuture API for entry-level AI/ML/NLP/Data Science listings
and write qualifying URLs to the Raw Listings sheet.

Queries and filters come from profile/career_profile.md front matter
(search_targeting + search_filters.salary_floor_sgd_monthly) — the profile
is the single source of truth for targeting; CLI args override per run.
Workflow 01's Gather Notes feedback phase is how targeting evolves.

Filters applied:
  - minimumYearsExperience <= max_years_experience
  - posting date within recency_days
  - expiry date in the future
  - job title must not contain excluded words/substrings
  - salary >= salary floor (if stated)

Each qualifying job is written as a FULLY-SCRAPED Raw Listings row (Scrape
Status="scraped" directly, not "new") — the MCF search API already returns
the complete listing description plus structured title/company/salary/dates
for free, so workflow 02 never needs to re-scrape or re-derive them via
Haiku for these rows. See schema/sheets.yaml changelog v3.
"""
import re
import sys
import html
import json
import argparse
import subprocess
from pathlib import Path
from datetime import date

import requests
from profile_common import load_frontmatter

MCF_API = "https://api.mycareersfuture.gov.sg/v2/jobs"
PREFETCH_SCRATCH = Path(".tmp/mcf_prefetch.json")

_profile = load_frontmatter()
_targeting = _profile.get("search_targeting", {})
if not _targeting.get("mcf_queries"):
    sys.exit("No search_targeting.mcf_queries in profile/career_profile.md front matter")

EXCLUDED_TITLE_WORDS = {w.lower() for w in _targeting.get("excluded_title_words", [])}
EXCLUDED_TITLE_SUBSTRINGS = [s.lower() for s in _targeting.get("excluded_title_substrings", [])]
SEARCH_QUERIES = _targeting["mcf_queries"]
DEFAULT_MAX_EXP = _targeting.get("max_years_experience", 1)
DEFAULT_RECENCY_DAYS = _targeting.get("recency_days", 30)
DEFAULT_SALARY_FLOOR = _profile.get("search_filters", {}).get("salary_floor_sgd_monthly", 4500)
DEFAULT_TARGET_COUNT = _targeting.get("target_count", 5)


def is_title_excluded(title: str) -> bool:
    lower = title.lower()
    words = re.split(r"[\s/\-]+", lower)
    if set(words) & EXCLUDED_TITLE_WORDS:
        return True
    return any(sub in lower for sub in EXCLUDED_TITLE_SUBSTRINGS)


def strip_html(text: str) -> str:
    """MCF's description field is HTML — turn it into plain-enough prose for
    Haiku (block boundaries become newlines so list items/paragraphs don't
    run together; doesn't need to be pretty, just parseable)."""
    if not text:
        return ""
    text = re.sub(r"</(p|li|div|h[1-6])>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


# MCF's salaryType is an adjective ("Monthly") — Curated Listings' existing
# convention is "per <period noun>" ("per month"), so map rather than lowercase.
SALARY_PERIODS = {"monthly": "month", "annual": "year", "yearly": "year",
                  "hourly": "hour", "daily": "day", "weekly": "week"}


def format_salary(salary: dict) -> str:
    """Match the 'S$X - S$Y per Type' convention Curated Listings already uses."""
    if not salary:
        return ""
    lo, hi = salary.get("minimum"), salary.get("maximum")
    stype = ((salary.get("type") or {}).get("salaryType") or "").lower()
    period = SALARY_PERIODS.get(stype, stype)
    suffix = f" per {period}" if period else ""
    if lo and hi and lo != hi:
        return f"S${lo:,} - S${hi:,}{suffix}"
    val = lo or hi
    return f"S${val:,}{suffix}" if val else ""


def search(query: str, limit: int = 40) -> list[dict]:
    resp = requests.get(MCF_API, params={"search": query, "limit": limit},
                        headers={"Accept": "application/json"}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def is_valid(job: dict, max_exp: int, recency_days: int, salary_floor: int) -> tuple[bool, str]:
    today = date.today()

    meta = job.get("metadata", {})
    expiry = meta.get("expiryDate")
    posted = meta.get("newPostingDate")
    url = meta.get("jobDetailsUrl", "")
    title = job.get("title", "")
    exp = job.get("minimumYearsExperience") or 0
    status = (job.get("status") or {}).get("jobStatus", "")

    if status.lower() != "open":
        return False, f"status={status}"

    if is_title_excluded(title):
        return False, f"title excluded: {title}"

    if exp > max_exp:
        return False, f"experience={exp}y > {max_exp}y"

    if expiry:
        exp_date = date.fromisoformat(expiry)
        if exp_date < today:
            return False, f"expired {expiry}"

    if posted:
        post_date = date.fromisoformat(posted)
        if (today - post_date).days > recency_days:
            return False, f"posted {posted} > {recency_days}d ago"

    salary = job.get("salary") or {}
    sal_min = salary.get("minimum") or 0
    if sal_min and sal_min < salary_floor:
        return False, f"salary min={sal_min} < {salary_floor}"

    return True, "ok"


def write_prefetched(job: dict, url: str, dry_run: bool) -> None:
    """Write a fully-scraped Raw Listings row: description + known structured
    fields, so this URL skips workflow 02 Phase 1's scrape queue entirely."""
    if dry_run:
        print(f"  [dry-run] would write (prefetched): {url}")
        return
    company = ((job.get("postedCompany") or {}).get("name") or
               (job.get("hiringCompany") or {}).get("name") or "")
    meta = job.get("metadata") or {}
    payload = {
        "url": url,
        "markdown": strip_html(job.get("description", "")),
        "job_title": job.get("title", ""),
        "company": company,
        "salary": format_salary(job.get("salary") or {}),
        "date_posted": meta.get("newPostingDate", ""),
        "application_deadline": meta.get("expiryDate", ""),
    }
    PREFETCH_SCRATCH.parent.mkdir(parents=True, exist_ok=True)
    PREFETCH_SCRATCH.write_text(json.dumps(payload))
    result = subprocess.run(
        ["python3", "tools/write_to_sheet.py", "--tab", "Raw Listings",
         "--fields-json", str(PREFETCH_SCRATCH)],
        capture_output=True, text=True
    )
    msg = result.stdout.strip() or result.stderr.strip()
    print(f"  {msg}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-exp", type=int, default=DEFAULT_MAX_EXP,
                        help=f"Max years of experience required (profile default: {DEFAULT_MAX_EXP})")
    parser.add_argument("--recency-days", type=int, default=DEFAULT_RECENCY_DAYS,
                        help=f"Only include listings posted within this many days (profile default: {DEFAULT_RECENCY_DAYS})")
    parser.add_argument("--salary-floor", type=int, default=DEFAULT_SALARY_FLOOR,
                        help=f"Min monthly salary in SGD (profile default: {DEFAULT_SALARY_FLOOR})")
    parser.add_argument("--target-count", type=int, default=DEFAULT_TARGET_COUNT,
                        help=f"Stop once this many qualifying URLs are added (profile default: {DEFAULT_TARGET_COUNT}; 0 = no cap)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print URLs without writing to sheet")
    parser.add_argument("--limit", type=int, default=40,
                        help="Results to fetch per query (default: 40)")
    args = parser.parse_args()

    seen_uuids: set[str] = set()
    added = 0

    for query in SEARCH_QUERIES:
        if args.target_count and added >= args.target_count:
            print(f"\nTarget of {args.target_count} reached — stopping before {query!r}")
            break
        print(f"\nSearching: {query!r}")
        try:
            jobs = search(query, limit=args.limit)
        except Exception as e:
            print(f"  Error: {e}")
            continue

        for job in jobs:
            if args.target_count and added >= args.target_count:
                break
            uuid = job.get("uuid", "")
            if uuid in seen_uuids:
                continue
            seen_uuids.add(uuid)

            url = (job.get("metadata") or {}).get("jobDetailsUrl", "")
            if not url:
                continue

            ok, reason = is_valid(job, args.max_exp, args.recency_days, args.salary_floor)
            title = job.get("title", "?")
            exp = job.get("minimumYearsExperience", 0)
            posted = (job.get("metadata") or {}).get("newPostingDate", "?")
            expiry = (job.get("metadata") or {}).get("expiryDate", "?")

            if ok:
                company = ((job.get("postedCompany") or {}).get("name") or
                           (job.get("hiringCompany") or {}).get("name") or "?")
                print(f"  + [{title}] @ {company} | exp={exp}y | posted={posted} | closes={expiry}")
                write_prefetched(job, url, args.dry_run)
                added += 1
            else:
                print(f"  - [{title}] SKIP: {reason}")

    cap_note = f" (target {args.target_count})" if args.target_count else ""
    print(f"\nDone. {added} listings {'would be ' if args.dry_run else ''}added to Raw Listings{cap_note}.")


if __name__ == "__main__":
    main()
