#!/usr/bin/env python3
"""Sync Curated Listings 'apply' rows into the Tracker, keyed by URL.

Replaces the old live QUERY in Tracker!A1 (removed by migrate_tracker.py):
  - appends a Tracker row (static display values, from the schema's sync_from
    mappings) for every Curated row with Listing Status='apply' whose URL is
    not yet in Tracker
  - seeds seed_default values (App Status='To Apply', Resume='Required', ...)
    into blank cells on ALL keyed rows — absorbs workflow 03's old Phase 0
  - never deletes, reorders, or overwrites non-blank cells; deleting a Curated
    row or flipping apply→skip therefore no longer affects the Tracker

Run at the end of /extract-curate and the start of /generate-docs. Idempotent.
"""
import sys
import argparse
from sheets_common import get_sheets_service, Tab, snake_header


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    args = parser.parse_args()

    service = get_sheets_service()
    curated = Tab(service, "Curated Listings")
    tracker = Tab(service, "Tracker")

    sync_map = {h["name"]: h["sync_from"] for h in tracker.spec["headers"] if "sync_from" in h}
    seed_map = {h["name"]: h["seed_default"] for h in tracker.spec["headers"] if "seed_default" in h}

    # iso_dates: date cells cross tabs here — formatted strings are locale-ambiguous
    apply_rows = {r.get("url", "").strip(): r for r in curated.read_rows(iso_dates=True)
                  if r.get("listing_status", "").strip().lower() == "apply" and r.get("url", "").strip()}
    tracker_rows = tracker.read_rows()
    tracker_urls = {r.get("url", "").strip() for r in tracker_rows if r.get("url", "").strip()}

    # 1. Append missing apply rows (in Curated order, below existing rows)
    appended = 0
    for url, row in apply_rows.items():
        if url in tracker_urls:
            continue
        cells = {tr_header: row.get(snake_header(cu_header), "")
                 for tr_header, cu_header in sync_map.items()}
        cells.update(seed_map)
        if args.dry_run:
            print(f"[dry-run] would append: {row.get('job_title', '?')} @ {row.get('company', '?')} ({url})")
        else:
            row_num = tracker.append_row(cells)
            print(f"Appended Tracker row {row_num}: {row.get('job_title', '?')} @ {row.get('company', '?')}")
        appended += 1

    # 2. Seed defaults into blank cells on existing rows
    seeded = 0
    for i, row in enumerate(tracker_rows):
        if not row.get("url", "").strip():
            continue
        to_write = {h: v for h, v in seed_map.items() if not row.get(snake_header(h), "").strip()}
        if to_write:
            if args.dry_run:
                print(f"[dry-run] would seed row {i + 2}: {to_write}")
            else:
                tracker.write_cells(i + 2, to_write, raw=True)
            seeded += len(to_write)

    # 3. Informational: Tracker rows whose Curated counterpart is gone / not apply
    for url in sorted(tracker_urls - set(apply_rows)):
        print(f"Note: Tracker row has no Curated 'apply' counterpart (fine if deliberately "
              f"skipped/deleted in Curated): {url}", file=sys.stderr)

    print(f"Sync {'(dry-run) ' if args.dry_run else ''}done: "
          f"{appended} row(s) appended, {seeded} default cell(s) seeded, "
          f"{len(tracker_urls)} existing row(s) untouched.")


if __name__ == "__main__":
    main()
