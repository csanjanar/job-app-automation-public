#!/usr/bin/env python3
"""ONE-TIME migration: remove the Tracker 'Follow-Up Due' column (schema v8 → v9).

'Follow-Up Due' was a visible ARRAYFORMULA column (WORKDAY(Date Applied+4,1))
that 'Action Req.' referenced to compute its "Follow up due" reminder tier, and
that had its own conditional-format highlight rule. Removing the column without
also touching those would leave Action Req. pointing at a deleted column
(#REF!) and an orphaned conditional-format rule.

What it does (aborts if 'Follow-Up Due' is already gone — already migrated):
  1. Snapshots the whole Tracker tab to .tmp/tracker_snapshot_<ts>.json
  2. Rewrites the 'Action Req.' ARRAYFORMULA (row 2) so its "Follow up due" tier
     computes WORKDAY(Date Applied+4,1) inline instead of reading the
     Follow-Up Due column — same reminder behaviour, no separate column needed
  3. Deletes any conditional-format rule whose range is exactly the
     'Follow-Up Due' column (the highlight rule from migrate_outcome_split.py)
  4. Deletes the 'Follow-Up Due' column itself
  5. Re-reads and reports; the snapshot is the rollback point

Dry-run by default; pass --yes to apply. Idempotent guard prevents a second run.
Run schema/sheets.yaml's v9 update + tools/check_schema.py afterwards (expect OK).
"""
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from sheets_common import get_sheets_service, sheet_id, Tab, col_to_letter, norm_header


def live_index(headers, name):
    target = norm_header(name)
    for i, h in enumerate(headers):
        if norm_header(h) == target:
            return i
    return None


def action_req_formula(tr: Tab) -> str:
    """Same logic as migrate_outcome_split.py's 'action' formula, but the
    'Follow up due' tier computes the due date inline from Date Applied
    instead of reading a separate Follow-Up Due column."""
    L = tr.col_letter
    da = L("Date Applied")
    url, oc = L("URL"), L("Outcome")
    res, cl, fu = L("Resume"), L("Cover Letter"), L("Follow-Up")
    app = L("App Status")

    fdue = f'IF({da}2:{da}="","",WORKDAY({da}2:{da}+4,1))'

    return (
        f'=ARRAYFORMULA(IF({url}2:{url}="","",'
        f'IF({oc}2:{oc}<>"","✓ "&{oc}2:{oc},'
        f'IF(({res}2:{res}="Generate")+({res}2:{res}="Change > Generate")'
        f'+({cl}2:{cl}="Generate")+({cl}2:{cl}="Change > Generate")>0,"Generate docs",'
        f'IF({res}2:{res}="Generated","Submit resume",'
        f'IF({cl}2:{cl}="Generated","Send cover letter",'
        f'IF({app}2:{app}="To Apply","Apply",'
        f'IF(({fu}2:{fu}<>"Not Required")*({fu}2:{fu}<>"Submitted")'
        f'*({fdue}<>"")*(N({fdue})<=TODAY())>0,"Follow up due",'
        f'IF({fu}2:{fu}="Generated","Send follow-up",'
        f'IF({fu}2:{fu}="Generate","Generate follow-up",'
        f'IF({app}2:{app}="Applied","Awaiting response",'
        f'"")))))))))))'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="Apply (default: dry-run report)")
    args = parser.parse_args()

    service = get_sheets_service()
    sid = sheet_id()
    tab = "Tracker"
    values = service.spreadsheets().values()

    tr = Tab(service, tab)
    live = list(tr.live_headers)

    fdue_idx = live_index(live, "Follow-Up Due")
    if fdue_idx is None:
        sys.exit("Tracker has no 'Follow-Up Due' column — already migrated. Nothing to do.")
    if live_index(live, "Action Req.") is None:
        sys.exit("Tracker has no 'Action Req.' column — not the state this tool expects. Aborting.")

    if not args.yes:
        print(f"[dry-run] Would: snapshot Tracker; rewrite 'Action Req.' to compute the "
              f"follow-up-due date inline from Date Applied; delete any conditional-format "
              f"rule on 'Follow-Up Due' (col {col_to_letter(fdue_idx)}); delete that column. "
              f"Re-run with --yes to apply.")
        return

    # ── 1. snapshot ──────────────────────────────────────────────────────
    before = values.get(spreadsheetId=sid, range=f"'{tab}'!A1:AZ").execute().get("values", [])
    snap = {"taken": datetime.now().isoformat(timespec="seconds"), "spreadsheet_id": sid,
            "values": before,
            "row2_formulas": values.get(spreadsheetId=sid, range=f"'{tab}'!2:2",
                                        valueRenderOption="FORMULA").execute().get("values", [])}
    snap_path = Path(".tmp") / f"tracker_snapshot_{datetime.now():%Y%m%d_%H%M%S}.json"
    snap_path.parent.mkdir(exist_ok=True)
    snap_path.write_text(json.dumps(snap, indent=2))
    print(f"Snapshot saved: {snap_path} ({len(before)} rows)")

    # ── 2. rewrite Action Req. (must happen before the column disappears) ──
    ar_col = tr.col_letter("Action Req.")
    values.update(spreadsheetId=sid, range=f"'{tab}'!{ar_col}2",
                  valueInputOption="USER_ENTERED",
                  body={"values": [[action_req_formula(tr)]]}).execute()
    print("Rewrote 'Action Req.' — 'Follow up due' now computed inline from Date Applied")

    # ── 3 & 4. delete the orphaned conditional-format rule, then the column ──
    tab_id = next(s["properties"]["sheetId"]
                  for s in service.spreadsheets().get(spreadsheetId=sid).execute()["sheets"]
                  if s["properties"]["title"] == tab)
    sheet_meta = service.spreadsheets().get(
        spreadsheetId=sid, ranges=[f"'{tab}'"],
        fields="sheets.conditionalFormats").execute()
    formats = sheet_meta["sheets"][0].get("conditionalFormats", [])
    rule_indices = [i for i, f in enumerate(formats)
                    for r in f.get("ranges", [])
                    if r.get("startColumnIndex") == fdue_idx and r.get("endColumnIndex") == fdue_idx + 1]

    requests = [{"deleteConditionalFormatRule": {"sheetId": tab_id, "index": i}}
                for i in sorted(rule_indices, reverse=True)]
    requests.append({"deleteDimension": {"range": {
        "sheetId": tab_id, "dimension": "COLUMNS",
        "startIndex": fdue_idx, "endIndex": fdue_idx + 1}}})
    service.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": requests}).execute()
    print(f"Deleted {len(rule_indices)} conditional-format rule(s) on 'Follow-Up Due' and the column itself")

    # ── 5. verify ────────────────────────────────────────────────────────
    after_headers = values.get(spreadsheetId=sid, range=f"'{tab}'!1:1").execute().get("values", [[]])[0]
    if "Follow-Up Due" in after_headers:
        print(f"WARNING: 'Follow-Up Due' still present after deletion — check the sheet "
              f"manually (snapshot {snap_path} is the rollback point)", file=sys.stderr)
    else:
        print("Verified: 'Follow-Up Due' is gone.")

    print("\nDone. Next: update schema/sheets.yaml (drop 'Follow-Up Due', bump schema_version), "
          "then python3 tools/check_schema.py (expect OK).")


if __name__ == "__main__":
    main()
