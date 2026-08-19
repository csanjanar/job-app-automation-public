#!/usr/bin/env python3
"""Extract structured job listing fields from raw text using Claude Haiku.

Also produces an advisory fit_score (1-5) + fit_rationale against the
preference sections of profile/career_profile.md — same call, same cost
order (~$0.001/listing). Apply/skip decisions stay manual.
"""
import sys
import os
import json
import argparse
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from sheets_common import classification_lines, load_schema
from profile_common import fit_preference_block

load_dotenv()

FIT_SPEC = load_schema()["fit_score"]
FIT_SCALE = FIT_SPEC["scale"]
FIT_MEANING = FIT_SPEC["meaning"].strip()

# Classification vocabularies come from schema/sheets.yaml — the single source
# shared with the sheet columns and workflows. Edit them there, not here.
SYSTEM_PROMPT = f"""You are a job listing parser. Extract structured information from job listings and return valid JSON only — no explanation, no markdown fences.

You will be told today's date. Job sites often show relative dates ("16 days ago", "3d ago", "Posted 2 weeks ago") instead of absolute ones — compute the absolute date yourself by subtracting from today's date, don't guess or leave it in relative form.

Return an object with exactly these fields:
- url (string)
- job_title (string)
- company (string)
- location (string)
- role_family (string — pick the single best match from: {classification_lines("role_family")}, or null if unclear)
- ml_domain (string — pick the single best match from: {classification_lines("ml_domain")}, or null if unclear)
- work_mode (string — pick the single best match from: {classification_lines("work_mode")}, or null if unclear)
- industry_vertical (string — pick the single best match from: {classification_lines("industry_vertical")}, or null if unclear)
- employer_type (string — pick the single best match from: {classification_lines("employer_type")}, or null if unclear)
- key_tools_skills (array of strings — specific named tools, frameworks, languages, platforms)
- key_concepts_practices (array of strings — methods, architectures, approaches, workflows)
- soft_skills_others (array of strings — interpersonal, organisational, and general professional skills)
- salary (string or null)
- recruiter_hr_contact (string or null, name and/or email if found)
- date_posted (string or null, ISO format YYYY-MM-DD — resolve any relative phrasing like "16 days ago" or "3d ago" against today's date)
- application_deadline (string or null, ISO format YYYY-MM-DD — resolve any relative phrasing the same way)
- fit_score (integer {FIT_SCALE}, judged against the CANDIDATE PREFERENCES block provided with the listing: {FIT_MEANING})
- fit_rationale (string, ONE sentence naming the specific preferences that matched or clashed — cite domains/industries/employer types/dealbreakers from the preferences, not generic praise)

Use null for any field not found in the listing (fit_score/fit_rationale are always produced)."""


def extract_fields(text: str, url: str = "", reference_date: str = "") -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # Relative dates ("3d ago") must resolve against the day the text was
    # scraped, not the day extraction runs — pass Raw Listings col C here.
    ref = reference_date or date.today().isoformat()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content":
                   f"CANDIDATE PREFERENCES (for fit_score/fit_rationale only):\n"
                   f"{fit_preference_block()}\n\n"
                   f"Today's date: {ref}\nURL: {url}\n\n{text}"}],
    )
    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        raw = raw.rsplit("```", 1)[0].strip()
    return json.loads(raw)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Path to .json (from scrape_listing) or .txt file")
    parser.add_argument("--url", default="", help="URL of the listing")
    parser.add_argument("--retry", action="store_true", help="Retry on parse failure")
    parser.add_argument("--scraped-date", default="",
                        help="Date the text was scraped (YYYY-MM-DD, Raw Listings col C); "
                             "used as the reference for resolving relative dates. Default: today")
    parser.add_argument("--override-job-title", default="")
    parser.add_argument("--override-company", default="")
    parser.add_argument("--override-salary", default="")
    parser.add_argument("--override-date-posted", default="")
    parser.add_argument("--override-application-deadline", default="")
    args = parser.parse_args()

    # Fields already known from Raw Listings' gather-time prefetch (MCF API /
    # Path B WebFetch) take precedence over Haiku's own derivation — Haiku
    # still runs (it's the only source for role_family/ml_domain/skills/fit
    # score), this just avoids trusting an LLM guess for facts we already
    # have from an authoritative source. See schema/sheets.yaml changelog v3.
    OVERRIDES = {
        "job_title": args.override_job_title,
        "company": args.override_company,
        "salary": args.override_salary,
        "date_posted": args.override_date_posted,
        "application_deadline": args.override_application_deadline,
    }

    if args.input:
        input_path = Path(args.input)
        if input_path.suffix == ".json":
            data = json.loads(input_path.read_text())
            text = data.get("markdown", data.get("text", ""))
            url = args.url or data.get("url", "")
        else:
            text = input_path.read_text()
            url = args.url
    else:
        text = sys.stdin.read()
        url = args.url

    try:
        fields = extract_fields(text, url, args.scraped_date)
    except json.JSONDecodeError as e:
        if not args.retry:
            print(f"JSON parse error: {e}", file=sys.stderr)
            sys.exit(1)
        print("Parse failed, retrying...", file=sys.stderr)
        try:
            fields = extract_fields(text, url, args.scraped_date)
        except json.JSONDecodeError as e2:
            print(f"JSON parse error on retry: {e2}", file=sys.stderr)
            sys.exit(1)

    for key, value in OVERRIDES.items():
        if value:
            fields[key] = value

    # Save to .tmp/
    if args.input:
        stem = Path(args.input).stem
        out_path = Path(".tmp") / f"{stem}_fields.json"
        out_path.write_text(json.dumps(fields, indent=2))
        print(f"Saved to {out_path}", file=sys.stderr)

    print(json.dumps(fields, indent=2))
