#!/usr/bin/env python3
"""Diff schema/sheets.yaml against the live sheet's header rows.

For every tab in the schema:
  - missing tool/formula headers → ERROR (exit 1) — tools cannot run correctly
  - missing manual headers       → WARNING (add them, or run --fix)
  - live headers not in schema   → WARNING (user-owned; tools will never touch
    them — add to the schema only if tools should manage them)
  - tab missing entirely         → ERROR

--fix appends any missing headers into the first free row-1 cells of that tab
(never moves or renames existing columns).

Run as step 0 of every workflow, and after every schema/sheets.yaml edit.
"""
import sys
import argparse
from sheets_common import (get_sheets_service, sheet_id, load_schema,
                           norm_header, col_to_letter)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true",
                        help="Append missing headers to each tab's row 1")
    parser.add_argument("--tab", help="Check a single tab only")
    args = parser.parse_args()

    schema = load_schema()
    service = get_sheets_service()
    sid = sheet_id()

    live_tabs = {s["properties"]["title"]
                 for s in service.spreadsheets().get(spreadsheetId=sid).execute()["sheets"]}

    errors, warnings = [], []
    tabs = {args.tab: schema["tabs"][args.tab]} if args.tab else schema["tabs"]

    for tab_name, spec in tabs.items():
        if tab_name not in live_tabs:
            # Skills tabs are created on first /refresh-skills — warn, don't fail
            (warnings if tab_name.startswith("Skills") else errors).append(
                f"[{tab_name}] tab missing from spreadsheet")
            continue

        row1 = service.spreadsheets().values().get(
            spreadsheetId=sid, range=f"'{tab_name}'!1:1",
        ).execute().get("values", [[]])
        live = row1[0] if row1 else []
        live_norms = {norm_header(h) for h in live if str(h).strip()}

        missing = []
        for h in spec["headers"]:
            if norm_header(h["name"]) not in live_norms:
                missing.append(h)
                target = errors if h["kind"] in ("tool", "formula") else warnings
                target.append(f"[{tab_name}] missing {h['kind']} column: '{h['name']}'")

        schema_norms = {norm_header(h["name"]) for h in spec["headers"]}
        for h in live:
            if str(h).strip() and norm_header(h) not in schema_norms:
                warnings.append(f"[{tab_name}] unknown column '{h.strip()}' — user-owned; "
                                f"tools ignore it (add to schema/sheets.yaml to manage it)")

        if missing and args.fix:
            start = len(live)
            new_cells = [h["name"] for h in missing]
            end_letter = col_to_letter(start + len(new_cells) - 1)
            service.spreadsheets().values().update(
                spreadsheetId=sid,
                range=f"'{tab_name}'!{col_to_letter(start)}1:{end_letter}1",
                valueInputOption="RAW",
                body={"values": [new_cells]},
            ).execute()
            print(f"[{tab_name}] added header(s): {', '.join(new_cells)}")
            # fixed → downgrade their error/warning entries
            fixed_names = {h["name"] for h in missing}
            errors[:] = [e for e in errors
                         if not any(f"'{n}'" in e and e.startswith(f"[{tab_name}]") for n in fixed_names)]
            warnings[:] = [w for w in warnings
                           if not any(f"'{n}'" in w and w.startswith(f"[{tab_name}]") for n in fixed_names)]

    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(f"\n{len(errors)} error(s) — run with --fix to append missing headers, "
              f"or align schema/sheets.yaml (version "
              f"{schema['schema_version']}) with the sheet.", file=sys.stderr)
        sys.exit(1)
    print(f"Schema v{schema['schema_version']} OK "
          f"({len(warnings)} warning(s), {len(tabs)} tab(s) checked).")


if __name__ == "__main__":
    main()
