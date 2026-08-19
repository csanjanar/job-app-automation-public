"""Shared Google Sheets access + schema-driven header resolution.

All sheet tools import from here so that:
  - OAuth (incl. expired-token browser re-auth fallback) lives in one place
  - columns are resolved BY HEADER NAME against the live row 1, validated
    against schema/sheets.yaml — never by hardcoded letters
  - write protection (formula columns, unknown user columns) is enforced
    uniformly

Header matching is insensitive to case, surrounding whitespace, punctuation
runs, and trailing ": description" suffixes, so "Input URL " in the sheet
matches "Input URL" in the schema.
"""
import os
import re
import sys
import yaml
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = "token.json"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "sheets.yaml"

# Google Sheets caps a cell at 50,000 chars; leave headroom
MAX_CELL_CHARS = 49_500


def get_sheets_service():
    creds = None
    if Path(TOKEN_PATH).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:  # revoked/expired refresh token → full re-auth
                print(f"Token refresh failed ({e}); starting browser re-auth...", file=sys.stderr)
                creds = None
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(TOKEN_PATH).write_text(creds.to_json())
    return build("sheets", "v4", credentials=creds)


def sheet_id() -> str:
    return os.environ["GOOGLE_SHEET_ID"]


@lru_cache(maxsize=1)
def load_schema() -> dict:
    return yaml.safe_load(SCHEMA_PATH.read_text())


def norm_header(h: str) -> str:
    """Canonical form for header matching: strip ': desc' suffix, lowercase,
    collapse punctuation/whitespace runs to single spaces."""
    h = str(h).split(":")[0]
    return re.sub(r"[^a-z0-9]+", " ", h.lower()).strip()


def snake_header(h: str) -> str:
    """Row-dict key form used by read_from_sheet (e.g. 'Docs (Link)' → docs_link)."""
    return norm_header(h).replace(" ", "_")


def col_to_letter(idx: int) -> str:
    """0-based column index → A1 letter(s)."""
    letters = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(ord("A") + rem) + letters
    return letters


def truncate_cell(value):
    if isinstance(value, str) and len(value) > MAX_CELL_CHARS:
        print(f"Warning: cell value truncated from {len(value)} to {MAX_CELL_CHARS} chars "
              f"(Sheets 50k/cell limit)", file=sys.stderr)
        return value[:MAX_CELL_CHARS]
    return value


class Tab:
    """A live tab bound to its schema entry, with header-name column resolution."""

    def __init__(self, service, tab_name: str, spreadsheet_id: str | None = None):
        schema = load_schema()
        if tab_name not in schema["tabs"]:
            sys.exit(f"Tab '{tab_name}' is not in schema/sheets.yaml "
                     f"(known: {', '.join(schema['tabs'])})")
        self.service = service
        self.name = tab_name
        self.sheet_id = spreadsheet_id or sheet_id()
        self.spec = schema["tabs"][tab_name]
        self.key_header = self.spec["key"]
        # schema lookup by normalized name
        self._schema_by_norm = {norm_header(h["name"]): h for h in self.spec["headers"]}
        # live row 1 → normalized name → 0-based index
        row1 = self.service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id, range=f"'{tab_name}'!1:1",
        ).execute().get("values", [[]])
        self.live_headers = row1[0] if row1 else []
        self._index_by_norm = {}
        for i, h in enumerate(self.live_headers):
            self._index_by_norm.setdefault(norm_header(h), i)

    # ── schema lookups ────────────────────────────────────────────────────
    def header_spec(self, header: str) -> dict | None:
        return self._schema_by_norm.get(norm_header(header))

    def kind(self, header: str) -> str | None:
        spec = self.header_spec(header)
        return spec["kind"] if spec else None

    # ── live-sheet lookups ────────────────────────────────────────────────
    def col_index(self, header: str) -> int:
        """0-based index of a header in the live sheet; exits if absent."""
        idx = self._index_by_norm.get(norm_header(header))
        if idx is None:
            sys.exit(f"Column '{header}' not found in '{self.name}' row 1 — "
                     f"run: python3 tools/check_schema.py --fix")
        return idx

    def col_letter(self, header: str) -> str:
        return col_to_letter(self.col_index(header))

    def assert_writable(self, header: str):
        spec = self.header_spec(header)
        if spec is None:
            sys.exit(f"Refusing to write '{header}' on '{self.name}' — not in "
                     f"schema/sheets.yaml (user-owned columns are never touched by tools; "
                     f"add it to the schema if tools should manage it)")
        if spec["kind"] == "formula":
            sys.exit(f"Refusing to write '{header}' on '{self.name}' — formula column")

    # ── row operations (all header-keyed) ─────────────────────────────────
    def key_column_values(self) -> list[str]:
        """Values of the key column from row 2 down (may include blanks)."""
        letter = self.col_letter(self.key_header)
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id, range=f"'{self.name}'!{letter}2:{letter}",
        ).execute()
        return [(r[0] if r else "") for r in result.get("values", [])]

    def find_row(self, key_value: str) -> int | None:
        """1-based row number of the first data row whose key column matches."""
        for i, v in enumerate(self.key_column_values()):
            if v.strip().lower() == key_value.strip().lower():
                return i + 2
        return None

    def next_free_row(self) -> int:
        return len(self.key_column_values()) + 2

    def write_cells(self, row_num: int, cells: dict[str, str], raw: bool = False):
        """Write {header: value} on one row via a single batchUpdate.
        Respects per-header schema `raw: true` overrides."""
        default_data, raw_data = [], []
        for header, value in cells.items():
            self.assert_writable(header)
            spec = self.header_spec(header)
            entry = {
                "range": f"'{self.name}'!{self.col_letter(header)}{row_num}",
                "values": [[truncate_cell(value)]],
            }
            (raw_data if (raw or spec.get("raw")) else default_data).append(entry)
        for input_option, data in (("USER_ENTERED", default_data), ("RAW", raw_data)):
            if data:
                self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body={"valueInputOption": input_option, "data": data},
                ).execute()

    def append_row(self, cells: dict[str, str], raw: bool = False) -> int:
        """Append {header: value} at the first free row (by key column). Writing
        explicit cells (not values().append) keeps ARRAYFORMULA columns from
        pushing appends to the sheet bottom and is order-independent."""
        row_num = self.next_free_row()
        self.write_cells(row_num, cells, raw=raw)
        return row_num

    def read_rows(self, iso_dates: bool = False) -> list[dict]:
        """All data rows as dicts keyed by snake_header of the live headers.

        iso_dates=True re-reads schema `date: true` columns unformatted and
        replaces their display strings with unambiguous ISO YYYY-MM-DD — use
        this whenever a date value will be written to another tab (formatted
        strings like '26-06-26' are locale-ambiguous and may land as text)."""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id, range=f"'{self.name}'",
        ).execute()
        rows = result.get("values", [])
        if not rows:
            return []
        keys = [snake_header(h) for h in rows[0]]
        dicts = [dict(zip(keys, row)) for row in rows[1:]]
        if iso_dates:
            raw = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id, range=f"'{self.name}'",
                valueRenderOption="UNFORMATTED_VALUE",
            ).execute().get("values", [])
            date_keys = {snake_header(h["name"]) for h in self.spec["headers"] if h.get("date")}
            for i, d in enumerate(dicts):
                for j, key in enumerate(keys):
                    if key in date_keys and i + 1 < len(raw) and j < len(raw[i + 1]):
                        v = raw[i + 1][j]
                        if isinstance(v, (int, float)):  # Sheets date serial (epoch 1899-12-30)
                            from datetime import datetime, timedelta
                            d[key] = (datetime(1899, 12, 30) + timedelta(days=v)).strftime("%Y-%m-%d")
        return dicts


def classification_lines(vocab_name: str) -> str:
    """Render a classification vocabulary from the schema as a quoted,
    comma-separated list for extraction prompts."""
    entries = load_schema()["classification"][vocab_name]
    parts = []
    for e in entries:
        if isinstance(e, dict):
            parts.append(f'"{e["name"]}" ({e["desc"]})')
        else:
            parts.append(f'"{e}"')
    return ", ".join(parts)
