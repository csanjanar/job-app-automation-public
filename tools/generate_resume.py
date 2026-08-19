#!/usr/bin/env python3
"""Generate a tailored LaTeX resume from a job listing and career profile."""
import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from generate_common import load_listing, require_profile, load_revise_doc, resolve_out_dir

load_dotenv()

SYSTEM_PROMPT = """You are an expert resume writer. You will be given:
1. A comprehensive career profile (YAML + narrative sections)
2. A LaTeX resume template (one-page, Jake's Resume style)
3. A job listing with structured fields

Your task: produce a tailored resume.tex that:
- Selects and orders the 3–4 most relevant projects and experience bullets for this specific role
- Mirrors the language and keywords from the job listing naturally — no generic phrases
- Adjusts the Technical Skills section to front-load tools/concepts relevant to this role
- Preserves ALL LaTeX formatting exactly — do not change preamble, page margins, or custom commands
- Uses only these custom commands: \\resumeItem, \\resumeSubheading, \\resumeExpHeading, \\resumeProjectHeading, \\resumeSubHeadingListStart/End, \\resumeItemListStart/End
- MUST fit on one page — if content is too long, trim less-relevant bullets (never truncate mid-bullet)
- Does NOT fabricate any experience, skills, credentials, or metrics not in the profile
- Does NOT add new LaTeX sections or packages

If given an EXISTING DOCUMENT plus USER FEEDBACK: revise that document, making only the changes needed to address the feedback while keeping everything else intact (same rules apply — one page, no fabrication).

If PER-APPLICATION INSTRUCTIONS are provided, treat them as the highest-priority tailoring signal after the factual constraints (no fabrication, one page).

Return ONLY the complete LaTeX source code. No explanation, no markdown fences, no ```latex wrapper."""


def generate_resume(listing: dict, template_path: Path, profile_path: Path,
                    existing_doc: str | None = None, comments: str | None = None) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    profile_text = profile_path.read_text()
    template_text = template_path.read_text()
    listing_text = json.dumps(listing, indent=2)

    if existing_doc:
        task = (f"JOB LISTING:\n{listing_text}\n\nEXISTING DOCUMENT:\n{existing_doc}\n\n"
                f"USER FEEDBACK TO INCORPORATE:\n{comments}\n\n"
                "Revise the existing resume.tex to address the feedback. Change only what the feedback requires.")
    else:
        task = f"JOB LISTING:\n{listing_text}\n\n"
        if comments:
            task += ("PER-APPLICATION INSTRUCTIONS FROM ALEX (row-specific directives for THIS "
                     "application — follow them, letting them override default emphasis/selection "
                     "choices; they are never license to fabricate anything not in the profile):\n"
                     f"{comments}\n\n")
        task += "Generate the tailored resume.tex now."

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    # Cache the profile + template — they're the same across calls
                    {
                        "type": "text",
                        "text": f"CAREER PROFILE:\n{profile_text}\n\nLATEX TEMPLATE:\n{template_text}",
                        "cache_control": {"type": "ephemeral"},
                    },
                    {"type": "text", "text": task},
                ],
            }
        ],
    )

    return message.content[0].text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--listing", required=True, help="Path to extracted fields JSON")
    parser.add_argument("--template", default="templates/resume_base.tex", help="LaTeX template path")
    parser.add_argument("--profile", default="profile/career_profile.md", help="Career profile path")
    parser.add_argument("--out-dir", help="Output directory (default: .tmp/applications/{Company}_{Role}_{date})")
    parser.add_argument("--revise", help="Path to the previously generated resume .tex to revise")
    parser.add_argument("--comments", help="User comments to incorporate (required with --revise)")
    args = parser.parse_args()

    listing = load_listing(args.listing)
    template_path = Path(args.template)
    profile_path = require_profile(args.profile)

    if not template_path.exists():
        sys.exit(f"Template not found: {template_path}")

    existing_doc = load_revise_doc(args.revise, args.comments)
    out_dir = resolve_out_dir(listing, args.out_dir)

    print("Revising resume..." if existing_doc else "Generating resume...", file=sys.stderr)
    latex = generate_resume(listing, template_path, profile_path,
                            existing_doc=existing_doc, comments=args.comments)

    out_path = out_dir / "resume.tex"
    out_path.write_text(latex)
    print(f"Saved to {out_path}")
    print(f"Next: python3 tools/compile_pdf.py --tex {out_path}")
