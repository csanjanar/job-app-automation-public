#!/usr/bin/env python3
"""ONE-TIME migration: replace Tracker's live QUERY (A1) with static values.

Why: the QUERY realigned rows whenever Curated changed, while K onward stayed
positional — one deleted Curated row silently corrupted every Tracker row
below it. After this migration, tools/sync_tracker.py appends new 'apply'
rows keyed by URL and nothing ever realigns.

What it does (aborts if A1 holds no QUERY — i.e. already migrated):
  1. Snapshots the whole Tracker tab (values + row-1/2 formulas) to
     .tmp/tracker_snapshot_<timestamp>.json
  2. Captures the QUERY's displayed A1:J block
  3. Clears A1, writes the headers and data back as static values —
     except 'Posted' (B) and 'Closing' (I), which become local ARRAYFORMULAs
     over this tab's own Date Posted (G) / Date Closing (H)
  4. Re-reads A:J and diffs against the pre-migration block, cell by cell

Curated 'App Status' (S) VLOOKUP into Tracker!A:K is URL-keyed and unaffected.
Run tools/sync_tracker.py afterwards — it must report a no-op.
"""
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from sheets_common import get_sheets_service, sheet_id, Tab, col_to_letter

# Local replacements for the QUERY-fed Curated T/U mirrors (same rendering),
# computed from Tracker's own Date Posted (G) / Date Closing (H)
POSTED_FORMULA = ('=ARRAYFORMULA(IF(G2:G="", "", '
                  'RIGHT("  " & DAYS(TODAY(), G2:G), 2) & " days ago"))')
CLOSING_FORMULA = ('=ARRAYFORMULA(IF(H2:H="", "", '
                   'IF(H2:H > TODAY(), "in " & (H2:H - TODAY()) & " days", '
                   'IF(H2:H = TODAY(), "today", (TODAY() - H2:H) & " days ago"))))')
QUERY_COLS = 10  # A:J — the block the old QUERY produced
FORMULA_COLS = {1: POSTED_FORMULA, 8: CLOSING_FORMULA}  # 0-based: B, I
DATE_COLS = {6: "dd-mm-yy", 7: "dd-mmm"}  # G Date Posted, H Date Closing — display format for the RAW serials


def get_values(service, sid, rng, render="FORMATTED_VALUE"):
    return service.spreadsheets().values().get(
        spreadsheetId=sid, range=rng, valueRenderOption=render,
    ).execute().get("values", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="Actually migrate (default: dry-run report)")
    args = parser.parse_args()

    service = get_sheets_service()
    sid = sheet_id()

    a1 = get_values(service, sid, "'Tracker'!A1", render="FORMULA")
    a1_formula = (a1[0][0] if a1 and a1[0] else "")
    if not str(a1_formula).upper().startswith("=QUERY"):
        sys.exit("Tracker!A1 holds no QUERY — already migrated? Nothing to do.")

    before = get_values(service, sid, "'Tracker'!A1:Z")
    # UNFORMATTED round-trips exactly when written back RAW (dates stay serial
    # numbers; cell display formats are cell properties and survive). Writing
    # FORMATTED strings back USER_ENTERED does NOT round-trip (locale-ambiguous
    # date re-parsing → wrong dates / #VALUE!).
    before_raw = get_values(service, sid, "'Tracker'!A1:Z", render="UNFORMATTED_VALUE")
    snapshot = {
        "taken": datetime.now().isoformat(timespec="seconds"),
        "spreadsheet_id": sid,
        "a1_formula": a1_formula,
        "row2_formulas": get_values(service, sid, "'Tracker'!2:2", render="FORMULA"),
        "values": before,
        "values_unformatted": before_raw,
    }
    snap_path = Path(".tmp") / f"tracker_snapshot_{datetime.now():%Y%m%d_%H%M%S}.json"
    snap_path.parent.mkdir(exist_ok=True)
    snap_path.write_text(json.dumps(snapshot, indent=2))
    print(f"Snapshot saved: {snap_path} ({len(before)} rows)")

    n_rows = len(before)
    if not args.yes:
        print(f"[dry-run] Would freeze {n_rows - 1} data row(s) of A:J to static values, "
              f"replace B/I with local ARRAYFORMULAs, and remove the A1 QUERY. "
              f"Re-run with --yes to migrate.")
        return

    # 1. Clear the QUERY — the whole spilled A:J block disappears with it
    service.spreadsheets().values().clear(spreadsheetId=sid, range="'Tracker'!A1").execute()

    # 2. Static headers A1:J1 (as the QUERY displayed them)
    headers = [h.strip() for h in before[0][:QUERY_COLS]]
    service.spreadsheets().values().update(
        spreadsheetId=sid, range=f"'Tracker'!A1:{col_to_letter(QUERY_COLS - 1)}1",
        valueInputOption="RAW", body={"values": [headers]},
    ).execute()

    # 3. Static data for A:J except B/I, written column-by-column so the
    #    formula columns stay truly empty for the ARRAYFORMULA spill.
    #    RAW + unformatted values = exact round-trip.
    data = []
    for col in range(QUERY_COLS):
        if col in FORMULA_COLS:
            continue
        letter = col_to_letter(col)
        col_values = [[row[col] if col < len(row) else ""] for row in before_raw[1:]]
        data.append({"range": f"'Tracker'!{letter}2:{letter}{n_rows}", "values": col_values})
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sid, body={"valueInputOption": "RAW", "data": data},
    ).execute()
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sid,
        body={"valueInputOption": "USER_ENTERED",
              "data": [{"range": f"'Tracker'!{col_to_letter(col)}2", "values": [[formula]]}
                       for col, formula in FORMULA_COLS.items()]},
    ).execute()

    # 3b. Date serials need their display format re-applied (clearing the QUERY
    #     spill leaves plain number formatting on some cells)
    tab_sheet_id = next(
        s["properties"]["sheetId"]
        for s in service.spreadsheets().get(spreadsheetId=sid).execute()["sheets"]
        if s["properties"]["title"] == "Tracker")
    service.spreadsheets().batchUpdate(
        spreadsheetId=sid,
        body={"requests": [{
            "repeatCell": {
                # whole column below the header — future sync-appended rows inherit it
                "range": {"sheetId": tab_sheet_id, "startRowIndex": 1,
                          "startColumnIndex": col, "endColumnIndex": col + 1},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": pattern}}},
                "fields": "userEnteredFormat.numberFormat",
            }} for col, pattern in DATE_COLS.items()]},
    ).execute()

    # 4. Verify by UNDERLYING VALUE (not display string — the old QUERY spill
    #    had inconsistent per-cell date formats, so display can legitimately
    #    change while the value is identical)
    rng = f"'Tracker'!A1:{col_to_letter(QUERY_COLS - 1)}{n_rows}"
    after_raw = get_values(service, sid, rng, render="UNFORMATTED_VALUE")
    after_fmt = get_values(service, sid, rng)

    def cell(block, r, c):
        return block[r][c] if r < len(block) and c < len(block[r]) else ""

    value_diffs, display_notes = [], []
    for r in range(n_rows):
        for c in range(QUERY_COLS):
            if r > 0 and c in FORMULA_COLS:
                continue  # recomputed; checked via display below
            if str(cell(after_raw, r, c)).strip() != str(cell(before_raw, r, c)).strip():
                value_diffs.append(f"  {col_to_letter(c)}{r + 1}: "
                                   f"{cell(before_raw, r, c)!r} → {cell(after_raw, r, c)!r}")
    for r in range(n_rows):
        for c in range(QUERY_COLS):
            if str(cell(after_fmt, r, c)).strip() != str(cell(before, r, c)).strip():
                display_notes.append(f"  {col_to_letter(c)}{r + 1}: displayed "
                                     f"{cell(before, r, c)!r} → {cell(after_fmt, r, c)!r}")

    if value_diffs:
        print(f"ERROR: {len(value_diffs)} cell VALUE(s) differ after migration "
              f"(restore from {snap_path}):", file=sys.stderr)
        print("\n".join(value_diffs), file=sys.stderr)
        sys.exit(1)
    if display_notes:
        print(f"Note: {len(display_notes)} cell(s) changed display format only "
              f"(underlying values verified identical):")
        print("\n".join(display_notes))
    print(f"Migrated: {n_rows - 1} row(s) frozen to static values, B/I now local "
          f"ARRAYFORMULAs, all underlying values verified identical.")
    print("Next: python3 tools/sync_tracker.py  (must report a no-op)")


if __name__ == "__main__":
    main()
