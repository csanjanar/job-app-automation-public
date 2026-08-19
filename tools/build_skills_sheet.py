#!/usr/bin/env python3
"""Build (or refresh) two skills analysis tabs from Curated Listings.

Tabs created/overwritten:
  - Skills Raw    : long-format table — one row per (skill, listing)
  - Skills Freq   : deduplicated frequency table — one row per unique skill,
                    with a "My Proficiency" column cross-referencing career_profile.md
                    and an "Avg Interest Rating" column joined in from Raw
                    Listings' "Interest Rating" (by URL)

Curated Listings and Raw Listings columns are resolved by header name via
tools/sheets_common.py (schema/sheets.yaml is the source of truth) — no
positional assumptions.

Run:
  python tools/build_skills_sheet.py
"""
import os
import re
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from sheets_common import get_sheets_service, Tab

load_dotenv()

PROFILE_PATH = "profile/career_profile.md"


# ── Proficiency matching ──────────────────────────────────────────────────────

def normalise(skill: str) -> str:
    """Lowercase + collapse whitespace. Keeps punctuation (so 'c++' ≠ 'c')."""
    return re.sub(r"\s+", " ", skill.lower().strip())


def parse_profile_skill_map(profile_path: str) -> dict[str, str]:
    """
    Parse career_profile.md YAML front matter and return a flat dict:
        normalised_term → proficiency_label

    Proficiency labels: Expert / Working / Familiar / Learning

    Covers both exact YAML key names (normalised) and a comprehensive
    alias table for terms that appear differently in job listings.
    """
    from profile_common import load_frontmatter
    data = load_frontmatter(Path(profile_path))
    if not data:
        return {}

    skill_map: dict[str, str] = {}

    def _add(name: str, proficiency: str):
        key = normalise(name)
        if key and key not in skill_map:
            skill_map[key] = proficiency

    # Register every skill from the YAML skills block
    for category, items in (data.get('skills') or {}).items():
        if category == 'currently_learning':
            for item in (items or []):
                if item:
                    _add(str(item).strip(), 'Learning')
        elif isinstance(items, dict):
            for yaml_key, proficiency in items.items():
                # e.g. "TensorFlow_Keras" → "TensorFlow Keras"
                readable = yaml_key.replace('_', ' ')
                _add(readable, str(proficiency))

    # Convenience closure — look up proficiency of a profile term
    def _prof(profile_readable: str) -> str:
        return skill_map.get(normalise(profile_readable), '')

    # ── Listing-term aliases ──────────────────────────────────────────────────
    # Maps how a term commonly appears in job listings → its proficiency from
    # the profile (via the normalised profile key looked up above).
    # Entries are only added if they are not already in skill_map.
    ALIASES: list[tuple[str, str]] = [
        # ── Languages ────────────────────────────────────────────────────────
        ("C++",                             _prof("C Plus Plus")),
        ("C#",                              _prof("CSharp")),
        ("Node.js",                         _prof("NodeJS Express")),
        ("NodeJS",                          _prof("NodeJS Express")),
        ("Express",                         _prof("NodeJS Express")),
        ("Express.js",                      _prof("NodeJS Express")),
        ("NoSQL",                           _prof("NoSQL MongoDB")),
        ("Relational databases",            _prof("MySQL")),
        ("RDBMS",                           _prof("RDBMS NoSQL Design")),
        ("Database management",             _prof("RDBMS NoSQL Design")),
        ("Schema design",                   _prof("Schema Normalization")),
        ("Query optimization",              _prof("Schema Normalization")),
        ("REST API",                        _prof("RESTful APIs")),
        ("REST APIs",                       _prof("RESTful APIs")),
        ("RESTful API",                     _prof("RESTful APIs")),
        ("Firebase",                        _prof("Google Firebase")),
        # ── ML & AI ──────────────────────────────────────────────────────────
        ("TensorFlow",                      _prof("TensorFlow Keras")),
        ("Keras",                           _prof("TensorFlow Keras")),
        ("scikit-learn",                    _prof("Scikit Learn")),
        ("sklearn",                         _prof("Scikit Learn")),
        ("Deep Learning",                   _prof("CNNs")),
        ("Deep Learning Architectures",     _prof("CNNs")),
        ("CNN",                             _prof("CNNs")),
        ("Computer Vision",                 _prof("OpenCV")),
        ("Data Augmentation",               _prof("Image Augmentation")),
        ("Object detection",                _prof("Object Detection")),
        ("Decision Trees",                  _prof("Classification Models Algorithms")),
        ("Decision Tree",                   _prof("Classification Models Algorithms")),
        ("Random Forest",                   _prof("Classification Models Algorithms")),
        ("AdaBoost",                        _prof("Classification Models Algorithms")),
        ("Ensemble Learning",               _prof("Classification Models Algorithms")),
        ("kNN",                             _prof("Classification Models Algorithms")),
        ("Hyperparameter Tuning",           _prof("Model Optimization")),
        ("Batch Normalization",             _prof("Model Optimization")),
        ("Reinforcement Learning",          _prof("Reinforcement Learning")),
        ("RL",                              _prof("Reinforcement Learning")),
        ("Q-Learning",                      _prof("Reinforcement Learning")),
        ("DQN",                             _prof("Reinforcement Learning")),
        ("Genetic Algorithm",               _prof("Genetic Algorithms Evolutionary")),
        ("Evolutionary Algorithm",          _prof("Genetic Algorithms Evolutionary")),
        ("Transfer Learning",               _prof("Transfer Learning")),
        # ── NLP ──────────────────────────────────────────────────────────────
        ("Natural Language Processing",     _prof("NLTK")),
        ("NLP",                             _prof("NLTK")),
        ("Tokenization",                    _prof("NLTK")),
        ("Lemmatization",                   _prof("NLTK")),
        ("TF-IDF",                          _prof("TF IDF")),
        ("TF IDF",                          _prof("TF IDF")),
        ("Sentiment Analysis",              _prof("Text Classification")),
        ("Named Entity Recognition",        _prof("NER")),
        ("Entity-Relation Extraction",      _prof("NER")),
        ("Information Retrieval",           _prof("TF IDF")),
        # ── Generative AI & LLMs ─────────────────────────────────────────────
        ("GPT-2",                           _prof("GPT2 Finetuning")),
        ("GPT2",                            _prof("GPT2 Finetuning")),
        ("Generative AI",                   _prof("GPT2 Finetuning")),
        ("LLM",                             _prof("LLM RAG")),
        ("LLMs",                            _prof("LLM RAG")),
        ("Large Language Models",           _prof("LLM RAG")),
        ("Large Language Model",            _prof("LLM RAG")),
        ("Large Language Models (LLMs)",    _prof("LLM RAG")),
        ("RAG",                             _prof("LLM RAG")),
        ("Retrieval-Augmented Generation",  _prof("LLM RAG")),
        ("Retrieval Augmented Generation",  _prof("LLM RAG")),
        ("Transformer",                     _prof("Transformers")),
        ("Hugging Face",                    _prof("Transformers")),
        ("HuggingFace",                     _prof("Transformers")),
        ("CLIP",                            _prof("Vision Language Models")),
        ("VLM",                             _prof("Vision Language Models")),
        ("VLMs",                            _prof("Vision Language Models")),
        ("Vision Language Model",           _prof("Vision Language Models")),
        ("GPT-4o",                          _prof("Vision Language Models")),
        ("AI Agents",                       _prof("Agentic AI MultiAgent")),
        ("Agentic AI",                      _prof("Agentic AI MultiAgent")),
        ("Multi-Agent",                     _prof("Agentic AI MultiAgent")),
        ("Multi Agent",                     _prof("Agentic AI MultiAgent")),
        ("Multi-Agent Systems",             _prof("Agentic AI MultiAgent")),
        ("Agentic frameworks",              _prof("Agentic AI MultiAgent")),
        ("Tool-use agents",                 _prof("Agentic AI MultiAgent")),
        ("Workflow-aware AI systems",       _prof("Agentic AI MultiAgent")),
        ("Prompt engineering",              _prof("LLM RAG")),  # used LLMs with prompting
        ("Prompt Engineering",              _prof("LLM RAG")),
        # ── Data Science ─────────────────────────────────────────────────────
        ("Matplotlib",                      _prof("Matplotlib Seaborn")),
        ("Seaborn",                         _prof("Matplotlib Seaborn")),
        ("Data Visualization",              _prof("Matplotlib Seaborn")),
        ("Data Visualisation",              _prof("Matplotlib Seaborn")),
        ("Exploratory Data Analysis",       _prof("EDA")),
        ("Data Analysis",                   _prof("EDA")),
        ("Data Analytics",                  _prof("EDA")),
        ("Feature Extraction",              _prof("Feature Engineering")),
        ("Statistical Analysis",            _prof("Statistical Analysis")),
        ("Statistics",                      _prof("Statistical Analysis")),
        ("Statistical Modelling",           _prof("Statistical Analysis")),
        ("Statistical Modeling",            _prof("Statistical Analysis")),
        ("Experimental Design",             _prof("Statistical Analysis")),
        ("Hypothesis Testing",              _prof("Statistical Analysis")),
        ("PCA",                             _prof("Dimensionality Reduction")),
        ("Data Preprocessing",              _prof("Data Preprocessing")),
        ("Data Preparation",                _prof("Data Preprocessing")),
        ("Data Ingestion",                  _prof("Data Preprocessing")),
        ("Data Cleaning",                   _prof("Data Preprocessing")),
        # ── DevOps & Cloud ───────────────────────────────────────────────────
        ("Git",                             _prof("Git GitHub")),
        ("GitHub",                          _prof("Git GitHub")),
        ("Bash",                            _prof("Linux Bash")),
        ("Linux",                           _prof("Linux Bash")),
        ("Shell scripting",                 _prof("Linux Bash")),
        ("Linux/Bash CLI",                  _prof("Linux Bash")),
        ("Containerization",                _prof("Docker")),
        ("Container orchestration",         _prof("Docker")),  # stretch but related
        ("Google Cloud Platform",           _prof("GCP")),
        ("Google Cloud",                    _prof("GCP")),
        # ── Software Engineering ─────────────────────────────────────────────
        ("Agile",                           _prof("Agile Scrum")),
        ("Scrum",                           _prof("Agile Scrum")),
        ("Unit Testing",                    _prof("Unit Testing")),
        ("Test-Driven Development",         _prof("TDD")),
        ("Object-Oriented Programming",     _prof("OOP")),
        ("OOP",                             _prof("OOP")),
        ("Modular Architecture",            _prof("Modular Architecture")),
        ("Microservices",                   _prof("Modular Architecture")),  # adjacent
        ("UI/UX",                           _prof("UI UX Design")),
        ("User Interface",                  _prof("UI UX Design")),
        # ── PyTorch (Learning) ───────────────────────────────────────────────
        ("Torch",                           _prof("PyTorch")),
        # ── GIS ──────────────────────────────────────────────────────────────
        ("ArcGIS",                          _prof("ArcGIS Pro")),
        ("GIS",                             _prof("ArcGIS Pro")),
    ]

    for listing_term, proficiency in ALIASES:
        if proficiency:
            _add(listing_term, proficiency)

    return skill_map


def lookup_profile(skill: str, skill_map: dict[str, str]) -> str:
    """Return proficiency label if skill matches profile, else empty string."""
    return skill_map.get(normalise(skill), "")


# ── Google Sheets helpers ─────────────────────────────────────────────────────

def get_or_create_sheet(service, sheet_id: str, tab_name: str) -> int:
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    for sheet in meta["sheets"]:
        if sheet["properties"]["title"] == tab_name:
            return sheet["properties"]["sheetId"]
    resp = service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
    ).execute()
    return resp["replies"][0]["addSheet"]["properties"]["sheetId"]


def clear_tab(service, sheet_id: str, tab_name: str):
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id, range=f"'{tab_name}'"
    ).execute()


def write_rows(service, sheet_id: str, tab_name: str, rows: list[list]):
    if not rows:
        return
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'{tab_name}'!A1",
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()


def bold_header(service, sheet_id: str, tab_sheet_id: int, num_cols: int):
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{
            "repeatCell": {
                "range": {
                    "sheetId": tab_sheet_id,
                    "startRowIndex": 0, "endRowIndex": 1,
                    "startColumnIndex": 0, "endColumnIndex": num_cols,
                },
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }
        }]},
    ).execute()


def parse_skills(cell_value: str) -> list[str]:
    if not cell_value:
        return []
    return [s.strip() for s in cell_value.split(",") if s.strip()]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    service = get_sheets_service()
    sheet_id = os.environ["GOOGLE_SHEET_ID"]

    # Load profile skill map
    profile_map = parse_profile_skill_map(PROFILE_PATH)
    print(f"Loaded {len(profile_map)} profile skill entries (including aliases).")

    # ── Read Curated Listings (header-keyed) ─────────────────────────────────
    rows = Tab(service, "Curated Listings").read_rows()
    print(f"Read {len(rows)} data rows from Curated Listings.")

    # ── Read Raw Listings' Interest Rating, joined to Curated by URL ─────────
    raw_listings_rows = Tab(service, "Raw Listings").read_rows()
    interest_by_url: dict[str, int] = {}
    for r in raw_listings_rows:
        url = r.get("input_url", "")
        rating = (r.get("interest_rating") or "").strip()
        if url and rating.isdigit():
            interest_by_url[url] = int(rating)
    print(f"Interest ratings found for {len(interest_by_url)} / {len(raw_listings_rows)} Raw Listings rows.")

    # ── Build raw skill records ──────────────────────────────────────────────
    # (skill, category, job_title, company, role_family, ml_domain, work_mode, url)
    raw_records = []
    for row in rows:
        url         = row.get("url", "")
        title       = row.get("job_title", "")
        company     = row.get("company", "")
        role_family = row.get("role_family", "")
        ml_domain   = row.get("ml_domain", "")
        work_mode   = row.get("work_mode", "")
        for skill in parse_skills(row.get("key_tools_skills", "")):
            raw_records.append((skill, "Tool / Framework", title, company, role_family, ml_domain, work_mode, url))
        for skill in parse_skills(row.get("key_concepts_practices", "")):
            raw_records.append((skill, "Concept / Practice", title, company, role_family, ml_domain, work_mode, url))
        for skill in parse_skills(row.get("soft_skills_others", "")):
            raw_records.append((skill, "Soft Skill", title, company, role_family, ml_domain, work_mode, url))

    print(f"  {len(raw_records)} total skill–listing pairs extracted.")

    # ── Build frequency table ────────────────────────────────────────────────
    freq: dict[str, dict] = {}
    for (skill, category, title, company, role_family, ml_domain, work_mode, url) in raw_records:
        key = normalise(skill)
        if key not in freq:
            freq[key] = {
                "canonical": skill,
                "category": category,
                "count": 0,
                "role_families": set(),
                "ml_domains": set(),
                "work_modes": set(),
                "titles": [],
                "ratings": [],
            }
        freq[key]["count"] += 1
        if role_family:
            freq[key]["role_families"].add(role_family)
        if ml_domain:
            freq[key]["ml_domains"].add(ml_domain)
        if work_mode:
            freq[key]["work_modes"].add(work_mode)
        freq[key]["titles"].append(title)
        if url in interest_by_url:
            freq[key]["ratings"].append(interest_by_url[url])

    category_order = {"Tool / Framework": 0, "Concept / Practice": 1, "Soft Skill": 2}
    sorted_freq = sorted(
        freq.values(),
        key=lambda x: (-x["count"], category_order.get(x["category"], 9), x["canonical"].lower()),
    )

    # ── Write Skills Raw tab ─────────────────────────────────────────────────
    tab_raw = "Skills Raw"
    sid_raw = get_or_create_sheet(service, sheet_id, tab_raw)
    clear_tab(service, sheet_id, tab_raw)
    raw_header = [
        "Skill / Term", "Category",
        "Job Title", "Company", "Role Family", "ML Domain", "Work Mode",
        "Source URL",
    ]
    raw_data = [raw_header] + [list(r) for r in raw_records]
    write_rows(service, sheet_id, tab_raw, raw_data)
    bold_header(service, sheet_id, sid_raw, len(raw_header))
    print(f"  Written {len(raw_data)-1} rows to '{tab_raw}'.")

    # ── Write Skills Freq tab ────────────────────────────────────────────────
    tab_freq = "Skills Freq"
    sid_freq = get_or_create_sheet(service, sheet_id, tab_freq)

    # Carry Review Notes forward across the wholesale rebuild (keyed by
    # normalised skill term) — clear_tab() below wipes them otherwise. Blank
    # on the first run after this column was introduced (no header yet).
    prior = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"'{tab_freq}'",
    ).execute().get("values", [])
    review_notes: dict[str, str] = {}
    if prior:
        prior_headers = [normalise(h) for h in prior[0]]
        if "review notes" in prior_headers:
            note_idx = prior_headers.index("review notes")
            for row in prior[1:]:
                if row and (note := (row[note_idx] if note_idx < len(row) else "")):
                    review_notes[normalise(row[0])] = note

    clear_tab(service, sheet_id, tab_freq)

    # Tally profile matches for summary
    matched = sum(1 for e in sorted_freq if lookup_profile(e["canonical"], profile_map))

    freq_header = [
        "Skill / Term", "Category", "My Proficiency", "Frequency", "Avg Interest Rating",
        "Role Families", "ML Domains", "Work Modes",
        "Appears In (Job Titles)", "Review Notes",
    ]
    freq_rows = [freq_header]
    for entry in sorted_freq:
        ratings = entry["ratings"]
        avg_interest = round(sum(ratings) / len(ratings), 1) if ratings else ""
        freq_rows.append([
            entry["canonical"],
            entry["category"],
            lookup_profile(entry["canonical"], profile_map),
            entry["count"],
            avg_interest,
            ", ".join(sorted(entry["role_families"])),
            ", ".join(sorted(entry["ml_domains"])),
            ", ".join(sorted(entry["work_modes"])),
            ", ".join(entry["titles"]),
            review_notes.get(normalise(entry["canonical"]), ""),
        ])
    write_rows(service, sheet_id, tab_freq, freq_rows)
    bold_header(service, sheet_id, sid_freq, len(freq_header))
    print(f"  Written {len(freq_rows)-1} unique skills to '{tab_freq}'"
          f"{f' ({len(review_notes)} Review Note(s) carried forward)' if review_notes else ''}.")
    print(f"  Profile matches: {matched} / {len(sorted_freq)} unique skills "
          f"({matched*100//len(sorted_freq) if sorted_freq else 0}% covered).")

    print("\nDone. Refresh your Google Sheet to see the updated tabs.")


if __name__ == "__main__":
    main()
