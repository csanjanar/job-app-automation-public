#!/usr/bin/env python3
"""Save a local copy of a generated resume/cover letter PDF to Job_Apps/applications/.

Named {Company}_Alex_{JobTitle}_{DocLabel}.pdf — company-first so the
right file is easy to pick out by eye when several are sitting in the
folder at once (the PDF here is local-only; only the .tex is pushed to
the GitHub docs repo, see push_docs_to_github.py).
"""
import sys
import shutil
import argparse
from pathlib import Path
from naming import sanitize_path_component

APPLICATIONS_DIR = Path("applications")

DOC_LABEL = {"resume": "Resume", "cover_letter": "CoverLetter"}


def clear_applications_dir():
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    for f in APPLICATIONS_DIR.iterdir():
        if f.is_file():
            f.unlink()
        else:
            shutil.rmtree(f)


def save_pdf(pdf_path: Path, company: str, job_title: str, doc_type: str = "resume") -> Path:
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    company_part = sanitize_path_component(company)
    role = sanitize_path_component(job_title)
    dest = APPLICATIONS_DIR / f"{company_part}_Alex_{role}_{DOC_LABEL[doc_type]}.pdf"
    shutil.copyfile(pdf_path, dest)
    return dest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear", action="store_true", help="Delete all files in applications/ (once per batch)")
    parser.add_argument("--pdf", help="Path to the generated PDF to copy")
    parser.add_argument("--company", help="Company name, used to name the saved file")
    parser.add_argument("--job-title", help="Job title, used to name the saved file")
    parser.add_argument("--doc-type", choices=DOC_LABEL.keys(), default="resume",
                        help="Names the saved file {Company}_Alex_{JobTitle}_Resume.pdf etc.")
    args = parser.parse_args()

    if args.clear:
        clear_applications_dir()
        print(f"Cleared {APPLICATIONS_DIR}/", file=sys.stderr)

    if args.pdf:
        if not args.company or not args.job_title:
            print("Provide --company and --job-title when saving a PDF", file=sys.stderr)
            sys.exit(1)
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"PDF not found: {pdf_path}", file=sys.stderr)
            sys.exit(1)
        dest = save_pdf(pdf_path, args.company, args.job_title, args.doc_type)
        print(f"Saved {dest}")

    if not args.clear and not args.pdf:
        print("Nothing to do: pass --clear and/or --pdf --job-title", file=sys.stderr)
        sys.exit(1)
