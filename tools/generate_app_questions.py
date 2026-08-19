#!/usr/bin/env python3
"""Generate answers to an employer's free-form application questions."""
import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from generate_common import load_listing, require_profile, load_revise_doc, resolve_out_dir

load_dotenv()

SYSTEM_PROMPT = """You are helping someone answer an employer's free-form application questions. You will be given a list of questions (verbatim, as pasted from the application) and a career profile.

For each question:
- Answer only using facts present in the career profile — never fabricate experience, skills, or claims not in it
- Keep answers concise and concrete (specific projects/outcomes over generalities), matched to the question's evident expected length (a one-line question gets a short answer; an essay-style prompt gets several sentences)
- Preserve the question's own wording as a heading, then the answer below it

Format the whole response as Markdown:

**Q: <question text>**

<answer>

**Q: <next question text>**

<answer>

If given EXISTING ANSWERS plus USER FEEDBACK: revise those answers, making only the changes needed to address the feedback while keeping everything else (including question order) intact.

Return only the Markdown Q&A content. No preamble, no explanation."""


def generate_app_questions(listing: dict, profile_path: Path, questions: str,
                            existing_doc: str | None = None) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    profile_text = profile_path.read_text()

    summary = {
        "company": listing.get("company"),
        "job_title": listing.get("job_title"),
        "key_tools_skills": listing.get("key_tools_skills"),
        "ml_domain": listing.get("ml_domain"),
    }

    if existing_doc:
        task = (f"JOB DETAILS:\n{json.dumps(summary, indent=2)}\n\nEXISTING ANSWERS:\n{existing_doc}\n\n"
                f"USER FEEDBACK TO INCORPORATE:\n{questions}\n\n"
                "Revise the answers to address the feedback. Change only what the feedback requires.")
    else:
        task = (f"JOB DETAILS:\n{json.dumps(summary, indent=2)}\n\n"
                f"QUESTIONS TO ANSWER (verbatim from the application):\n{questions}\n\n"
                "Answer each question.")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
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
    parser.add_argument("--revise", help="Path to the previously generated app_questions.md to revise")
    parser.add_argument("--comments", required=True,
                        help="Fresh run: the question text to answer (required — it's the actual "
                             "input, not optional feedback). Revise run: feedback on the existing answers.")
    args = parser.parse_args()

    listing = load_listing(args.listing)
    profile_path = require_profile(args.profile)
    existing_doc = load_revise_doc(args.revise, args.comments)
    out_dir = resolve_out_dir(listing, args.out_dir)

    print("Revising application question answers..." if existing_doc
          else "Generating application question answers...", file=sys.stderr)
    msg = generate_app_questions(listing, profile_path, args.comments, existing_doc=existing_doc)

    out_path = out_dir / "app_questions.md"
    out_path.write_text(msg)
    print(f"Saved to {out_path}")
