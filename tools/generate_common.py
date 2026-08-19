"""Shared CLI plumbing for the three doc generators (resume/cover letter/follow-up).

Purely mechanical fixed-data retrieval — load the listing, validate the
profile path, load an existing doc for --revise, resolve the output
directory. Each generator's actual prompt + API call logic is NOT here;
that's what makes each script a distinct tool.
"""
import sys
import json
from datetime import date
from pathlib import Path
from naming import sanitize_path_component


def load_listing(path: str) -> dict:
    """Load extracted-fields JSON; unwrap a single-element array if given one."""
    listing = json.loads(Path(path).read_text())
    if isinstance(listing, list):
        if not listing:
            sys.exit(f"{path} is an empty JSON array — no listing data")
        listing = listing[0]
    return listing


def require_profile(path: str) -> Path:
    profile_path = Path(path)
    if not profile_path.exists():
        sys.exit(f"Career profile not found: {profile_path}")
    return profile_path


def load_revise_doc(revise: str | None, comments: str | None) -> str | None:
    """Validate + load the existing document for a --revise run; None for fresh."""
    if not revise:
        return None
    if not comments:
        sys.exit("Provide --comments with --revise")
    revise_path = Path(revise)
    if not revise_path.exists():
        sys.exit(f"Existing document not found: {revise_path}")
    return revise_path.read_text()


def resolve_out_dir(listing: dict, out_dir_arg: str | None) -> Path:
    """Default: .tmp/applications/{Company}_{Role}_{today}. Created if missing."""
    if out_dir_arg:
        out_dir = Path(out_dir_arg)
    else:
        company = sanitize_path_component(listing.get("company", "Unknown"))
        role = sanitize_path_component(listing.get("job_title", "Role"))
        out_dir = Path(".tmp/applications") / f"{company}_{role}_{date.today().isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir
