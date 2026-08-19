#!/usr/bin/env python3
"""ONE-TIME migration: redesign the Tracker 'Action Req.' control panel (schema v10 → v11).

Changes applied to the live Tracker tab:

  1. App-status lifecycle finalised: 'Responded' retired, 'Completed' made
     official (To Apply → Applied → Completed). 'Completed' was already in live
     use before this tool; any stray 'Responded' cells are remapped → 'Completed'.
  2. New manual 'Follow-up Date' column (appended). Records when a follow-up was
     actually sent — resets the 'Awaiting response' staleness clock (counted from
     the later of Date Applied / Follow-up Date; stale ≥21 days) and, blank on an
     'Applied' row past 3 days, drives the 'Follow-up due' nudge.
  3. Follow-Up column gains a 'No Contact' sentinel (schema vocab
     'follow_up_trigger' = doc_trigger + No Contact) → Action Req.
     'No contact — revisit'.
  4. 'Action Req.' rewritten as a phase-gated ladder (first match wins):
        URL blank                 → ""
        Outcome set               → "✓ " & Outcome
        App Status = Applied      → Generate/Send cover letter → No contact —
                                    revisit / Generate follow-up / Send follow-up
                                    / Follow-up due (≥3d) / Awaiting response
        App Status = Completed     → Awaiting response (+ " (Nd)" once ≥21d stale)
        App Status = To Apply      → Generate docs / Submit docs / Ready — mark
                                    applied   (gated on Resume + App Qns only;
                                    Cover Letter never gates applying)
  5. 'Posted' / 'Closing' display formulas gain Option-A assumed dates: a missing
     Date Posted/Closing is inferred as EDATE(other, ∓1 month) for display, and
     italicised via conditional format so inferred dates are visible as such.
  6. All Tracker conditional formatting rebuilt into ONE harmonised palette shared
     by the Action Req. cell and every status / trigger dropdown:
        amber  = to-do (generate / submit / send / To Apply / Required / Revise)
        blue   = in-progress (Applied / Generated)
        green  = done or ready (Completed / Submitted / Ready / Interview / Offer)
        grey   = passive / neutral (Awaiting response / Not Required / Closed)
        red    = urgent (Follow-up due / stale awaiting / past-due closing)
        purple = networking (No Contact / No contact — revisit)

What it does (idempotent — refuses to re-run once migrated):
  1. Snapshots the whole Tracker tab (values + row-2 formulas + conditional-format
     rules) to .tmp/tracker_snapshot_<ts>.json  ← the rollback point
  2. Appends the 'Follow-up Date' header if absent
  3. Remaps any 'Responded' App Status cells → 'Completed'
  4. Writes the new 'Action Req.' / 'Posted' / 'Closing' ARRAYFORMULAs
  5. Deletes every existing Tracker conditional-format rule and adds the new set
  6. Resets dropdowns (App Status, Outcome, Resume/Cover Letter/App Qns, Follow-Up)
     and the Follow-up Date number format
  7. Re-reads and verifies

Dry-run by default; pass --yes to apply. --skip-formatting does structure +
formulas only. Run schema/sheets.yaml's v11 update + tools/check_schema.py
afterwards (expect OK — 'Follow-up Date' now in both), then tools/sync_tracker.py
(expect a no-op).
"""
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from sheets_common import (get_sheets_service, sheet_id, load_schema, Tab,
                           col_to_letter, norm_header)

FOLLOW_UP_DATE = "Follow-up Date"
NEW_SIGNATURE = "Ready — mark applied"   # appears only in the v11 Action Req. formula

# ── harmonised palette (light backgrounds) ───────────────────────────────────
AMBER = {"red": 1.0, "green": 0.90, "blue": 0.60}
BLUE = {"red": 0.80, "green": 0.90, "blue": 1.0}
GREEN = {"red": 0.80, "green": 0.94, "blue": 0.80}
GREY = {"red": 0.90, "green": 0.90, "blue": 0.90}
RED = {"red": 0.96, "green": 0.80, "blue": 0.80}
PURPLE = {"red": 0.90, "green": 0.82, "blue": 0.98}
GREY_TEXT = {"red": 0.5, "green": 0.5, "blue": 0.5}

AMBER_ACTIONS = ["Generate docs", "Submit docs", "Generate cover letter",
                 "Send cover letter", "Generate follow-up", "Send follow-up"]


def live_index(headers, name):
    target = norm_header(name)
    for i, h in enumerate(headers):
        if norm_header(h) == target:
            return i
    return None


def IFf(cond, a, b):
    """Balanced IF(...) builder — avoids hand-counting nested parentheses."""
    return f"IF({cond},{a},{b})"


def action_req_formula(tr: Tab) -> str:
    L = tr.col_letter
    R = lambda c: f"{c}2:{c}"
    U, OC = R(L("URL")), R(L("Outcome"))
    DA, FDT = R(L("Date Applied")), R(L(FOLLOW_UP_DATE))
    RES, CL = R(L("Resume")), R(L("Cover Letter"))
    FU, AQ = R(L("Follow-Up")), R(L("App Qns"))
    APP = R(L("App Status"))

    # waiting days = TODAY() − later of (Follow-up Date, Date Applied)
    wait = f'(TODAY()-IF({FDT}="",{DA},{FDT}))'
    # "Awaiting response", stale suffix " (Nd)" once wait ≥ 21 days (only if Date Applied set)
    aw = f'("Awaiting response"&IF(({DA}<>"")*({wait}>=21)," ("&{wait}&"d)",""))'

    applied = IFf(
        f'({CL}="Required")+({CL}="Revise")>0', '"Generate cover letter"',
        IFf(f'{CL}="Generated"', '"Send cover letter"',
            IFf(f'{FU}="No Contact"', '"No contact — revisit"',
                IFf(f'({FU}="Required")+({FU}="Revise")>0', '"Generate follow-up"',
                    IFf(f'{FU}="Generated"', '"Send follow-up"',
                        IFf(f'({FU}="Submitted")+({FDT}<>"")+({FU}="Not Required")>0', aw,
                            IFf(f'({DA}<>"")*(TODAY()-{DA}>=3)>0', '"Follow-up due"', aw)))))))

    to_apply = IFf(
        f'({RES}="Required")+({RES}="Revise")+({AQ}="Required")+({AQ}="Revise")>0',
        '"Generate docs"',
        IFf(f'({RES}="Generated")+({AQ}="Generated")>0', '"Submit docs"',
            f'"{NEW_SIGNATURE}"'))

    body = IFf(
        f'{U}=""', '""',
        IFf(f'{OC}<>""', f'"✓ "&{OC}',
            IFf(f'{APP}="Applied"', applied,
                IFf(f'{APP}="Completed"', aw,
                    IFf(f'{APP}="To Apply"', to_apply, '""')))))
    return f"=ARRAYFORMULA({body})"


def posted_formula(tr: Tab) -> str:
    """Posted display; missing Date Posted inferred as EDATE(Date Closing, -1)."""
    L = tr.col_letter
    DP, DC = f"{L('Date Posted')}2:{L('Date Posted')}", f"{L('Date Closing')}2:{L('Date Closing')}"
    effp = f'IF({DP}<>"",{DP},EDATE({DC},-1))'
    return (f'=ARRAYFORMULA(IF(({DP}="")*({DC}=""),"",'
            f'RIGHT("  "&DAYS(TODAY(),{effp}),2)&" days ago"))')


def closing_formula(tr: Tab) -> str:
    """Closing countdown; missing Date Closing inferred as EDATE(Date Posted, +1)."""
    L = tr.col_letter
    DP, DC = f"{L('Date Posted')}2:{L('Date Posted')}", f"{L('Date Closing')}2:{L('Date Closing')}"
    effc = f'IF({DC}<>"",{DC},EDATE({DP},1))'
    return (f'=ARRAYFORMULA(IF(({DC}="")*({DP}=""),"",'
            f'IF({effc}>TODAY(),"in "&({effc}-TODAY())&" days",'
            f'IF({effc}=TODAY(),"today",(TODAY()-{effc})&" days ago"))))')


def col_range(tr: Tab, tab_id: int, header: str) -> dict:
    c = tr.col_index(header)
    return {"sheetId": tab_id, "startRowIndex": 1, "startColumnIndex": c, "endColumnIndex": c + 1}


def _bg_eq(rng, text, color):
    return {"ranges": [rng], "booleanRule": {
        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": text}]},
        "format": {"backgroundColor": color}}}


def _bg_starts(rng, text, color):
    return {"ranges": [rng], "booleanRule": {
        "condition": {"type": "TEXT_STARTS_WITH", "values": [{"userEnteredValue": text}]},
        "format": {"backgroundColor": color}}}


def _bg_custom(rng, formula, color):
    return {"ranges": [rng], "booleanRule": {
        "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]},
        "format": {"backgroundColor": color}}}


def conditional_format_rules(tr: Tab, tab_id: int) -> list[dict]:
    """Ordered list of rule bodies (priority order = evaluation order)."""
    L = tr.col_letter
    OCL, DPL, DCL = L("Outcome"), L("Date Posted"), L("Date Closing")
    rules = []

    # ── Action Req. cell background (harmonised) ──────────────────────────────
    ar = col_range(tr, tab_id, "Action Req.")
    rules.append(_bg_custom(ar, f'=OR(${OCL}2="Interview",${OCL}2="Offer")', GREEN))
    rules.append(_bg_custom(ar, f'=OR(${OCL}2="Rejected",${OCL}2="Closed")', GREY))
    rules.append(_bg_eq(ar, "Follow-up due", RED))
    rules.append(_bg_starts(ar, "Awaiting response (", RED))       # stale variant
    rules.append(_bg_eq(ar, "Awaiting response", GREY))
    for a in AMBER_ACTIONS:
        rules.append(_bg_eq(ar, a, AMBER))
    rules.append(_bg_eq(ar, "No contact — revisit", PURPLE))
    rules.append(_bg_eq(ar, NEW_SIGNATURE, GREEN))

    # ── status / trigger dropdown backgrounds (same palette) ──────────────────
    for val, color in (("To Apply", AMBER), ("Applied", BLUE), ("Completed", GREEN)):
        rules.append(_bg_eq(col_range(tr, tab_id, "App Status"), val, color))
    for val, color in (("Interview", GREEN), ("Offer", GREEN),
                       ("Rejected", RED), ("Closed", GREY)):
        rules.append(_bg_eq(col_range(tr, tab_id, "Outcome"), val, color))
    doc_palette = (("Required", AMBER), ("Revise", AMBER), ("Generated", BLUE),
                   ("Submitted", GREEN), ("Not Required", GREY))
    for header in ("Resume", "Cover Letter", "App Qns"):
        for val, color in doc_palette:
            rules.append(_bg_eq(col_range(tr, tab_id, header), val, color))
    for val, color in doc_palette + (("No Contact", PURPLE),):
        rules.append(_bg_eq(col_range(tr, tab_id, "Follow-Up"), val, color))

    # ── Posted / Closing assumed-date italics ─────────────────────────────────
    posted_rng, closing_rng = col_range(tr, tab_id, "Posted"), col_range(tr, tab_id, "Closing")
    rules.append({"ranges": [posted_rng], "booleanRule": {
        "condition": {"type": "CUSTOM_FORMULA",
                      "values": [{"userEnteredValue": f'=AND(${DPL}2="",${DCL}2<>"")'}]},
        "format": {"textFormat": {"italic": True}}}})
    rules.append({"ranges": [closing_rng], "booleanRule": {
        "condition": {"type": "CUSTOM_FORMULA",
                      "values": [{"userEnteredValue": f'=AND(${DCL}2="",${DPL}2<>"")'}]},
        "format": {"textFormat": {"italic": True}}}})

    # ── Closing countdown red (past) / amber (≤3d), assumed-date aware ─────────
    effc = f'IF(${DCL}2<>"",${DCL}2,IF(${DPL}2<>"",EDATE(${DPL}2,1),""))'
    rules.append(_bg_custom(closing_rng, f'=AND({effc}<>"",{effc}<TODAY())', RED))
    rules.append(_bg_custom(closing_rng,
                            f'=AND({effc}<>"",{effc}>=TODAY(),{effc}-TODAY()<=3)', AMBER))

    # ── terminal rows (Outcome Rejected/Closed): dim + strikethrough whole row ─
    last_col = len(tr.live_headers)
    rules.append({"ranges": [{"sheetId": tab_id, "startRowIndex": 1,
                              "startColumnIndex": 0, "endColumnIndex": last_col}],
                  "booleanRule": {
                      "condition": {"type": "CUSTOM_FORMULA",
                                    "values": [{"userEnteredValue":
                                                f'=OR(${OCL}2="Rejected",${OCL}2="Closed")'}]},
                      "format": {"textFormat": {"foregroundColor": GREY_TEXT,
                                                "strikethrough": True}}}})
    return rules


def validation_requests(tr: Tab, tab_id: int) -> list[dict]:
    vocab = load_schema()["vocabularies"]
    reqs = []
    dropdowns = (("App Status", vocab["app_status"]), ("Outcome", vocab["outcome"]),
                 ("Resume", vocab["doc_trigger"]), ("Cover Letter", vocab["doc_trigger"]),
                 ("App Qns", vocab["doc_trigger"]), ("Follow-Up", vocab["follow_up_trigger"]))
    for header, values in dropdowns:
        reqs.append({"setDataValidation": {
            "range": col_range(tr, tab_id, header),
            "rule": {"condition": {"type": "ONE_OF_LIST",
                                   "values": [{"userEnteredValue": v} for v in values]},
                     "strict": False, "showCustomUi": True}}})
    # Follow-up Date number format (match Outcome Date's dd-mmm-yy)
    reqs.append({"repeatCell": {
        "range": col_range(tr, tab_id, FOLLOW_UP_DATE),
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "dd-mmm-yy"}}},
        "fields": "userEnteredFormat.numberFormat"}})
    return reqs


def sheet_props(service, sid, tab):
    for s in service.spreadsheets().get(spreadsheetId=sid).execute()["sheets"]:
        if s["properties"]["title"] == tab:
            return s["properties"]["sheetId"], len(s.get("conditionalFormats", []))
    sys.exit(f"Tab '{tab}' not found.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="Apply (default: dry-run report)")
    parser.add_argument("--skip-formatting", action="store_true",
                        help="Structure + formulas only (no dropdowns/format/conditional rules)")
    args = parser.parse_args()

    service = get_sheets_service()
    sid = sheet_id()
    tab = "Tracker"
    values = service.spreadsheets().values()

    tr = Tab(service, tab)
    live = list(tr.live_headers)
    for h in ("URL", "Outcome", "Date Applied", "App Status", "Resume",
              "Cover Letter", "Follow-Up", "App Qns", "Action Req.", "Posted", "Closing"):
        if live_index(live, h) is None:
            sys.exit(f"Tracker has no '{h}' column — not the state this tool expects. Aborting.")

    # ── current state ────────────────────────────────────────────────────────
    grid = values.get(spreadsheetId=sid, range=f"'{tab}'").execute().get("values", [])
    hdr = grid[0] if grid else []
    ar_idx = live_index(hdr, "Action Req.")
    row2 = values.get(spreadsheetId=sid, range=f"'{tab}'!2:2",
                      valueRenderOption="FORMULA").execute().get("values", [[]])
    row2 = row2[0] if row2 else []
    cur_ar = row2[ar_idx] if ar_idx is not None and ar_idx < len(row2) else ""

    has_fudate = live_index(hdr, FOLLOW_UP_DATE) is not None
    already = has_fudate and (NEW_SIGNATURE in cur_ar)
    if already:
        print("Tracker already has the 'Follow-up Date' column and the v11 Action Req. "
              "ladder — already migrated. Nothing to do.")
        return

    app_idx = live_index(hdr, "App Status")
    responded_rows = [i + 2 for i, r in enumerate(grid[1:])
                      if (r[app_idx] if app_idx < len(r) else "").strip() == "Responded"]
    tab_id, n_cf = sheet_props(service, sid, tab)

    # ── dry-run report ───────────────────────────────────────────────────────
    if not args.yes:
        print("[dry-run] Would migrate the Tracker to schema v11:")
        print(f"  - Append '{FOLLOW_UP_DATE}' column: {'no (already present)' if has_fudate else 'yes'}")
        print(f"  - Remap 'Responded' → 'Completed': {len(responded_rows)} row(s) "
              f"{responded_rows or ''}")
        print("  - Rewrite Action Req. (phase-gated ladder), Posted/Closing (assumed dates)")
        if args.skip_formatting:
            print("  - Skip dropdowns / number format / conditional formatting (--skip-formatting)")
        else:
            print(f"  - Replace all {n_cf} existing conditional-format rule(s) with the "
                  f"harmonised set")
            print("  - Reset dropdowns (App Status, Outcome, Resume, Cover Letter, App Qns, "
                  "Follow-Up) + Follow-up Date date format")
        print("Re-run with --yes to apply.")
        return

    # ── 1. snapshot (values + row-2 formulas + conditional formats) ──────────
    cf_snapshot = next((s.get("conditionalFormats", [])
                        for s in service.spreadsheets().get(spreadsheetId=sid).execute()["sheets"]
                        if s["properties"]["title"] == tab), [])
    snap = {"taken": datetime.now().isoformat(timespec="seconds"), "spreadsheet_id": sid,
            "values": grid, "row2_formulas": [row2], "conditional_formats": cf_snapshot}
    snap_path = Path(".tmp") / f"tracker_snapshot_{datetime.now():%Y%m%d_%H%M%S}.json"
    snap_path.parent.mkdir(exist_ok=True)
    snap_path.write_text(json.dumps(snap, indent=2))
    print(f"Snapshot saved: {snap_path} ({len(grid)} rows, {len(cf_snapshot)} CF rule(s))")

    # ── 2. append 'Follow-up Date' header if missing ─────────────────────────
    if not has_fudate:
        start = len(live)
        values.update(spreadsheetId=sid, range=f"'{tab}'!{col_to_letter(start)}1",
                      valueInputOption="RAW", body={"values": [[FOLLOW_UP_DATE]]}).execute()
        print(f"Appended '{FOLLOW_UP_DATE}' at column {col_to_letter(start)}.")
    tr = Tab(service, tab)   # refresh header map now that structure is final

    # ── 3. remap any 'Responded' → 'Completed' ───────────────────────────────
    if responded_rows:
        app_col = tr.col_letter("App Status")
        values.batchUpdate(spreadsheetId=sid, body={"valueInputOption": "RAW", "data": [
            {"range": f"'{tab}'!{app_col}{n}", "values": [["Completed"]]} for n in responded_rows
        ]}).execute()
        print(f"Remapped {len(responded_rows)} 'Responded' → 'Completed'.")
    else:
        print("No 'Responded' cells to remap.")

    # ── 4. write the three ARRAYFORMULAs (row 2) ─────────────────────────────
    fdata = [
        {"range": f"'{tab}'!{tr.col_letter('Action Req.')}2", "values": [[action_req_formula(tr)]]},
        {"range": f"'{tab}'!{tr.col_letter('Posted')}2", "values": [[posted_formula(tr)]]},
        {"range": f"'{tab}'!{tr.col_letter('Closing')}2", "values": [[closing_formula(tr)]]},
    ]
    values.batchUpdate(spreadsheetId=sid,
                       body={"valueInputOption": "USER_ENTERED", "data": fdata}).execute()
    print("Wrote ARRAYFORMULAs: Action Req. (v11 ladder), Posted / Closing (assumed dates).")

    # ── 5. formatting: delete every existing CF rule, add the harmonised set ──
    if not args.skip_formatting:
        _, n_now = sheet_props(service, sid, tab)
        reqs = [{"deleteConditionalFormatRule": {"sheetId": tab_id, "index": i}}
                for i in range(n_now - 1, -1, -1)]
        for i, rule in enumerate(conditional_format_rules(tr, tab_id)):
            reqs.append({"addConditionalFormatRule": {"index": i, "rule": rule}})
        reqs += validation_requests(tr, tab_id)
        service.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": reqs}).execute()
        print(f"Replaced {n_now} CF rule(s) with the harmonised set; reset dropdowns + "
              f"Follow-up Date format.")
    else:
        print("Skipped dropdowns / number format / conditional formatting (--skip-formatting).")

    # ── 6. verify ─────────────────────────────────────────────────────────────
    after = values.get(spreadsheetId=sid, range=f"'{tab}'").execute().get("values", [])
    ahdr = after[0] if after else []
    a_app = live_index(ahdr, "App Status")
    app_vocab = set(load_schema()["vocabularies"]["app_status"])
    bad = []
    if live_index(ahdr, FOLLOW_UP_DATE) is None:
        bad.append("  'Follow-up Date' column missing after migration")
    for i, r in enumerate(after[1:], start=2):
        v = (r[a_app] if a_app is not None and a_app < len(r) else "").strip()
        if v and v not in app_vocab:
            bad.append(f"  row {i}: App Status '{v}' not in {sorted(app_vocab)}")
    after_row2 = values.get(spreadsheetId=sid, range=f"'{tab}'!2:2",
                            valueRenderOption="FORMULA").execute().get("values", [[]])
    after_row2 = after_row2[0] if after_row2 else []
    new_ar = after_row2[live_index(ahdr, "Action Req.")] if ahdr else ""
    if NEW_SIGNATURE not in new_ar:
        bad.append("  Action Req. formula does not contain the v11 signature")

    if bad:
        print(f"WARNING: {len(bad)} issue(s) remain (snapshot {snap_path} is the rollback point):",
              file=sys.stderr)
        print("\n".join(bad), file=sys.stderr)
        sys.exit(1)
    print("Verified: Follow-up Date present, App Status vocab clean, Action Req. on the v11 ladder.")

    print("\nDone. Next: python3 tools/check_schema.py  (expect OK), then "
          "python3 tools/sync_tracker.py  (expect a no-op).")


if __name__ == "__main__":
    main()
