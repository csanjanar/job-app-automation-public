#!/usr/bin/env python3
"""Push generated application docs to the private GitHub docs repo via gh CLI."""
import os
import sys
import shutil
import argparse
import subprocess
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from naming import sanitize_path_component

load_dotenv()

CLONE_DIR = Path(".tmp/job_app_docs_repo")

STAGE_FILES = {
    # Only the .tex source is pushed — the compiled PDF stays local-only
    # (applications/, named for easy submission; see save_local_copy.py).
    "resume": [
        ("resume.tex", "Alex_Resume_{role}.tex"),
    ],
    "cover_letter": [
        ("resume.tex", "Alex_Resume_{role}.tex"),
        ("cover_letter.md", "Alex_CoverLetter_{role}.md"),
    ],
    "follow_up": [
        ("followup_message.md", "Alex_FollowUp_{role}.md"),
    ],
    "app_questions": [
        ("app_questions.md", "Alex_AppQuestions_{role}.md"),
    ],
}
STAGE_ALIASES = {"pending": "resume"}  # back-compat


def run(cmd: list, cwd: Path = None):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"{cmd[0]} failed (exit {result.returncode})")
    return result.stdout.strip()


def ensure_repo_cloned(repo: str):
    if CLONE_DIR.exists():
        run(["git", "pull"], cwd=CLONE_DIR)
    else:
        CLONE_DIR.parent.mkdir(parents=True, exist_ok=True)
        run(["gh", "repo", "clone", repo, str(CLONE_DIR)])


def repo_web_url(repo: str) -> str:
    repo = repo.removesuffix(".git")
    if repo.startswith("http"):
        return repo
    return f"https://github.com/{repo}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=list(STAGE_FILES) + list(STAGE_ALIASES))
    parser.add_argument("--src-dir", help="Local .tmp/applications/{Company}_{Role}_{date}/ scratch folder")
    parser.add_argument("--company")
    parser.add_argument("--job-title")
    parser.add_argument("--date", help="DD-MM folder date — pass the row's Docs Gen Date if set; default today")
    parser.add_argument("--no-push", action="store_true",
                        help="Stage + commit without pushing (batch mode; finish with --push-only)")
    parser.add_argument("--push-only", action="store_true",
                        help="Just push previously committed work — no files copied")
    parser.add_argument("--no-delete-src", action="store_true",
                        help="Keep the local scratch dir after copying")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_DOCS_REPO"))
    args = parser.parse_args()

    if not args.repo:
        print("No repo given: pass --repo or set GITHUB_DOCS_REPO in .env", file=sys.stderr)
        sys.exit(1)

    if args.push_only:
        if not CLONE_DIR.exists():
            print(f"Nothing to push: {CLONE_DIR} does not exist", file=sys.stderr)
            sys.exit(1)
        run(["git", "push"], cwd=CLONE_DIR)
        print(f"Pushed all pending commits to {args.repo}")
        sys.exit(0)

    for arg_name in ("stage", "src_dir", "company", "job_title"):
        if not getattr(args, arg_name):
            print(f"--{arg_name.replace('_', '-')} is required (unless --push-only)", file=sys.stderr)
            sys.exit(1)
    stage = STAGE_ALIASES.get(args.stage, args.stage)

    src_dir = Path(args.src_dir)
    if not src_dir.exists():
        print(f"Source directory not found: {src_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Cloning/pulling {args.repo}...", file=sys.stderr)
    ensure_repo_cloned(args.repo)

    company = sanitize_path_component(args.company)
    role = sanitize_path_component(args.job_title)
    folder_date = args.date or date.today().strftime("%d-%m")
    folder_name = f"{folder_date}_{company}_{role}"
    target_dir = CLONE_DIR / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for src_name, dest_pattern in STAGE_FILES[stage]:
        src_path = src_dir / src_name
        if not src_path.exists():
            print(f"Expected file not found, skipping: {src_path}", file=sys.stderr)
            continue
        dest_name = dest_pattern.format(role=role)
        shutil.copyfile(src_path, target_dir / dest_name)
        copied.append(dest_name)

    if not copied:
        print("No files copied, aborting.", file=sys.stderr)
        sys.exit(1)

    run(["git", "add", str(folder_name)], cwd=CLONE_DIR)
    run(["git", "commit", "-m", f"Add docs for {args.company} - {args.job_title} ({stage})"], cwd=CLONE_DIR)
    if args.no_push:
        print(f"Committed (not pushed): {folder_name} ({', '.join(copied)})")
    else:
        run(["git", "push"], cwd=CLONE_DIR)
        print(f"Pushed to {args.repo}: {folder_name} ({', '.join(copied)})")

    # Machine-readable outputs for the Tracker write-back (Docs (Link) / Docs Gen Date)
    print(f"FOLDER_DATE={folder_date}")
    print(f"FOLDER_URL={repo_web_url(args.repo)}/tree/main/{folder_name}")

    if not args.no_delete_src:
        shutil.rmtree(src_dir)
        print(f"Removed local scratch dir: {src_dir}", file=sys.stderr)
