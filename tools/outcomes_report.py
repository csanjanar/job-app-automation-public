#!/usr/bin/env python3
"""Aggregate application outcomes for workflow 05 (/review-outcomes).

Deterministic reporting only — joins Tracker and Curated Listings by URL and
prints a markdown report; the agent interprets it and proposes template /
prompt / targeting changes (approved diffs only).

App Status is lifecycle (To Apply / Applied / Completed); the actual result
lives in Outcome (Interview / Offer / Rejected / Closed). The funnel counts
applications off App Status and responses/results off Outcome.

Sections:
  1. Funnel        — App Status + Outcome counts, days-pending for un-answered rows
  2. Breakdowns    — applied rate + Outcome mix by Role Family, Employer Type,
                     ML Domain, Template, Fit Score (fit-calibration check)
  3. Directives    — every ✓-applied comment (Resume/Cover Letter/Follow-Up), grouped, for
                     spotting recurring tailoring instructions to promote
  4. Manual edits  — docs-repo commits that are NOT generation pushes
                     ("Add docs for ..."), i.e. hand-tweaks worth mining

Usage: python3 tools/outcomes_report.py [--out .tmp/outcomes_report.md]
"""
import re
import argparse
import subprocess
from datetime import date, datetime
from pathlib import Path
from collections import Counter, defaultdict
from sheets_common import get_sheets_service, Tab

CLONE_DIR = Path(".tmp/job_app_docs_repo")
APPLIED_STATES = {"Applied", "Completed"}   # App Status values that count as "applied"
COMMENT_KEYS = ["resume_comments", "cover_letter_comments", "follow_up_comments"]
APPLIED_MARK = re.compile(r"^✓ applied (\d{4}-\d{2}-\d{2}) — (.*)$", re.DOTALL)


def pct(n, d):
    return f"{n}/{d} ({n * 100 // d}%)" if d else "0/0"


def breakdown(rows: list[dict], dim: str, label: str, lines: list[str]):
    groups = defaultdict(lambda: {"total": 0, "applied": 0, "outcomes": Counter()})
    for r in rows:
        key = r.get(dim, "").strip() or "(blank)"
        g = groups[key]
        g["total"] += 1
        if r.get("app_status", "").strip() in APPLIED_STATES:
            g["applied"] += 1
        oc = r.get("outcome", "").strip()
        if oc:
            g["outcomes"][oc] += 1
    if not groups:
        return
    lines.append(f"\n### By {label}\n")
    lines.append("| " + label + " | Applied+ | Interview/Offer | Rejected | Outcomes |")
    lines.append("|---|---|---|---|---|")
    for key, g in sorted(groups.items(), key=lambda kv: -kv[1]["total"]):
        oc = g["outcomes"]
        pos = oc["Interview"] + oc["Offer"]
        oc_str = ", ".join(f"{s}:{v}" for s, v in oc.most_common()) or "—"
        lines.append(f"| {key} | {g['applied']}/{g['total']} | {pos} | {oc['Rejected']} | {oc_str} |")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="Also write the report to this path")
    args = parser.parse_args()

    service = get_sheets_service()
    tracker_rows = Tab(service, "Tracker").read_rows()
    curated = {r.get("url", "").strip(): r for r in Tab(service, "Curated Listings").read_rows()}

    rows = []
    for t in tracker_rows:
        url = t.get("url", "").strip()
        if not url:
            continue
        joined = dict(curated.get(url, {}))
        joined.update({k: v for k, v in t.items() if str(v).strip()})
        rows.append(joined)

    lines = [f"# Application Outcomes Report — {date.today().isoformat()}\n"]

    # 1. Funnel
    statuses = Counter(r.get("app_status", "").strip() or "(blank)" for r in rows)
    outcomes = Counter(oc for r in rows if (oc := r.get("outcome", "").strip()))
    applied = [r for r in rows if r.get("app_status", "").strip() in APPLIED_STATES]
    responded = [r for r in rows if r.get("outcome", "").strip()]
    lines.append("## Funnel\n")
    lines.append(f"- Tracked: {len(rows)} | Applied: {len(applied)} | "
                 f"Responses: {pct(len(responded), len(applied))} | "
                 f"Interview+: {outcomes['Interview'] + outcomes['Offer']}")
    lines.append("- Status counts: " + ", ".join(f"{s}: {n}" for s, n in statuses.most_common()))
    if outcomes:
        lines.append("- Outcome counts: " + ", ".join(f"{s}: {n}" for s, n in outcomes.most_common()))
    pending = []
    for r in applied:
        if r.get("app_status") in APPLIED_STATES and not r.get("outcome", "").strip() \
                and r.get("date_applied", "").strip():
            for fmt in ("%Y-%m-%d", "%d-%m-%y", "%d-%m-%Y", "%d/%m/%Y", "%d/%m/%y"):
                try:
                    days = (date.today() - datetime.strptime(r["date_applied"].strip(), fmt).date()).days
                    pending.append((days, r))
                    break
                except ValueError:
                    continue
    if pending:
        lines.append("- Awaiting response: "
                     + "; ".join(f"{r.get('job_title', '?')} @ {r.get('company', '?')} ({d}d)"
                                 for d, r in sorted(pending, reverse=True)))

    # 2. Breakdowns (incl. fit calibration)
    lines.append("\n## Breakdowns")
    for dim, label in [("role_family", "Role Family"), ("employer_type", "Employer Type"),
                       ("ml_domain", "ML Domain"), ("template", "Template"),
                       ("fit_score", "Fit Score")]:
        breakdown(rows, dim, label, lines)

    # 3. Consumed directives (recurring ones are promotion candidates)
    lines.append("\n## Consumed comment directives (✓ applied)\n")
    directives = []
    for r in rows:
        for key in COMMENT_KEYS:
            m = APPLIED_MARK.match(r.get(key, "").strip())
            if m:
                directives.append((m.group(2).strip(), key.replace("_comments", ""),
                                   r.get("company", "?")))
    if directives:
        by_text = defaultdict(list)
        for text, doc, company in directives:
            by_text[text].append(f"{doc}@{company}")
        for text, uses in sorted(by_text.items(), key=lambda kv: -len(kv[1])):
            flag = " **[recurring — promotion candidate]**" if len(uses) > 1 else ""
            flag = " **[flagged !general]**" if text.lower().startswith("!general") else flag
            lines.append(f"- ({len(uses)}×) \"{text}\" — {', '.join(uses)}{flag}")
    else:
        lines.append("- none yet")

    # 4. Manual post-generation edits in the docs repo
    lines.append("\n## Manual doc edits (docs repo commits that aren't generation pushes)\n")
    if CLONE_DIR.exists():
        log = subprocess.run(
            ["git", "log", "--pretty=%h %ad %s", "--date=short", "--no-merges"],
            cwd=CLONE_DIR, capture_output=True, text=True).stdout.splitlines()
        manual = [l for l in log if " Add docs for " not in l]
        if manual:
            lines.append("Inspect each with `git -C .tmp/job_app_docs_repo show <hash>` — "
                         "consistent hand-edits are template/prompt promotion candidates:\n")
            lines.extend(f"- {l}" for l in manual)
        else:
            lines.append("- none")
    else:
        lines.append(f"- docs repo clone not found at {CLONE_DIR} — "
                     f"run: gh repo clone $GITHUB_DOCS_REPO {CLONE_DIR}")

    report = "\n".join(lines)
    print(report)
    if args.out:
        Path(args.out).write_text(report)
        print(f"\n(saved to {args.out})")


if __name__ == "__main__":
    main()
