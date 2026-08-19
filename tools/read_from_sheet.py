#!/usr/bin/env python3
"""Read rows from a named Google Sheet tab. Outputs JSON.

Row keys are snake_cased live headers (e.g. "Docs (Link)" → docs_link) via
tools/sheets_common.py, so output keys track the sheet, not hardcoded letters.
"""
import sys
import json
import argparse
from pathlib import Path
from sheets_common import get_sheets_service, Tab

# Status lives under a tab-specific header: Raw Listings "Scrape Status",
# Curated Listings "Listing Status", Tracker "App Status".
STATUS_KEYS = ["status", "scrape_status", "listing_status", "app_status"]


def row_status(row: dict) -> str:
    for key in STATUS_KEYS:
        if key in row:
            return row[key]
    return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tab", default="Curated Listings")
    parser.add_argument("--company", help="Filter by company name (case-insensitive)")
    parser.add_argument("--role", help="Filter by job title (case-insensitive)")
    parser.add_argument("--status", help="Filter by the tab's status column (Scrape/Listing/App Status), case-insensitive, e.g. 'apply', 'new', 'scraped'")
    parser.add_argument("--url", help="Filter by exact URL match (case-insensitive)")
    parser.add_argument("--first", action="store_true",
                        help="Output the first matching row as a single JSON object (not an array); exit 1 if no match")
    parser.add_argument("--out", help="Save output to this JSON file path")
    args = parser.parse_args()

    rows = Tab(get_sheets_service(), args.tab).read_rows()

    if args.company:
        rows = [r for r in rows if args.company.lower() in r.get("company", "").lower()]
    if args.role:
        rows = [r for r in rows if args.role.lower() in r.get("job_title", "").lower()]
    if args.status:
        rows = [r for r in rows if row_status(r).strip().lower() == args.status.strip().lower()]
    if args.url:
        rows = [r for r in rows if (r.get("url") or r.get("input_url", "")).strip().lower() == args.url.strip().lower()]

    if args.first:
        if not rows:
            print("No matching row found", file=sys.stderr)
            sys.exit(1)
        output = json.dumps(rows[0], indent=2)
        saved_msg = f"Saved 1 row (object) to {args.out}"
    else:
        output = json.dumps(rows, indent=2)
        saved_msg = f"Saved {len(rows)} rows to {args.out}"

    if args.out:
        Path(args.out).write_text(output)
        print(saved_msg, file=sys.stderr)
    else:
        print(output)
