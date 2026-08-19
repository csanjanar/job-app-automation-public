#!/usr/bin/env python3
"""Generate a tailored plain-text cover letter (.md) from a job listing and career profile."""
import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from generate_common import load_listing, require_profile, load_revise_doc, resolve_out_dir

load_dotenv()

SYSTEM_PROMPT = """You are an expert cover letter writer. You will be given:
1. A comprehensive career profile (YAML + narrative sections)
2. A job listing with structured fields

Your task: write a tailored cover letter as plain text (~250-300 words), structured as:
- Salutation (use the one provided)
- 3-4 body paragraphs: opens with genuine enthusiasm for the specific role and company, highlights 2-3 experiences from the profile most relevant to this listing, uses language from the listing naturally without parroting it, closes with a clear low-pressure call to action
- Sign-off: "Best regards,\\nAlex"

No date line, no address block, no letterhead — this is a lean message body meant to be pasted into an application portal or email, not a formal printed letter.

Sounds human and specific, not generic; does NOT fabricate experience, skills, or metrics not in the profile.

If given an EXISTING MESSAGE plus USER FEEDBACK: revise that message, making only the changes needed to address the feedback while keeping everything else intact.

If PER-APPLICATION INSTRUCTIONS are provided, treat them as the highest-priority tailoring signal after the factual constraints (no fabrication).

Return ONLY the plain-text message. No explanation, no markdown fences, no headers."""


def generate_cover_letter(listing: dict, profile_path: Path,
                          existing_doc: str | None = None, comments: str | None = None) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    profile_text = profile_path.read_text()
    listing_text = json.dumps(listing, indent=2)

    recruiter = listing.get("recruiter_hr_contact")
    salutation = f"Dear {recruiter}," if recruiter else "Dear Hiring Manager,"

    if existing_doc:
        task = (f"JOB LISTING:\n{listing_text}\n\nEXISTING MESSAGE:\n{existing_doc}\n\n"
                f"USER FEEDBACK TO INCORPORATE:\n{comments}\n\n"
                "Revise the existing cover letter to address the feedback. Change only what the feedback requires.")
    else:
        task = f"JOB LISTING:\n{listing_text}\n\nSalutation to use: {salutation}\n\n"
        if comments:
            task += ("PER-APPLICATION INSTRUCTIONS FROM ALEX (row-specific directives for THIS "
                     "application — follow them, letting them override default emphasis/selection "
                     "choices; they are never license to fabricate anything not in the profile):\n"
                     f"{comments}\n\n")
        task += "Write the tailored cover letter now."

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    # Cache the profile — same across calls
                    {
                        "type": "text",
                        "text": f"CAREER PROFILE:\n{profile_text}",
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
    parser.add_argument("--profile", default="profile/career_profile.md")
    parser.add_argument("--out-dir", help="Output directory (default: .tmp/applications/{Company}_{Role}_{date})")
    parser.add_argument("--revise", help="Path to the previously generated cover letter .md to revise")
    parser.add_argument("--comments", help="User comments to incorporate (required with --revise)")
    args = parser.parse_args()

    listing = load_listing(args.listing)
    profile_path = require_profile(args.profile)
    existing_doc = load_revise_doc(args.revise, args.comments)
    out_dir = resolve_out_dir(listing, args.out_dir)

    print("Revising cover letter..." if existing_doc else "Generating cover letter...", file=sys.stderr)
    text = generate_cover_letter(listing, profile_path,
                                 existing_doc=existing_doc, comments=args.comments)

    out_path = out_dir / "cover_letter.md"
    out_path.write_text(text)
    print(f"Saved to {out_path}")
