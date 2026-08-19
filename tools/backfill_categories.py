#!/usr/bin/env python3
"""One-off script to backfill Role Family, ML Domain, Work Mode, Industry Vertical,
and Employer Type (cols E–I) for existing rows in Curated Listings.

Run once after schema migration. Safe to re-run — overwrites same cells.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = "token.json"

# ── Manually determined categorical values for each existing listing ──────────
# Keys must exactly match the URL in col A of Curated Listings.
# Columns: Role Family | ML Domain | Work Mode | Industry Vertical | Employer Type
BACKFILL = {
    "https://www.mycareersfuture.gov.sg/job/information-technology/machine-learning-engineer-cantina-research-singapore-ce9a9d72eb2f8a7bd9bf8d5e2521981f": [
        "ML Engineer",
        "Multimodal",
        "Engineering",
        "Social / Media / Creative",
        "AI-First Startup",
    ],
    "https://www.mycareersfuture.gov.sg/job/information-technology/data-scientist-titansoft-f5043aa84fa1bdda20c13f6a0063b6a6": [
        "Data Scientist",
        "Classical ML / Analytics",
        "Analytics",
        "Gaming / Entertainment",
        "Established Tech",
    ],
    "https://www.mycareersfuture.gov.sg/job/information-technology/ai-engineer-go-genie-fded203f5c9f9193330e6f01e64a9402": [
        "AI Engineer",
        "Classical ML / Analytics",
        "Engineering",
        "Logistics / Ops",
        "AI-First Startup",
    ],
    "https://www.mycareersfuture.gov.sg/job/information-technology/ai-full-stack-engineer-l-12-month-contract-manpower-staffing-services-2c0113125e25edfd14342d97f977559e": [
        "Full-Stack AI Engineer",
        "NLP / LLM",
        "Engineering",
        "General Tech / SaaS",
        "Recruitment / Agency",
    ],
    "https://www.mycareersfuture.gov.sg/job/information-technology/data-scientist-digital-biz-solutions-86aaee2eaf7c03be5f3da53be6249d8a": [
        "Data Scientist",
        "Classical ML / Analytics",
        "Product",
        "General Tech / SaaS",
        "Consultancy",
    ],
    "https://www.mycareersfuture.gov.sg/job/information-technology/ai-engineer-fragment-works-d0bc882b9aec66b440b1c87971c04c86": [
        "AI Engineer",
        "Multimodal",
        "Engineering",
        "Social / Media / Creative",
        "AI-First Startup",
    ],
    "https://www.mycareersfuture.gov.sg/job/information-technology/associate-data-scientist-workato-5fee9b6964c98766d0c35de742af134b": [
        "Data Scientist",
        "NLP / LLM",
        "Product",
        "General Tech / SaaS",
        "Established Tech",
    ],
    "https://www.mycareersfuture.gov.sg/job/information-technology/ai-researcher-evolution-recruitment-solutions-dfbf87fb5e642bded031bfde8c9804dd": [
        "Research Scientist",
        "NLP / LLM",
        "Research",
        "General Tech / SaaS",
        "Recruitment / Agency",
    ],
    "https://careers.nus.edu.sg/job/Research-Analyst-Associate-Fellow-in-Machine-Learning-and-Artificial-Intelligence-%28MLAI%29/24252-en_GB": [
        "Research Analyst",
        "Classical ML / Analytics",
        "Research",
        "Research Institute / Lab",
        "Research Institute / Lab",
    ],
    "https://www.mycareersfuture.gov.sg/job/banking-finance/ai-engineer-helius-technologies-9592fa5cfc699aa1e81899b85a7e4945": [
        "AI Engineer",
        "",          # ML Domain unknown — no listing text scraped
        "",          # Work Mode unknown
        "FinTech",
        "Established Tech",
    ],
}


def get_sheets_service():
    creds = None
    if Path(TOKEN_PATH).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(TOKEN_PATH).write_text(creds.to_json())
    return build("sheets", "v4", credentials=creds)


def main():
    service = get_sheets_service()
    sheet_id = os.environ["GOOGLE_SHEET_ID"]
    tab = "Curated Listings"

    # Read all URLs from col A (skip header row 1)
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{tab}'!A2:A",
    ).execute()
    url_rows = result.get("values", [])

    updated = 0
    for i, row in enumerate(url_rows):
        if not row:
            continue
        url = row[0].strip()
        if url not in BACKFILL:
            print(f"  ⚠ No backfill entry for row {i+2}: {url[:80]}...")
            continue

        values = BACKFILL[url]
        row_num = i + 2  # 1-based, offset by header row
        range_name = f"'{tab}'!E{row_num}:I{row_num}"
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": [values]},
        ).execute()
        print(f"  ✓ Updated row {row_num}: {values[0]} / {values[1]} / {values[2]}")
        updated += 1

    print(f"\nDone — updated {updated} rows.")


if __name__ == "__main__":
    main()
