#!/usr/bin/env python3
"""Compile a LaTeX file to PDF using tectonic."""
import sys
import argparse
import subprocess
from pathlib import Path


def compile_pdf(tex_path: Path) -> Path:
    result = subprocess.run(
        ["tectonic", tex_path.name],
        capture_output=True,
        text=True,
        cwd=tex_path.parent,
    )

    if result.returncode != 0:
        print("tectonic stderr:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"tectonic failed (exit {result.returncode})")

    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"PDF not produced at {pdf_path}")

    return pdf_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tex", required=True, help="Path to .tex file")
    args = parser.parse_args()

    tex_path = Path(args.tex)
    if not tex_path.exists():
        print(f"File not found: {tex_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Compiling {tex_path}...", file=sys.stderr)
    try:
        pdf_path = compile_pdf(tex_path)
        print(f"PDF saved to {pdf_path}")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
