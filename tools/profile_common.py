"""Shared loader for profile/career_profile.md's YAML front matter.

Used by build_skills_sheet.py (proficiency registry), search_mcf.py
(search_targeting), and extract_fields.py (fit-scoring preference block).
"""
import re
import sys
import yaml
from pathlib import Path

PROFILE_PATH = Path("profile/career_profile.md")

# Front-matter keys that express job preferences — the fit-scoring context
FIT_PREFERENCE_KEYS = ["search_filters", "domain_preferences",
                       "industry_preferences", "company_preferences"]


def load_frontmatter(path: Path = PROFILE_PATH) -> dict:
    text = Path(path).read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        print(f"  ⚠ Could not find YAML front matter in {path}", file=sys.stderr)
        return {}
    # Strip pure comment lines so PyYAML doesn't choke on markdown fragments
    yaml_clean = "\n".join(line for line in match.group(1).split("\n")
                           if not line.lstrip().startswith("#"))
    try:
        return yaml.safe_load(yaml_clean) or {}
    except yaml.YAMLError as e:
        print(f"  ⚠ YAML parse error in {path}: {e}", file=sys.stderr)
        return {}


def fit_preference_block(path: Path = PROFILE_PATH) -> str:
    """Condensed preference sections, rendered as YAML for the fit-scoring
    prompt. Keeps the profile the single source of truth for what 'fit' means."""
    data = load_frontmatter(path)
    subset = {k: data[k] for k in FIT_PREFERENCE_KEYS if k in data}
    return yaml.safe_dump(subset, sort_keys=False, allow_unicode=True, width=100)
