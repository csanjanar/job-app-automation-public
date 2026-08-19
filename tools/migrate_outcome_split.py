#!/usr/bin/env python3
"""ONE-TIME migration: split the Tracker's App Status / Outcome control panel
(schema v3 → v4) and add the new derived columns.

Before (v3):
  - App Status carried lifecycle AND result (To Apply/Applied/Interview/Offer/Rejected/Closed)
  - Outcome held a DATE (consumed by the old 'Days > Post' formula)

After (v4):
  - App Status = lifecycle only (To Apply / Applied / Responded)
  - Outcome    = result status (Interview / Offer / Rejected / Closed)
  - Outcome Date (new) = the date the result landed  ← old Outcome's values move here
  - Apply Lag  = 'Days > Post' renamed, formula simplified to a single number
  - Follow-Up Due = 'Follow-Up Date' renamed (formula unchanged)
  - Salary (mo) (new formula) + Action Req. (new formula)

Handles two possible pre-migration states, detected from which of Outcome /
Outcome Date already exists live:
  A) clean v3 — 'Outcome' holds dates, no 'Outcome Date' yet → dates get moved
  B) already hand-split by a manual edit predating this tool — 'Outcome Date'
     already holds the dates, no 'Outcome' yet → nothing to move, 'Outcome' is
     added fresh and backfilled from the old terminal App Status values

What it does (aborts if already migrated — 'Apply Lag'/'Outcome'/'Action Req.'
present, 'Days > Post' gone; also aborts if both or neither of Outcome/Outcome
Date exist, since that's an ambiguous state needing manual reconciliation):
  1. Snapshots the whole Tracker tab to .tmp/tracker_snapshot_<ts>.json
  2. Renames the two formula headers in row 1 (in place)
  3. Appends the three new headers at the first free row-1 cells
  4. Backfills existing rows:
       [state A only] old Outcome date → Outcome Date (RAW, so the serial round-trips)
       old App Status ∈ {Interview,Offer,Rejected,Closed}
                         → Outcome = that value, App Status = 'Responded'
       (in state A, Outcome column is cleared first since it still holds raw dates)
  5. Writes the row-2 ARRAYFORMULAs (Apply Lag / Follow-Up Due / Salary (mo) / Action Req.)
  6. Sets data-validation dropdowns (App Status, Outcome), Outcome Date number format
  7. Applies conditional formatting (Action Req., Date Closing, Follow-Up Due, terminal rows)
  8. Re-reads and reports; the snapshot is the rollback point

Dry-run by default; pass --yes to apply. Idempotent guard prevents a second run.
Run tools/check_schema.py afterwards (expect OK), then tools/sync_tracker.py (expect no-op).
"""
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from sheets_common import get_sheets_service, sheet_id, Tab, col_to_letter, norm_header

RENAMES = {"Days > Post": "Apply Lag", "Follow-Up Date": "Follow-Up Due"}
BASE_NEW_HEADERS = ["Salary (mo)", "Action Req."]
TERMINAL = {"Interview", "Offer", "Rejected", "Closed"}   # old App Status values that are results

APP_STATUS_VOCAB = ["To Apply", "Applied", "Responded"]
OUTCOME_VOCAB = ["Interview", "Offer", "Rejected", "Closed"]

# Colours
RED = {"red": 0.80, "green": 0.0, "blue": 0.0}
GREY = {"red": 0.5, "green": 0.5, "blue": 0.5}
GREEN = {"red": 0.0, "green": 0.55, "blue": 0.0}
BG_RED = {"red": 0.96, "green": 0.80, "blue": 0.80}
BG_AMBER = {"red": 1.0, "green": 0.90, "blue": 0.60}
BG_FOLLOW = {"red": 1.0, "green": 0.85, "blue": 0.40}

RED_ACTIONS = ["Apply", "Follow up due", "Submit resume", "Send cover letter",
               "Generate docs", "Send follow-up", "Generate follow-up"]


def live_index(headers, name):
    """0-based index of a header (normalised match) in a live header list, or None."""
    target = norm_header(name)
    for i, h in enumerate(headers):
        if norm_header(h) == target:
            return i
    return None


def arrayformulas(tr: Tab) -> dict[str, str]:
    """Row-2 ARRAYFORMULAs keyed by header, built from live column letters."""
    L = tr.col_letter
    da, dp = L("Date Applied"), L("Date Posted")
    sal = L("Salary")
    url, oc = L("URL"), L("Outcome")
    res, cl, fu = L("Resume"), L("Cover Letter"), L("Follow-Up")
    app, fdue = L("App Status"), L("Follow-Up Due")

    apply_lag = (f'=ARRAYFORMULA(IF(({da}2:{da}="")+({dp}2:{dp}=""),"",'
                 f'DAYS({da}2:{da},{dp}2:{dp})))')

    follow_due = f'=ARRAYFORMULA(IF({da}2:{da}="","",WORKDAY({da}2:{da}+4,1)))'

    salary_mo = (rf'=ARRAYFORMULA(IF({sal}2:{sal}="","",IFERROR(ROUND('
                 rf'VALUE(REGEXREPLACE(REGEXEXTRACT({sal}2:{sal},"[\d,]+(?:\.\d+)?"),",",""))'
                 rf'/IF(REGEXMATCH(LOWER({sal}2:{sal}),"ann|/yr|year|p\.?a|per annum"),12,1)),"")))')

    action = (
        f'=ARRAYFORMULA(IF({url}2:{url}="","",'
        f'IF({oc}2:{oc}<>"","✓ "&{oc}2:{oc},'
        f'IF(({res}2:{res}="Generate")+({res}2:{res}="Change > Generate")'
        f'+({cl}2:{cl}="Generate")+({cl}2:{cl}="Change > Generate")>0,"Generate docs",'
        f'IF({res}2:{res}="Generated","Submit resume",'
        f'IF({cl}2:{cl}="Generated","Send cover letter",'
        f'IF({app}2:{app}="To Apply","Apply",'
        f'IF(({fu}2:{fu}<>"Not Required")*({fu}2:{fu}<>"Submitted")'
        f'*({fdue}2:{fdue}<>"")*(N({fdue}2:{fdue})<=TODAY())>0,"Follow up due",'
        f'IF({fu}2:{fu}="Generated","Send follow-up",'
        f'IF({fu}2:{fu}="Generate","Generate follow-up",'
        f'IF({app}2:{app}="Applied","Awaiting response",'
        f'"")))))))))))')

    return {"Apply Lag": apply_lag, "Follow-Up Due": follow_due,
            "Salary (mo)": salary_mo, "Action Req.": action}


def formatting_requests(tr: Tab, tab_id: int) -> list[dict]:
    """Conditional-format + data-validation + number-format batchUpdate requests."""
    idx = tr.col_index

    def col_range(header, start_row=1):
        c = idx(header)
        return {"sheetId": tab_id, "startRowIndex": start_row,
                "startColumnIndex": c, "endColumnIndex": c + 1}

    reqs = []

    # ── data validation dropdowns ─────────────────────────────────────────
    for header, vocab in (("App Status", APP_STATUS_VOCAB), ("Outcome", OUTCOME_VOCAB)):
        reqs.append({"setDataValidation": {
            "range": col_range(header),
            "rule": {"condition": {"type": "ONE_OF_LIST",
                                   "values": [{"userEnteredValue": v} for v in vocab]},
                     "strict": False, "showCustomUi": True}}})

    # ── Outcome Date number format ────────────────────────────────────────
    reqs.append({"repeatCell": {
        "range": col_range("Outcome Date"),
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "dd-mmm-yy"}}},
        "fields": "userEnteredFormat.numberFormat"}})

    # ── Action Req. text colours ──────────────────────────────────────────
    ar = col_range("Action Req.")
    for val in RED_ACTIONS:
        reqs.append({"addConditionalFormatRule": {"index": 0, "rule": {
            "ranges": [ar],
            "booleanRule": {"condition": {"type": "TEXT_EQ",
                                          "values": [{"userEnteredValue": val}]},
                            "format": {"textFormat": {"foregroundColor": RED, "bold": True}}}}}})
    reqs.append({"addConditionalFormatRule": {"index": 0, "rule": {
        "ranges": [ar],
        "booleanRule": {"condition": {"type": "TEXT_EQ",
                                      "values": [{"userEnteredValue": "Awaiting response"}]},
                        "format": {"textFormat": {"foregroundColor": GREY}}}}}})
    reqs.append({"addConditionalFormatRule": {"index": 0, "rule": {
        "ranges": [ar],
        "booleanRule": {"condition": {"type": "TEXT_STARTS_WITH",
                                      "values": [{"userEnteredValue": "✓"}]},
                        "format": {"textFormat": {"foregroundColor": GREEN, "bold": True}}}}}})

    # ── Date Closing red (past) / amber (≤3 days) ─────────────────────────
    hc = col_to_letter(idx("Date Closing"))
    reqs.append({"addConditionalFormatRule": {"index": 0, "rule": {
        "ranges": [col_range("Date Closing")],
        "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [
            {"userEnteredValue": f'=AND(${hc}2<>"",${hc}2<TODAY())'}]},
            "format": {"backgroundColor": BG_RED}}}}})
    reqs.append({"addConditionalFormatRule": {"index": 0, "rule": {
        "ranges": [col_range("Date Closing")],
        "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [
            {"userEnteredValue": f'=AND(${hc}2<>"",${hc}2>=TODAY(),${hc}2-TODAY()<=3)'}]},
            "format": {"backgroundColor": BG_AMBER}}}}})

    # ── Follow-Up Due highlight when due & not sent/NA ────────────────────
    fd = col_to_letter(idx("Follow-Up Due"))
    ff = col_to_letter(idx("Follow-Up"))
    reqs.append({"addConditionalFormatRule": {"index": 0, "rule": {
        "ranges": [col_range("Follow-Up Due")],
        "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [
            {"userEnteredValue": f'=AND(${fd}2<>"",TODAY()>=${fd}2,'
                                 f'${ff}2<>"Submitted",${ff}2<>"Not Required")'}]},
            "format": {"backgroundColor": BG_FOLLOW}}}}})

    # ── Terminal rows (Outcome Rejected/Closed): dim + strikethrough whole row ──
    oc = col_to_letter(idx("Outcome"))
    last_col = len(tr.live_headers)
    reqs.append({"addConditionalFormatRule": {"index": 0, "rule": {
        "ranges": [{"sheetId": tab_id, "startRowIndex": 1,
                    "startColumnIndex": 0, "endColumnIndex": last_col}],
        "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [
            {"userEnteredValue": f'=OR(${oc}2="Rejected",${oc}2="Closed")'}]},
            "format": {"textFormat": {"foregroundColor": GREY, "strikethrough": True}}}}}})

    return reqs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="Apply (default: dry-run report)")
    parser.add_argument("--skip-formatting", action="store_true",
                        help="Skip dropdowns/number-format/conditional-formatting (structure + backfill + formulas only)")
    args = parser.parse_args()

    service = get_sheets_service()
    sid = sheet_id()
    tab = "Tracker"
    values = service.spreadsheets().values()

    tr = Tab(service, tab)
    live = list(tr.live_headers)

    # ── guard ─────────────────────────────────────────────────────────────
    if (live_index(live, "Apply Lag") is not None and live_index(live, "Days > Post") is None
            and live_index(live, "Outcome") is not None and live_index(live, "Action Req.") is not None):
        sys.exit("Tracker already has Apply Lag/Outcome/Action Req. with no Days > Post — "
                 "already migrated. Nothing to do.")
    for old in RENAMES:
        if live_index(live, old) is None:
            sys.exit(f"Expected column '{old}' not found in Tracker — sheet is not in the "
                     f"pre-migration (v3) state this tool handles. Aborting.")

    # 'Outcome' vs 'Outcome Date' can be in one of two pre-migration states:
    #   A) clean v3 — 'Outcome' holds dates, 'Outcome Date' doesn't exist yet (dates get moved)
    #   B) already hand-split by a manual edit predating this tool — 'Outcome Date' already
    #      holds the dates, 'Outcome' doesn't exist yet (nothing to move, add 'Outcome' fresh)
    has_outcome = live_index(live, "Outcome") is not None
    has_outcome_date = live_index(live, "Outcome Date") is not None
    if has_outcome and has_outcome_date:
        sys.exit("Tracker has BOTH 'Outcome' and 'Outcome Date' already — ambiguous "
                 "pre-migration state, needs manual reconciliation. Aborting.")
    if not has_outcome and not has_outcome_date:
        sys.exit("Tracker has NEITHER 'Outcome' nor 'Outcome Date' — not a state this tool "
                 "recognises. Aborting.")
    move_dates = has_outcome and not has_outcome_date
    NEW_HEADERS = BASE_NEW_HEADERS + (["Outcome Date"] if move_dates else ["Outcome"])

    # ── snapshot ──────────────────────────────────────────────────────────
    before = values.get(spreadsheetId=sid, range=f"'{tab}'!A1:AZ").execute().get("values", [])
    before_raw = values.get(spreadsheetId=sid, range=f"'{tab}'!A1:AZ",
                            valueRenderOption="UNFORMATTED_VALUE").execute().get("values", [])
    snap = {"taken": datetime.now().isoformat(timespec="seconds"), "spreadsheet_id": sid,
            "values": before, "values_unformatted": before_raw,
            "row2_formulas": values.get(spreadsheetId=sid, range=f"'{tab}'!2:2",
                                        valueRenderOption="FORMULA").execute().get("values", [])}
    snap_path = Path(".tmp") / f"tracker_snapshot_{datetime.now():%Y%m%d_%H%M%S}.json"
    snap_path.parent.mkdir(exist_ok=True)
    snap_path.write_text(json.dumps(snap, indent=2))
    print(f"Snapshot saved: {snap_path} ({len(before)} rows)")

    n_rows = max(len(before), 1)
    a_idx = live_index(live, "App Status")
    old_app = [(r[a_idx] if a_idx < len(r) else "") for r in before[1:]]
    to_responded = sum(1 for v in old_app if str(v).strip() in TERMINAL)
    if move_dates:
        o_idx = live_index(live, "Outcome")
        old_out_raw = [(r[o_idx] if o_idx < len(r) else "") for r in before_raw[1:]]
        dates_moved = sum(1 for v in old_out_raw if str(v).strip() != "")
    else:
        old_out_raw, dates_moved = [], 0

    if not args.yes:
        if move_dates:
            print(f"[dry-run] Would: rename {RENAMES}; append {NEW_HEADERS}; "
                  f"move {dates_moved} Outcome date(s) → Outcome Date; set {to_responded} row(s) "
                  f"App Status→'Responded' with the result copied to Outcome; write 4 ARRAYFORMULAs; "
                  f"{'skip' if args.skip_formatting else 'apply'} validation/format. "
                  f"Re-run with --yes to migrate.")
        else:
            print(f"[dry-run] 'Outcome Date' already present (pre-existing manual split) — "
                  f"nothing to move. Would: rename {RENAMES}; append {NEW_HEADERS}; set "
                  f"{to_responded} row(s) App Status→'Responded' with the result copied to the "
                  f"new Outcome column; write 4 ARRAYFORMULAs; "
                  f"{'skip' if args.skip_formatting else 'apply'} validation/format. "
                  f"Re-run with --yes to migrate.")
        return

    # ── 1. rename headers in place ────────────────────────────────────────
    rename_data = []
    for old, new in RENAMES.items():
        c = live_index(live, old)
        rename_data.append({"range": f"'{tab}'!{col_to_letter(c)}1", "values": [[new]]})
        live[c] = new
    values.batchUpdate(spreadsheetId=sid,
                       body={"valueInputOption": "RAW", "data": rename_data}).execute()

    # ── 2. append new headers at the first free row-1 cells ───────────────
    start = len(live)
    end = col_to_letter(start + len(NEW_HEADERS) - 1)
    values.update(spreadsheetId=sid, range=f"'{tab}'!{col_to_letter(start)}1:{end}1",
                  valueInputOption="RAW", body={"values": [NEW_HEADERS]}).execute()
    print(f"Renamed {list(RENAMES.items())}; appended {NEW_HEADERS}")

    # fresh header map now that structure is final
    tr = Tab(service, tab)
    L = tr.col_letter
    out_col, app_col = L("Outcome"), L("App Status")

    # ── 3. backfill (order matters: read-old already captured above) ──────
    if move_dates:
        # a) old Outcome dates → Outcome Date (RAW so serials round-trip)
        od_col = L("Outcome Date")
        values.update(spreadsheetId=sid, range=f"'{tab}'!{od_col}2:{od_col}{n_rows}",
                      valueInputOption="RAW",
                      body={"values": [[v] for v in old_out_raw]}).execute()
        # b) clear old Outcome (still holds raw dates), then write derived result status below
        values.clear(spreadsheetId=sid, range=f"'{tab}'!{out_col}2:{out_col}{n_rows}").execute()
    new_out, new_app = [], []
    for v in old_app:
        s = str(v).strip()
        new_out.append([s] if s in TERMINAL else [""])
        new_app.append(["Responded"] if s in TERMINAL else [v])
    values.batchUpdate(spreadsheetId=sid, body={"valueInputOption": "RAW", "data": [
        {"range": f"'{tab}'!{out_col}2:{out_col}{n_rows}", "values": new_out},
        {"range": f"'{tab}'!{app_col}2:{app_col}{n_rows}", "values": new_app},
    ]}).execute()
    if move_dates:
        print(f"Backfilled: {dates_moved} date(s) → Outcome Date, "
              f"{to_responded} row(s) → App Status 'Responded'")
    else:
        print(f"'Outcome Date' left untouched (already correct); backfilled "
              f"{to_responded} row(s) into new Outcome column, App Status → 'Responded'")

    # ── 4. row-2 ARRAYFORMULAs (USER_ENTERED) ─────────────────────────────
    fdata = [{"range": f"'{tab}'!{L(h)}2", "values": [[f]]}
             for h, f in arrayformulas(tr).items()]
    values.batchUpdate(spreadsheetId=sid,
                       body={"valueInputOption": "USER_ENTERED", "data": fdata}).execute()
    print("Wrote ARRAYFORMULAs: Apply Lag, Follow-Up Due, Salary (mo), Action Req.")

    # ── 5. validation + formatting ────────────────────────────────────────
    if not args.skip_formatting:
        tab_id = next(s["properties"]["sheetId"]
                      for s in service.spreadsheets().get(spreadsheetId=sid).execute()["sheets"]
                      if s["properties"]["title"] == tab)
        service.spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": formatting_requests(tr, tab_id)}).execute()
        print("Applied dropdowns, Outcome Date format, and conditional formatting")

    # ── 6. verify vocab ───────────────────────────────────────────────────
    after = values.get(spreadsheetId=sid, range=f"'{tab}'").execute().get("values", [])
    hdr = after[0]
    ai, oi = live_index(hdr, "App Status"), live_index(hdr, "Outcome")
    bad = []
    for i, r in enumerate(after[1:], start=2):
        a = (r[ai] if ai < len(r) else "").strip()
        o = (r[oi] if oi < len(r) else "").strip()
        if a and a not in APP_STATUS_VOCAB:
            bad.append(f"  row {i}: App Status '{a}' not in {APP_STATUS_VOCAB}")
        if o and o not in OUTCOME_VOCAB:
            bad.append(f"  row {i}: Outcome '{o}' not in {OUTCOME_VOCAB}")
    if bad:
        print(f"WARNING: {len(bad)} cell(s) outside the new vocab "
              f"(snapshot {snap_path} is the rollback point):", file=sys.stderr)
        print("\n".join(bad), file=sys.stderr)
    else:
        print("Verified: all App Status / Outcome values conform to the v4 vocab.")

    print("\nDone. Next: python3 tools/check_schema.py  (expect OK), then "
          "python3 tools/sync_tracker.py  (expect a no-op).")


if __name__ == "__main__":
    main()
