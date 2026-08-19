#!/usr/bin/env python3
"""Append or update a row in a named Google Sheet tab.

All columns are addressed BY HEADER NAME via schema/sheets.yaml + the live
header row (see tools/sheets_common.py) — never by letter. --set therefore
takes header names, e.g. --set "App Status=Applied". Formula columns and
columns not in the schema are refused.
"""
import sys
import json
import argparse
from datetime import date
from pathlib import Path
from sheets_common import get_sheets_service, Tab, load_schema, snake_header

# Raw Listings "Source" — friendly job-board names keyed by URL domain
SOURCE_DOMAINS = {
    "mycareersfuture.gov.sg": "MyCareersFuture",
    "jobstreet.com": "JobStreet",
    "jobleads.com": "JobLeads",
    "linkedin.com": "LinkedIn",
    "glassdoor": "Glassdoor",
    "indeed.com": "Indeed",
    "careers.nus.edu.sg": "NUS Careers",
    "ntu.edu.sg": "NTU Careers",
    "jobs.careers.gov.sg": "Careers@Gov",
}


def source_from_url(url: str) -> str:
    """Friendly job-board name for a known domain; any other domain (a
    company's own career page — Workday, Greenhouse, etc.) is a 'Company
    Portal' rather than a raw, technical-looking hostname."""
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower()
    for domain, name in SOURCE_DOMAINS.items():
        if domain in host:
            return name
    return "Company Portal"


def load_scraped_text(path_str: str) -> str:
    """Read scraped text from a scrape_listing JSON or a plain .txt file."""
    path = Path(path_str)
    if path.suffix == ".json":
        return json.loads(path.read_text()).get("markdown", "")
    return path.read_text()


def parse_set_args(sets: list[str], tab: Tab) -> dict[str, str]:
    """Parse repeatable --set "Header=value" args, validating against schema."""
    cells = {}
    for s in sets:
        header, sep, value = s.partition("=")
        header = header.strip()
        if not sep or not header:
            sys.exit(f'Bad --set (expected "Header name=value"): {s}')
        if len(header) <= 2 and tab.header_spec(header) is None:
            sys.exit(f"--set now takes header names, not column letters: {s!r}. "
                     f"Writable headers on '{tab.name}': "
                     + ", ".join(h["name"] for h in tab.spec["headers"]
                                 if h["kind"] != "formula"))
        tab.assert_writable(header)
        cells[header] = value
    return cells


def fields_to_cells(fields: dict, tab: Tab) -> dict[str, str]:
    """Map an extract_fields JSON object onto Curated headers via the schema's
    `field:` mappings; list values are comma-joined, append defaults applied."""
    cells = {}
    for h in tab.spec["headers"]:
        if "append_default" in h:
            cells[h["name"]] = h["append_default"]
        elif "field" in h:
            value = fields.get(h["field"])
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            cells[h["name"]] = "" if value is None else str(value)
    return cells


def read_row_by_number(tab: Tab, row_num: int) -> dict[str, str]:
    """Snake-cased header→value dict for a single row (targeted range read,
    no full-tab fetch)."""
    result = tab.service.spreadsheets().values().get(
        spreadsheetId=tab.sheet_id, range=f"'{tab.name}'!{row_num}:{row_num}",
    ).execute()
    values = result.get("values", [[]])
    row = values[0] if values else []
    return dict(zip([snake_header(h) for h in tab.live_headers], row))


def backfill_raw_from_fields(service, fields: dict) -> int:
    """After a Curated Listings write, fill in any still-blank gather-time
    prefetch cells (Job Title/Company/Salary/Date Posted/Date Closing, plus
    Source) on the matching Raw Listings row — Curated's extraction just
    derived the same facts those `field:`-mapped Raw Listings columns exist
    to hold, for listings that went through scrape-then-extract rather than
    Path A/B prefetch; Source is filled the same deterministic way tool
    appends set it (source_from_url), no extraction dependency. Never
    overwrites a cell that's already non-blank (prefetched at gather time,
    or hand-edited). Never touches 'Found' — that's a gather-time-only
    signal. Returns the number of cells written."""
    url = fields.get("url", "")
    if not url:
        return 0
    raw_tab = Tab(service, "Raw Listings")
    row_num = raw_tab.find_row(url)
    if row_num is None:
        return 0
    candidate = fields_to_cells(fields, raw_tab)
    candidate["Source"] = source_from_url(url)
    current = read_row_by_number(raw_tab, row_num)
    to_write = {h: v for h, v in candidate.items()
                if v and not current.get(snake_header(h), "").strip()}
    if to_write:
        raw_tab.write_cells(row_num, to_write)
        print(f"Backfilled Raw Listings row {row_num}: "
              + ", ".join(f"{h}={v!r}" for h, v in to_write.items()))
    return len(to_write)


def backfill_defaults(tab: Tab, cells: dict[str, str]):
    """Fill each given column only where blank, on every row with a key value."""
    rows = tab.read_rows()
    from sheets_common import snake_header
    filled = 0
    for i, row in enumerate(rows):
        row_num = i + 2
        if not row.get(snake_header(tab.key_header), "").strip():
            continue
        to_write = {h: v for h, v in cells.items()
                    if not row.get(snake_header(h), "").strip()}
        if to_write:
            tab.write_cells(row_num, to_write, raw=True)
            filled += len(to_write)
    print(f"Backfill: filled {filled} cell(s) across {tab.name}"
          if filled else "Backfill: nothing to do (all cells already set)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tab", required=True, help="Sheet tab name")
    parser.add_argument("--data", help="Path to scrape_listing JSON (.json) or plain text (.txt) for manually-copied listings")
    parser.add_argument("--fields-json", help="Path to a fields JSON: extract_fields output (Curated Listings) "
                        "or a gather-time prefetch payload with url/markdown/known fields (Raw Listings)")
    parser.add_argument("--url", default="", help="URL to write or look up")
    parser.add_argument("--status", default="new", help="Scrape Status value to write (Raw Listings)")
    parser.add_argument("--update-url", help="Update existing row matching this URL in the tab's key column")
    parser.add_argument("--set", action="append", default=[], metavar="HEADER=VALUE",
                        help='Set a cell on the matched row by header name, e.g. --set "App Status=Applied" (repeatable)')
    parser.add_argument("--raw", action="store_true",
                        help="Write --set values as RAW (no Sheets type coercion)")
    parser.add_argument("--backfill-defaults", action="store_true",
                        help="Fill each --set HEADER=VALUE into every keyed row where that cell is blank")
    args = parser.parse_args()

    service = get_sheets_service()
    tab = Tab(service, args.tab)
    today = date.today().isoformat()

    # Generic header-keyed writes work on any schema tab
    if args.set:
        cells = parse_set_args(args.set, tab)
        if args.backfill_defaults:
            backfill_defaults(tab, cells)
        elif args.update_url:
            row_num = tab.find_row(args.update_url)
            if row_num is None:
                sys.exit(f"URL not found in {tab.name}: {args.update_url}")
            tab.write_cells(row_num, cells, raw=args.raw)
            print(f"Updated '{tab.name}' row {row_num}: "
                  + ", ".join(f"{h}={v!r}" for h, v in cells.items()))
        else:
            sys.exit("Provide --update-url <url> or --backfill-defaults with --set")

    elif args.tab == "Raw Listings":
        if args.update_url:
            # Post-scrape update: text, date, status
            if not args.data:
                sys.exit("Provide --data for --update-url mode")
            cells = {
                "Text Scraped": load_scraped_text(args.data),
                "Date Scraped": today,
                "Scrape Status": args.status,
            }
            row_num = tab.find_row(args.update_url)
            if row_num is None:
                print(f"URL not found in '{tab.name}', appending as new row instead.", file=sys.stderr)
                cells["Input URL"] = args.update_url
                cells["Source"] = source_from_url(args.update_url)
                cells["Found"] = "gather-listings"
                row_num = tab.append_row(cells)
                print(f"Appended row {row_num} to '{tab.name}'")
            else:
                tab.write_cells(row_num, cells)
                print(f"Updated row {row_num} in '{tab.name}'")
        elif args.url:
            # Gather path: append URL-only row, skip duplicates
            existing = tab.find_row(args.url)
            if existing:
                print(f"Skipped (already exists at row {existing}): {args.url}")
            else:
                row_num = tab.append_row({
                    "Input URL": args.url,
                    "Scrape Status": "new",
                    "Source": source_from_url(args.url),
                    "Found": "gather-listings",
                })
                print(f"Appended row {row_num} to '{tab.name}'")
        elif args.fields_json:
            # Prefetch path: the source already gave us the full text + known
            # structured fields (MCF API search, or an agent WebFetch read) —
            # write a fully-scraped row in one shot so this URL never enters
            # workflow 02 Phase 1's scrape queue (which only reads
            # Scrape Status="new"). Payload: {"url", "markdown", plus any of
            # job_title/company/salary/date_posted/application_deadline —
            # same key names extract_fields.py returns, so blank ones simply
            # fall back to Haiku's own derivation at extraction time.
            fields = json.loads(Path(args.fields_json).read_text())
            url = fields.get("url", "")
            if not url:
                sys.exit("--fields-json payload for Raw Listings must include 'url'")
            existing = tab.find_row(url)
            if existing:
                print(f"Skipped (already exists at row {existing}): {url}")
                sys.exit(0)
            cells = {
                "Input URL": url,
                "Text Scraped": fields.get("markdown", ""),
                "Date Scraped": today,
                "Scrape Status": "scraped",
                "Source": source_from_url(url),
                "Found": "gather-listings",
            }
            cells.update(fields_to_cells(fields, tab))  # Job Title/Company/Salary/Date Posted/Date Closing
            row_num = tab.append_row(cells)
            print(f"Appended row {row_num} to '{tab.name}' (prefetched — Scrape Status=scraped)")
        else:
            sys.exit("Provide --url, --update-url, --fields-json, or --set for Raw Listings tab")

    elif args.tab == "Curated Listings":
        if not args.fields_json:
            sys.exit("Provide --fields-json (or --set) for Curated Listings tab")
        fields = json.loads(Path(args.fields_json).read_text())
        # Skip if this URL is already curated — existing rows carry manual
        # Listing Status / Pre-Comments / edits and must never be touched
        url = fields.get("url", "")
        if url:
            existing = tab.find_row(url)
            if existing:
                print(f"Skipped (already curated at row {existing}): {url}")
                sys.exit(0)
        row_num = tab.append_row(fields_to_cells(fields, tab))
        print(f"Appended row {row_num} to '{tab.name}'")
        backfill_raw_from_fields(service, fields)

    else:
        sys.exit(f"No write mode for tab '{args.tab}': use --set (any schema tab), "
                 f"--url/--data/--update-url (Raw Listings), or --fields-json (Curated Listings)")
