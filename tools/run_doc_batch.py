#!/usr/bin/env python3
"""Deterministic driver for workflow 03's per-row document pipeline.

The agent's judgment lives in the MANIFEST (built before any paid call):
which rows, fresh vs revise, template choice, which comments to consume.
This driver executes the mechanical ladder per doc —

    resume:                          pending → generated → compiled → page_ok → saved_local → staged
    cover_letter/follow_up/app_questions: pending → generated → staged   (plain text — no compile/save)

then one batch push and per-row Tracker write-back (statuses, Docs (Link),
Docs Gen Date, Template, ✓-applied comment prefixes). Progress is saved to
the manifest after every step, so a failed batch resumes with --resume and
NEVER re-fires a paid generation call or re-consumes a comment.

Manifest shape (.tmp/doc_batch_manifest.json), built by the agent:
{
  "batch_date": "2026-07-14",
  "rows": [{
    "url": "...", "company": "...", "job_title": "...",
    "folder_date": "14-07",            # Tracker 'Docs Gen Date' if set, else today DD-MM
    "docs_gen_date_was_blank": true,   # write Docs Gen Date back after push
    "docs": {
      "resume":       {"mode": "fresh", "template": "templates/resume_ml_research.tex",
                       "comments": null, "comment_header": "Resume - Comments"},
      "cover_letter": {"mode": "revise", "revise_path": ".tmp/job_app_docs_repo/.../x.md",
                       "comments": "...", "comment_header": "Cover Letter - Comments"},
      "follow_up":    {...},
      "app_questions": {"mode": "fresh", "comments": "<question text — required, not optional>",
                        "comment_header": "App Qns - Comments"}
    }}]
}
(status/error/scratch_dir/folder_url fields are added by the driver.)

Usage:
  python3 tools/run_doc_batch.py --manifest .tmp/doc_batch_manifest.json --validate
  python3 tools/run_doc_batch.py --manifest .tmp/doc_batch_manifest.json
  python3 tools/run_doc_batch.py --manifest .tmp/doc_batch_manifest.json --resume
"""
import sys
import json
import argparse
import subprocess
from datetime import date
from pathlib import Path
from naming import sanitize_path_component
from sheets_common import get_sheets_service, Tab

DOC_ORDER = ["resume", "cover_letter", "follow_up", "app_questions"]
DOC_FILES = {"resume": "resume.tex", "cover_letter": "cover_letter.md",
             "follow_up": "followup_message.md", "app_questions": "app_questions.md"}
GENERATORS = {"resume": "tools/generate_resume.py",
              "cover_letter": "tools/generate_cover_letter.py",
              "follow_up": "tools/generate_followup.py",
              "app_questions": "tools/generate_app_questions.py"}
TRIGGER_HEADERS = {"resume": "Resume", "cover_letter": "Cover Letter", "follow_up": "Follow-Up",
                    "app_questions": "App Qns"}
# Docs that skip compile/page-check/save-local — plain text, pushed as-is
PLAIN_TEXT_DOCS = {"cover_letter", "follow_up", "app_questions"}


def save(manifest: dict, path: Path):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2))
    tmp.rename(path)


def run(cmd: list[str], ok_if: str | None = None) -> subprocess.CompletedProcess:
    """Run a tool; raise with its output on failure unless output matches ok_if."""
    print(f"  $ {' '.join(str(c) for c in cmd)}", file=sys.stderr)
    result = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if result.returncode != 0:
        blob = result.stdout + result.stderr
        if ok_if and ok_if in blob:
            return result
        raise RuntimeError(f"{Path(cmd[1] if cmd[0].startswith('python') else cmd[0]).name} "
                           f"failed:\n{blob.strip()[-2000:]}")
    return result


def validate(manifest: dict) -> list[str]:
    problems = []
    if not manifest.get("rows"):
        problems.append("manifest has no rows")
    for i, row in enumerate(manifest.get("rows", [])):
        tag = f"row {i} ({row.get('url', '?')[:60]})"
        for key in ("url", "company", "job_title", "folder_date"):
            if not row.get(key):
                problems.append(f"{tag}: missing {key}")
        if not row.get("docs"):
            problems.append(f"{tag}: no docs requested")
        for doc, spec in (row.get("docs") or {}).items():
            if doc not in DOC_ORDER:
                problems.append(f"{tag}: unknown doc type '{doc}'")
                continue
            mode = spec.get("mode")
            if mode not in ("fresh", "revise"):
                problems.append(f"{tag}/{doc}: mode must be fresh|revise, got {mode!r}")
            if mode == "revise":
                if not spec.get("comments"):
                    problems.append(f"{tag}/{doc}: revise requires comments")
                rp = spec.get("revise_path")
                if not rp or not Path(rp).exists():
                    problems.append(f"{tag}/{doc}: revise_path missing or not found: {rp}")
            if doc == "resume":
                tpl = spec.get("template")
                if not tpl or not Path(tpl).exists():
                    problems.append(f"{tag}/{doc}: template missing or not found: {tpl}")
            if doc == "app_questions" and not spec.get("comments"):
                problems.append(f"{tag}/{doc}: comments (the question text) are required, "
                                f"fresh or revise")
            if spec.get("comments") and not spec.get("comment_header"):
                problems.append(f"{tag}/{doc}: comments present but no comment_header for write-back")
    return problems


def ladder(row: dict, doc: str, spec: dict, listing_path: Path):
    """Advance one doc through its remaining steps. Mutates spec['status']."""
    scratch = Path(row["scratch_dir"])
    status = spec.get("status", "pending")

    if status == "pending":
        cmd = ["python3", GENERATORS[doc], "--listing", listing_path, "--out-dir", scratch]
        if doc == "resume":
            cmd += ["--template", spec["template"]]
        if spec["mode"] == "revise":
            cmd += ["--revise", spec["revise_path"]]
        if spec.get("comments"):
            cmd += ["--comments", spec["comments"]]
        run(cmd)
        status = spec["status"] = "generated"

    if doc in PLAIN_TEXT_DOCS:
        return  # no compile/save steps; staging happens per row

    if status == "generated":
        run(["python3", "tools/compile_pdf.py", "--tex", scratch / DOC_FILES[doc]])
        pdf = scratch / DOC_FILES[doc].replace(".tex", ".pdf")
        from pypdf import PdfReader
        pages = len(PdfReader(str(pdf)).pages)
        if doc == "resume" and pages != 1:
            # status stays "generated" (not committed past compile) so --resume
            # recompiles against the trimmed .tex instead of re-checking the stale PDF
            raise RuntimeError(f"resume.pdf is {pages} pages — trim the weakest bullets "
                               f"in {scratch / 'resume.tex'} and re-run with --resume")
        status = spec["status"] = "page_ok"

    if status == "page_ok":
        pdf = scratch / DOC_FILES[doc].replace(".tex", ".pdf")
        run(["python3", "tools/save_local_copy.py", "--pdf", pdf, "--company", row["company"],
             "--job-title", row["job_title"], "--doc-type", doc])
        spec["status"] = "saved_local"


def stage_row(row: dict):
    """Commit this row's generated docs into the docs-repo clone (no push)."""
    docs = row["docs"]
    resume_or_cl = [d for d in ("resume", "cover_letter") if d in docs]
    stages = []
    if resume_or_cl:
        stages.append("cover_letter" if "cover_letter" in docs else "resume")
    if "follow_up" in docs:
        stages.append("follow_up")
    if "app_questions" in docs:
        stages.append("app_questions")
    for stage in stages:
        result = run(["python3", "tools/push_docs_to_github.py", "--stage", stage,
                      "--src-dir", row["scratch_dir"], "--company", row["company"],
                      "--job-title", row["job_title"], "--date", row["folder_date"],
                      "--no-push", "--no-delete-src"],
                     ok_if="nothing to commit")  # identical revision — already current
        for line in result.stdout.splitlines():
            if line.startswith("FOLDER_URL="):
                row["folder_url"] = line.split("=", 1)[1]
            if line.startswith("FOLDER_DATE="):
                row["folder_date"] = line.split("=", 1)[1]
    for d in docs.values():
        if d.get("status") != "failed":
            d["status"] = "staged"


def write_back(row: dict, tracker: Tab):
    row_num = tracker.find_row(row["url"])
    if row_num is None:
        raise RuntimeError(f"URL not in Tracker (was the row synced?): {row['url']}")
    today = date.today().isoformat()
    cells = {}
    for doc, spec in row["docs"].items():
        if spec.get("status") != "staged":
            continue
        cells[TRIGGER_HEADERS[doc]] = "Generated"
        if spec.get("comments") and spec.get("comment_header"):
            cells[spec["comment_header"]] = f"✓ applied {today} — {spec['comments']}"
        if doc == "resume" and spec.get("template"):
            cells["Template"] = Path(spec["template"]).stem
    if row.get("folder_url"):
        cells["Docs (Link)"] = row["folder_url"]
    if row.get("docs_gen_date_was_blank"):
        cells["Docs Gen Date"] = row["folder_date"]
    tracker.write_cells(row_num, cells, raw=False)
    row["written_back"] = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=".tmp/doc_batch_manifest.json")
    parser.add_argument("--resume", action="store_true",
                        help="Continue a partially-run manifest (skips completed steps)")
    parser.add_argument("--validate", action="store_true", help="Check the manifest and exit")
    parser.add_argument("--skip-push", action="store_true",
                        help="Stage + commit only; finish later with push_docs_to_github.py --push-only + --resume")
    args = parser.parse_args()

    mpath = Path(args.manifest)
    manifest = json.loads(mpath.read_text())

    problems = validate(manifest)
    if problems:
        print("Manifest problems:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)
    if args.validate:
        docs = sum(len(r["docs"]) for r in manifest["rows"])
        print(f"Manifest OK: {len(manifest['rows'])} row(s), {docs} doc(s). "
              f"Estimated generation cost ≈ ${docs * 0.05:.2f}–{docs * 0.10:.2f}.")
        return

    started = any(spec.get("status") not in (None, "pending")
                  for row in manifest["rows"] for spec in row["docs"].values())
    if started and not args.resume:
        sys.exit("This manifest has already been (partially) run — pass --resume to "
                 "continue it, or point --manifest at a new file.")

    service = get_sheets_service()
    tracker = Tab(service, "Tracker")
    curated = Tab(service, "Curated Listings")

    # Clear local review copies once per batch (not on resume). Resume is the
    # only doc that produces one — cover_letter/follow_up are plain text
    # pushed straight to GitHub, so a cover-letter-only batch must NOT wipe
    # applications/ (it holds review PDFs from a prior resume batch).
    if not manifest.get("cleared_applications") and any(
            "resume" in row["docs"] for row in manifest["rows"]):
        run(["python3", "tools/save_local_copy.py", "--clear"])
        manifest["cleared_applications"] = True
        save(manifest, mpath)

    failures = 0
    for row in manifest["rows"]:
        print(f"\n=== {row['job_title']} @ {row['company']} ===", file=sys.stderr)
        try:
            if "scratch_dir" not in row:
                company = sanitize_path_component(row["company"])
                role = sanitize_path_component(row["job_title"])
                row["scratch_dir"] = f".tmp/applications/{company}_{role}_{manifest.get('batch_date', date.today().isoformat())}"
                save(manifest, mpath)
            scratch = Path(row["scratch_dir"])
            scratch.mkdir(parents=True, exist_ok=True)

            listing_path = scratch / "listing.json"
            if not listing_path.exists():
                listing = next((r for r in curated.read_rows()
                                if r.get("url", "").strip().lower() == row["url"].strip().lower()), None)
                if listing is None:
                    raise RuntimeError("no Curated Listings row for this URL — run /extract-curate first")
                listing_path.write_text(json.dumps(listing, indent=2))

            current_doc = None
            for doc in DOC_ORDER:
                if doc not in row["docs"]:
                    continue
                spec = row["docs"][doc]
                if spec.get("status") == "failed":  # --resume: retry from the failed step
                    spec["status"] = spec.pop("resume_from", "pending")
                    spec.pop("error", None)
                if spec.get("status") == "staged":
                    continue
                current_doc = doc
                ladder(row, doc, spec, listing_path)
                save(manifest, mpath)
            current_doc = None

            # done pre-stage: tex docs reach saved_local, follow_up stops at generated
            if any(spec.get("status") in ("generated", "saved_local")
                   for spec in row["docs"].values()):
                stage_row(row)
                save(manifest, mpath)

        except Exception as e:
            failures += 1
            if current_doc:  # record where it stopped so --resume retries the same step
                spec = row["docs"][current_doc]
                spec["resume_from"] = spec.get("status", "pending")
                spec["status"] = "failed"
                spec["error"] = str(e)
            else:
                row["stage_error"] = str(e)
            save(manifest, mpath)
            print(f"  FAILED: {e}", file=sys.stderr)
            continue

    staged_rows = [r for r in manifest["rows"]
                   if any(s.get("status") == "staged" for s in r["docs"].values())]

    if args.skip_push:
        print(f"\nStaged {len(staged_rows)} row(s); skipped push as requested. "
              f"Finish with: python3 tools/push_docs_to_github.py --push-only, "
              f"then re-run with --resume for the write-back.")
        return

    if staged_rows and not manifest.get("pushed"):
        print("\nPushing batch...", file=sys.stderr)
        run(["python3", "tools/push_docs_to_github.py", "--push-only"])
        manifest["pushed"] = True
        save(manifest, mpath)

    if manifest.get("pushed"):
        for row in staged_rows:
            if not row.get("written_back"):
                write_back(row, tracker)
                save(manifest, mpath)

    # Clean up scratch dirs for fully written-back rows
    import shutil
    for row in manifest["rows"]:
        if row.get("written_back") and row.get("scratch_dir") and Path(row["scratch_dir"]).exists():
            shutil.rmtree(row["scratch_dir"])

    done = sum(1 for r in manifest["rows"] if r.get("written_back"))
    print(f"\nBatch done: {done}/{len(manifest['rows'])} row(s) generated, pushed, "
          f"written back{f'; {failures} FAILED (fix + re-run with --resume)' if failures else ''}.")
    for row in manifest["rows"]:
        if row.get("written_back"):
            print(f"  {row['job_title']} @ {row['company']} → {row.get('folder_url', '?')}")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
