#!/usr/bin/env python3
"""Generate a follow-up/referral or personal-networking outreach message for a
job listing. Format (email/LinkedIn connection note/LinkedIn message/WhatsApp)
and purpose (job follow-up vs. personal networking) are driven by free-form
instructions in the Tracker's Follow-Up - Comments column, which may also
request multiple variants (e.g. a LinkedIn connection note plus a longer
message for after connecting) in one output file."""
import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from generate_common import load_listing, require_profile, load_revise_doc, resolve_out_dir

load_dotenv()

SYSTEM_PROMPT = """You are helping someone reach out about a job opportunity or professional contact. Your default purpose is a job follow-up / referral ask: write a short, natural outreach message that references the specific role and company, briefly mentions 1-2 relevant strengths from the profile, and ends with a clear, low-pressure ask (e.g. a quick call, referral, or introduction).

SHIFT PURPOSE WHEN SIGNALED: if PER-APPLICATION INSTRUCTIONS indicate the contact matters beyond this specific hiring decision — e.g. wanting to learn about their career trajectory, ask further questions, or arrange a chat/meet-up — write a more personal, networking-oriented message instead of a job pitch. Still ground it in the real role/company/profile context, but drop the transactional "consider me for this role" framing in favor of genuine interest in the person and their path. The job/company is what started the conversation, not necessarily what it's about.

MEDIUM: infer the intended medium(s) from PER-APPLICATION INSTRUCTIONS (or context) and match its convention. The word/character counts below are ceilings, not targets to approach — write shorter when the content allows it, and always count before finalizing:
- Email: formal, no more than 180 words (aim for 120-150); a brief natural subject line is fine.
- LinkedIn connection request: STRICT LIMIT 300 characters, including spaces — this is a real platform limit that truncates/rejects longer notes, not a style preference. Budget for it explicitly: 1-2 short sentences, one idea only (who you are + the one specific reason you're reaching out). No sign-off, no "I'd love to connect" filler — the connect action itself says that. If your draft is over 300 characters, cut a clause, don't just trim words.
- LinkedIn message to an existing connection: conversational, no more than 120 words (aim for 80-100) — you're already connected, so skip the self-introduction and get straight to the point.
- WhatsApp: no more than 100 words (aim for 50-80), informal — contractions fine, no corporate phrasing.
- If no medium is specified: default to a general email/LinkedIn-suitable message, no more than 150 words (aim for 100-130), warm and direct, not salesy — the original one-size-fits-all style.

OPTIONAL TAG CONVENTION: a segment may open with `[medium]` and/or `{purpose}` tags, e.g. `[linkedin-connect] {personal}: "mention the FYP overlap"`.
- `[medium]` is one or more of email / linkedin-connect / linkedin-message / whatsapp, joined with `+` if more than one (e.g. `[linkedin-connect + linkedin-message]`). Each medium listed produces its own variant, following that medium's convention above — medium is what forks variants.
- `{purpose}` is optional; its only defined value is `personal` (the networking purpose above, instead of the default follow-up purpose). `{personal + job}` blends both purposes into the same message — purpose modifies content/tone, it does NOT fork additional variants. So `[linkedin-connect + linkedin-message] {personal + job}` produces exactly 2 variants (one per medium), each blending genuine personal interest with the job/referral ask — not 4.
- Each variant gets its own heading per MULTIPLE VARIANTS below, in the order mediums are listed. A separate tagged line starts a separate, independently-tagged variant group.
- Untagged instructions are read as free text exactly as before — infer medium/purpose/variant count from context rather than requiring tags.

MULTIPLE VARIANTS: if PER-APPLICATION INSTRUCTIONS ask for more than one message (e.g. a LinkedIn connection request AND a longer follow-up for after connecting), produce each variant under its own short markdown heading (e.g. "## LinkedIn Connection Request", "## Follow-Up After Connecting"), in the order requested, each following its own medium's convention above. Otherwise, produce exactly one message with no heading.

If a recruiter/contact name is provided, address them by name wherever the medium's convention calls for a greeting (email, LinkedIn message to an existing connection); a connection-request note or WhatsApp message can lead with the name instead of a formal salutation if that reads more naturally.

If given an EXISTING MESSAGE plus USER FEEDBACK: revise that message, making only the changes needed to address the feedback while keeping everything else intact (including which variant(s) are present, unless the feedback asks to add or remove one).

PER-APPLICATION INSTRUCTIONS, when provided, are the highest-priority tailoring signal for purpose, medium, and variant count — after the factual constraint that nothing may be fabricated beyond what's in the profile.

Return the message(s) as plain text/markdown only — no commentary before or after."""


def generate_followup(listing: dict, profile_path: Path,
                      existing_doc: str | None = None, comments: str | None = None) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    profile_text = profile_path.read_text()

    contact = listing.get("recruiter_hr_contact") or "not provided"
    summary = {
        "company": listing.get("company"),
        "job_title": listing.get("job_title"),
        "recruiter_hr_contact": contact,
        "key_tools_skills": listing.get("key_tools_skills"),
        "ml_domain": listing.get("ml_domain"),
    }

    if existing_doc:
        task = (f"JOB DETAILS:\n{json.dumps(summary, indent=2)}\n\nEXISTING MESSAGE:\n{existing_doc}\n\n"
                f"USER FEEDBACK TO INCORPORATE:\n{comments}\n\n"
                "Revise the message to address the feedback. Change only what the feedback requires.")
    else:
        task = f"JOB DETAILS:\n{json.dumps(summary, indent=2)}\n\n"
        if comments:
            task += ("PER-APPLICATION INSTRUCTIONS FROM ALEX (row-specific directives for THIS "
                     "application — follow them, letting them override default emphasis/selection "
                     "choices; they are never license to fabricate anything not in the profile):\n"
                     f"{comments}\n\n")
        task += "Write the outreach message."

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
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
    parser.add_argument("--revise", help="Path to the previously generated follow-up .md to revise")
    parser.add_argument("--comments", help="User comments to incorporate — also where medium "
                        "(email/LinkedIn connection note/LinkedIn message/WhatsApp/etc.), purpose "
                        "(job follow-up vs. personal networking), and multi-variant requests go "
                        "(required with --revise)")
    args = parser.parse_args()

    listing = load_listing(args.listing)
    profile_path = require_profile(args.profile)
    existing_doc = load_revise_doc(args.revise, args.comments)
    out_dir = resolve_out_dir(listing, args.out_dir)

    print("Revising follow-up message..." if existing_doc else "Generating follow-up message...", file=sys.stderr)
    msg = generate_followup(listing, profile_path,
                            existing_doc=existing_doc, comments=args.comments)

    out_path = out_dir / "followup_message.md"
    out_path.write_text(msg)
    print(f"Saved to {out_path}")
