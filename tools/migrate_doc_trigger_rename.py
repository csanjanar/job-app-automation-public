#!/usr/bin/env python3
"""ONE-TIME migration: relabel the Tracker doc-trigger vocabulary (schema v9 → v10).

The doc_trigger vocabulary used by the Resume / Cover Letter / Follow-Up / App
Qns columns is relabelled for clarity:

    'Generate'          → 'Required'
    'Change > Generate' → 'Revise'
    (Generated / Submitted / Not Required unchanged)

Only the trigger *inputs* change. No executable tool logic depends on the old
strings: run_doc_batch.py always writes 'Generated' and derives fresh/revise
from the agent-built manifest, and sync_tracker.py reads seed_default straight
from schema/sheets.yaml. The two live artefacts that DID hardcode the old
strings are handled here:

  1. Existing cell values in the four trigger columns  ('Generate'→'Required',
     'Change > Generate'→'Revise').
  2. The 'Action Req.' ARRAYFORMULA (row 2) — its trigger *comparisons* are
     rewritten. Its *output* labels ("Generate docs", "Generate follow-up",
     "Submit resume", …) are action instructions, not vocabulary, and are left
     unchanged.
  3. The data-validation dropdowns on the four trigger columns are reset to the
     new vocabulary so the picker offers the new labels.

What it does (idempotent — reports "nothing to do" if already on the new vocab):
  1. Snapshots the whole Tracker tab to .tmp/tracker_snapshot_<ts>.json
  2. Renames existing trigger cell values (RAW, exact trimmed match)
  3. Rewrites the 'Action Req.' ARRAYFORMULA's trigger comparisons
  4. Resets the four trigger columns' dropdowns to the new vocab
  5. Re-reads and verifies no old value / comparison remains

Dry-run by default; pass --yes to apply. The Action Req. formula reproduced
here is the v9 inline-Follow-Up-Due version (WORKDAY computed inline from Date
Applied) last written by tools/remove_follow_up_due.py — kept byte-identical
except for the two renamed comparison operands.

Run schema/sheets.yaml's v10 update + tools/check_schema.py afterwards
(expect OK — no headers change), then tools/sync_tracker.py (seeds 'Required'
into any blank Resume cells going forward).
"""
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from sheets_common import get_sheets_service, sheet_id, Tab, norm_header

TRIGGER_HEADERS = ["Resume", "Cover Letter", "Follow-Up", "App Qns"]
VALUE_RENAMES = {"generate": "Required", "change > generate": "Revise"}  # matched case-insensitively
NEW_VOCAB = ["Required", "Revise", "Generated", "Submitted", "Not Required"]
OLD_COMPARISONS = ('="Generate"', '="Change > Generate"')


def live_index(headers, name):
    target = norm_header(name)
    for i, h in enumerate(headers):
        if norm_header(h) == target:
            return i
    return None


def action_req_formula(tr: Tab) -> str:
    """v9 inline-Follow-Up-Due 'Action Req.' formula (see remove_follow_up_due.py),
    with the trigger comparisons renamed:
      "Generate"→"Required", "Change > Generate"→"Revise".
    Output action labels ("Generate docs" / "Generate follow-up" / …) unchanged."""
    L = tr.col_letter
    da = L("Date Applied")
    url, oc = L("URL"), L("Outcome")
    res, cl, fu = L("Resume"), L("Cover Letter"), L("Follow-Up")
    app = L("App Status")

    fdue = f'IF({da}2:{da}="","",WORKDAY({da}2:{da}+4,1))'

    return (
        f'=ARRAYFORMULA(IF({url}2:{url}="","",'
        f'IF({oc}2:{oc}<>"","✓ "&{oc}2:{oc},'
        f'IF(({res}2:{res}="Required")+({res}2:{res}="Revise")'
        f'+({cl}2:{cl}="Required")+({cl}2:{cl}="Revise")>0,"Generate docs",'
        f'IF({res}2:{res}="Generated","Submit resume",'
        f'IF({cl}2:{cl}="Generated","Send cover letter",'
        f'IF({app}2:{app}="To Apply","Apply",'
        f'IF(({fu}2:{fu}<>"Not Required")*({fu}2:{fu}<>"Submitted")'
        f'*({fdue}<>"")*(N({fdue})<=TODAY())>0,"Follow up due",'
        f'IF({fu}2:{fu}="Generated","Send follow-up",'
        f'IF({fu}2:{fu}="Required","Generate follow-up",'
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

    for h in TRIGGER_HEADERS + ["Action Req."]:
        if live_index(live, h) is None:
            sys.exit(f"Tracker has no '{h}' column — not the state this tool expects. Aborting.")

    # ── read current state ────────────────────────────────────────────────
    grid = values.get(spreadsheetId=sid, range=f"'{tab}'").execute().get("values", [])
    hdr = grid[0] if grid else []
    trig_idx = {h: live_index(hdr, h) for h in TRIGGER_HEADERS}

    # cell value renames needed (per header → list of (row_num, old, new))
    cell_changes = {h: [] for h in TRIGGER_HEADERS}
    for r_off, row in enumerate(grid[1:]):
        row_num = r_off + 2
        for h in TRIGGER_HEADERS:
            c = trig_idx[h]
            val = (row[c] if c is not None and c < len(row) else "").strip()
            new = VALUE_RENAMES.get(val.lower())
            if new and new != val:
                cell_changes[h].append((row_num, val, new))
    total_cell_changes = sum(len(v) for v in cell_changes.values())

    # Action Req. formula rewrite needed?
    ar_idx = live_index(hdr, "Action Req.")
    row2 = values.get(spreadsheetId=sid, range=f"'{tab}'!2:2",
                      valueRenderOption="FORMULA").execute().get("values", [[]])
    row2 = row2[0] if row2 else []
    cur_ar = row2[ar_idx] if ar_idx < len(row2) else ""
    formula_needs_rewrite = any(old in cur_ar for old in OLD_COMPARISONS)

    if total_cell_changes == 0 and not formula_needs_rewrite:
        print("Tracker doc-trigger vocab is already on v10 (no 'Generate'/'Change > Generate' "
              "cell values and Action Req. uses the new comparisons) — nothing to do.")
        return

    # ── dry-run report ────────────────────────────────────────────────────
    if not args.yes:
        print("[dry-run] Would migrate the Tracker doc-trigger vocabulary "
              "(Generate→Required, Change > Generate→Revise):")
        for h in TRIGGER_HEADERS:
            if cell_changes[h]:
                summary = ", ".join(f"row {n} {old!r}→{new!r}" for n, old, new in cell_changes[h])
                print(f"  {h}: {len(cell_changes[h])} cell(s) — {summary}")
        print(f"  Cell values to rename: {total_cell_changes}")
        print(f"  Action Req. formula rewrite: {'yes' if formula_needs_rewrite else 'no (already new)'}")
        print(f"  Reset dropdowns on: {', '.join(TRIGGER_HEADERS)} → {NEW_VOCAB}")
        print("Re-run with --yes to apply.")
        return

    # ── 1. snapshot ───────────────────────────────────────────────────────
    snap = {"taken": datetime.now().isoformat(timespec="seconds"), "spreadsheet_id": sid,
            "values": grid, "row2_formulas": [row2]}
    snap_path = Path(".tmp") / f"tracker_snapshot_{datetime.now():%Y%m%d_%H%M%S}.json"
    snap_path.parent.mkdir(exist_ok=True)
    snap_path.write_text(json.dumps(snap, indent=2))
    print(f"Snapshot saved: {snap_path} ({len(grid)} rows)")

    # ── 2. rename existing cell values (RAW, per-cell so blanks untouched) ─
    data = []
    for h in TRIGGER_HEADERS:
        col = tr.col_letter(h)
        for row_num, _old, new in cell_changes[h]:
            data.append({"range": f"'{tab}'!{col}{row_num}", "values": [[new]]})
    if data:
        values.batchUpdate(spreadsheetId=sid,
                           body={"valueInputOption": "RAW", "data": data}).execute()
    print(f"Renamed {total_cell_changes} trigger cell value(s).")

    # ── 3. rewrite Action Req. formula ────────────────────────────────────
    if formula_needs_rewrite:
        ar_col = tr.col_letter("Action Req.")
        values.update(spreadsheetId=sid, range=f"'{tab}'!{ar_col}2",
                      valueInputOption="USER_ENTERED",
                      body={"values": [[action_req_formula(tr)]]}).execute()
        print("Rewrote 'Action Req.' — trigger comparisons now match Required/Revise.")
    else:
        print("Action Req. already on the new comparisons — left as-is.")

    # ── 4. reset dropdowns on the four trigger columns ────────────────────
    tab_id = next(s["properties"]["sheetId"]
                  for s in service.spreadsheets().get(spreadsheetId=sid).execute()["sheets"]
                  if s["properties"]["title"] == tab)
    reqs = []
    for h in TRIGGER_HEADERS:
        c = tr.col_index(h)
        reqs.append({"setDataValidation": {
            "range": {"sheetId": tab_id, "startRowIndex": 1,
                      "startColumnIndex": c, "endColumnIndex": c + 1},
            "rule": {"condition": {"type": "ONE_OF_LIST",
                                   "values": [{"userEnteredValue": v} for v in NEW_VOCAB]},
                     "strict": False, "showCustomUi": True}}})
    service.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": reqs}).execute()
    print(f"Reset dropdowns on {', '.join(TRIGGER_HEADERS)} → {NEW_VOCAB}")

    # ── 5. verify ─────────────────────────────────────────────────────────
    after = values.get(spreadsheetId=sid, range=f"'{tab}'").execute().get("values", [])
    ahdr = after[0] if after else []
    aidx = {h: live_index(ahdr, h) for h in TRIGGER_HEADERS}
    bad = []
    for r_off, row in enumerate(after[1:]):
        for h in TRIGGER_HEADERS:
            c = aidx[h]
            v = (row[c] if c is not None and c < len(row) else "").strip()
            if v and v.lower() in VALUE_RENAMES:
                bad.append(f"  row {r_off + 2} {h}: still '{v}'")
    after_row2 = values.get(spreadsheetId=sid, range=f"'{tab}'!2:2",
                            valueRenderOption="FORMULA").execute().get("values", [[]])
    after_row2 = after_row2[0] if after_row2 else []
    new_ar = after_row2[live_index(ahdr, "Action Req.")] if ahdr else ""
    if any(old in new_ar for old in OLD_COMPARISONS):
        bad.append("  Action Req. formula still contains an old comparison")

    if bad:
        print(f"WARNING: {len(bad)} issue(s) remain (snapshot {snap_path} is the rollback point):",
              file=sys.stderr)
        print("\n".join(bad), file=sys.stderr)
        sys.exit(1)
    print("Verified: no old trigger values remain and Action Req. uses the new comparisons.")

    print("\nDone. Next: python3 tools/check_schema.py  (expect OK), then "
          "python3 tools/sync_tracker.py  (seeds 'Required' into blank Resume cells).")


if __name__ == "__main__":
    main()
