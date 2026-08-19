#!/usr/bin/env python3
"""Iterative Action Req. tweak: add a 'Find Contact' nudge + make Follow-Up
'Not Required' fall through to the follow-up nudge (post-v11, no schema change).

Two changes to the live Tracker 'Action Req.' ARRAYFORMULA, both inside the
App Status = Applied branch (cover-letter steps first, then follow-up steps):

  1. NEW rung after the 'No Contact' check:
        Follow-up Contact (col U) empty  →  "Find Contact"
     Shows immediately so a contactless applied row prompts you to go find one
     to reach out to later. If you genuinely can't, set Follow-Up = 'No Contact'
     (the rung above it) → "No contact — revisit" (parked, silent).

  2. 'Not Required' no longer short-circuits to "Awaiting response". The stale
     clause becomes  (Follow-Up = Submitted) OR (Follow-up Date set)  only, so a
     row whose Follow-Up is still the seeded default 'Not Required' (contact
     present, nothing generated/sent) falls through to the ≥3-day rung and shows
     "Follow-up due". To intentionally stop chasing a role, set App Status =
     Completed (not Follow-Up = Not Required).

Everything else is unchanged: 'No Contact' stays in the follow_up_trigger vocab
and its dropdown; the staleness clock still counts from the later of Date
Applied / Follow-up Date and resets once a follow-up lands; To Apply / Completed
branches untouched.

Formatting: adds one conditional-format rule painting the Action Req. cell amber
when it equals "Find Contact" (same amber as the other to-do actions). Idempotent
— skips the rule if it already exists.

Dry-run by default; pass --yes to apply. Safe to re-run.
"""
import sys
import argparse

from sheets_common import get_sheets_service, sheet_id, Tab

AMBER = {"red": 1.0, "green": 0.90, "blue": 0.60}
FIND_CONTACT = "Find Contact"


def IFf(cond, a, b):
    """Balanced IF(...) builder — avoids hand-counting nested parentheses."""
    return f"IF({cond},{a},{b})"


def action_req_formula(tr: Tab) -> str:
    L = tr.col_letter
    R = lambda c: f"{c}2:{c}"
    U, OC = R(L("URL")), R(L("Outcome"))
    DA, FDT = R(L("Date Applied")), R(L("Follow-up Date"))
    RES, CL = R(L("Resume")), R(L("Cover Letter"))
    FUC = R(L("Follow-up Contact"))
    FU, AQ = R(L("Follow-Up")), R(L("App Qns"))
    APP = R(L("App Status"))

    wait = f'(TODAY()-IF({FDT}="",{DA},{FDT}))'
    aw = f'("Awaiting response"&IF(({DA}<>"")*({wait}>=21)," ("&{wait}&"d)",""))'

    applied = IFf(
        f'({CL}="Required")+({CL}="Revise")>0', '"Generate cover letter"',
        IFf(f'{CL}="Generated"', '"Send cover letter"',
            IFf(f'{FU}="No Contact"', '"No contact — revisit"',
                IFf(f'{FUC}=""', f'"{FIND_CONTACT}"',
                    IFf(f'({FU}="Required")+({FU}="Revise")>0', '"Generate follow-up"',
                        IFf(f'{FU}="Generated"', '"Send follow-up"',
                            IFf(f'({FU}="Submitted")+({FDT}<>"")>0', aw,
                                IFf(f'({DA}<>"")*(TODAY()-{DA}>=3)>0', '"Follow-up due"', aw))))))))

    to_apply = IFf(
        f'({RES}="Required")+({RES}="Revise")+({AQ}="Required")+({AQ}="Revise")>0',
        '"Generate docs"',
        IFf(f'({RES}="Generated")+({AQ}="Generated")>0', '"Submit docs"',
            '"Ready — mark applied"'))

    body = IFf(
        f'{U}=""', '""',
        IFf(f'{OC}<>""', f'"✓ "&{OC}',
            IFf(f'{APP}="Applied"', applied,
                IFf(f'{APP}="Completed"', aw,
                    IFf(f'{APP}="To Apply"', to_apply, '""')))))
    return f"=ARRAYFORMULA({body})"


def find_contact_rule(tab_id: int, col_index: int) -> dict:
    rng = {"sheetId": tab_id, "startRowIndex": 1,
           "startColumnIndex": col_index, "endColumnIndex": col_index + 1}
    return {"ranges": [rng], "booleanRule": {
        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": FIND_CONTACT}]},
        "format": {"backgroundColor": AMBER}}}


def sheet_meta(service, sid, tab):
    for s in service.spreadsheets().get(spreadsheetId=sid).execute()["sheets"]:
        if s["properties"]["title"] == tab:
            return s["properties"]["sheetId"], s.get("conditionalFormats", [])
    sys.exit(f"Tab '{tab}' not found.")


def has_find_contact_rule(cf_rules) -> bool:
    for r in cf_rules:
        cond = r.get("booleanRule", {}).get("condition", {})
        if cond.get("type") == "TEXT_EQ":
            vals = [v.get("userEnteredValue") for v in cond.get("values", [])]
            if FIND_CONTACT in vals:
                return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="Apply (default: dry-run report)")
    args = parser.parse_args()

    service = get_sheets_service()
    sid = sheet_id()
    tab = "Tracker"
    values = service.spreadsheets().values()

    tr = Tab(service, tab)
    for h in ("URL", "Outcome", "Date Applied", "Follow-up Date", "App Status",
              "Resume", "Cover Letter", "Follow-up Contact", "Follow-Up", "App Qns",
              "Action Req."):
        if tr.col_index(h) is None:
            sys.exit(f"Tracker has no '{h}' column — not the expected state. Aborting.")

    ar_col = tr.col_letter("Action Req.")
    new_formula = action_req_formula(tr)
    cur = values.get(spreadsheetId=sid, range=f"'{tab}'!{ar_col}2",
                     valueRenderOption="FORMULA").execute().get("values", [[""]])[0][0]
    tab_id, cf_rules = sheet_meta(service, sid, tab)

    formula_changed = cur.strip() != new_formula.strip()
    rule_present = has_find_contact_rule(cf_rules)

    if not args.yes:
        print("[dry-run] Would update Action Req.:")
        print(f"  - Rewrite Action Req. formula: {'yes' if formula_changed else 'no (already current)'}")
        if formula_changed:
            print(f"      new: {new_formula}")
        print(f"  - Add amber '{FIND_CONTACT}' conditional-format rule: "
              f"{'no (already present)' if rule_present else 'yes'}")
        if not formula_changed and rule_present:
            print("  Nothing to do — already applied.")
        print("Re-run with --yes to apply.")
        return

    if not formula_changed and rule_present:
        print("Already applied — Action Req. formula current and 'Find Contact' rule present. "
              "Nothing to do.")
        return

    if formula_changed:
        values.update(spreadsheetId=sid, range=f"'{tab}'!{ar_col}2",
                      valueInputOption="USER_ENTERED",
                      body={"values": [[new_formula]]}).execute()
        print(f"Rewrote Action Req. formula (Find Contact rung + Not Required fall-through).")
    else:
        print("Action Req. formula already current — left as-is.")

    if not rule_present:
        col_index = tr.col_index("Action Req.")
        service.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": [
            {"addConditionalFormatRule": {"index": 0,
                                          "rule": find_contact_rule(tab_id, col_index)}}
        ]}).execute()
        print(f"Added amber '{FIND_CONTACT}' conditional-format rule.")
    else:
        print(f"'{FIND_CONTACT}' rule already present — left as-is.")

    # verify
    after = values.get(spreadsheetId=sid, range=f"'{tab}'!{ar_col}2",
                       valueRenderOption="FORMULA").execute().get("values", [[""]])[0][0]
    _, cf_after = sheet_meta(service, sid, tab)
    bad = []
    if FIND_CONTACT not in after:
        bad.append("  Action Req. formula does not contain the 'Find Contact' rung")
    if '(W2:W="Not Required")' in after or '="Not Required")+' in after:
        bad.append("  'Not Required' still present in the stale clause")
    if not has_find_contact_rule(cf_after):
        bad.append("  'Find Contact' conditional-format rule missing after apply")
    if bad:
        print(f"WARNING: {len(bad)} issue(s):", file=sys.stderr)
        print("\n".join(bad), file=sys.stderr)
        sys.exit(1)
    print("Verified: Find Contact rung present, Not Required fall-through in place, amber rule live.")


if __name__ == "__main__":
    main()
