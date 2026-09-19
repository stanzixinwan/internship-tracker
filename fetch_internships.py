#!/usr/bin/env python3
"""
Daily scan of SimplifyJobs/Summer2027-Internships for postings that match a
configurable set of keywords, with new matches appended to a Google Sheet.

Required environment variables (set as GitHub Actions secrets):
  GOOGLE_SERVICE_ACCOUNT_JSON  - full contents of your service account key file (JSON)
  SHEET_ID                     - the Google Sheet's ID (the long id in its URL)

Optional environment variables:
  SHEET_TAB                    - worksheet/tab name to write into (default: "Sheet1")

Run locally for testing:
  pip install -r requirements.txt
  export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service-account.json)"
  export SHEET_ID="your-sheet-id"
  python fetch_internships.py
"""

import os
import sys
import json
import datetime
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# 1. CONFIGURATION -- this is the section you'll want to tune over time
# ---------------------------------------------------------------------------

# "dev" is this repo's default branch (check github.com/SimplifyJobs/Summer2027-Internships
# if that ever changes). Swap the repo name for Summer2026-Internships, New-Grad-Positions,
# etc. to track a different list with the same script.
REPO_README_URL = (
    "https://raw.githubusercontent.com/SimplifyJobs/"
    "Summer2027-Internships/dev/README.md"
)

# Section headers as they appear verbatim in the README. If SimplifyJobs
# renames a section, update the string on the right to match.
SECTION_HEADERS = [
    ("Software Engineering", "## \U0001F4BB Software Engineering Internship Roles"),
    ("Product Management", "## \U0001F4F1 Product Management Internship Roles"),
    ("Data Science, AI & ML", "## \U0001F916 Data Science, AI & Machine Learning Internship Roles"),
    ("Quant Finance", "## \U0001F4C8 Quantitative Finance Internship Roles"),
    ("Hardware Engineering", "## \U0001F527 Hardware Engineering Internship Roles"),
]

# Keywords matched case-insensitively against "Company + Role" text.
# This is the main dial for how broad/narrow your matches are.
KEYWORDS = [
    "robot", "robotics", "manipulation", "autonom", "embodied",
    "machine learning", " ml ", "ml intern", "artificial intelligence",
    " ai ", "ai/ml", "deep learning", "reinforcement learning",
    "computer vision", "nlp", "natural language", "perception",
    "self-driving", "autonomous vehicle", "vla", "llm",
    "large language model", "distributed systems", "cuda", "gpu inference",
]

# Only keep postings at most this many days old (based on the README's "Age"
# column: "0d", "3d", "1mo", ...). Set to None to disable age filtering.
# Keep this reasonably small once the sheet is populated -- it just limits
# how far back a fresh run looks, not how often the script runs.
MAX_AGE_DAYS = 14

# Column layout written to the sheet. If you already have a header row with
# different column names, either rename your header row to match this, or
# edit this list to match your header row.
SHEET_HEADERS = [
    "Company", "Role / Title", "Date Applied", "Status", "Job ID",
    "Link", "OA", "Interview Stage", "Referral", "Location", "Notes",
]

DEFAULT_STATUS = "\u5f85\u6295\u9012"  # "To apply" -- change to English if you prefer

# ---------------------------------------------------------------------------
# 2. FETCH + PARSE
# ---------------------------------------------------------------------------

def fetch_readme() -> str:
    resp = requests.get(REPO_README_URL, timeout=30)
    resp.raise_for_status()
    return resp.text


def split_sections(content: str) -> dict:
    idxs = [(name, content.find(marker)) for name, marker in SECTION_HEADERS]
    idxs.append(("__END__", len(content)))
    sections = {}
    for i in range(len(idxs) - 1):
        name, start = idxs[i]
        _, end = idxs[i + 1]
        if start == -1:
            continue  # section not found -- README structure may have changed
        sections[name] = content[start:end]
    return sections


def parse_age_to_days(age_text: str):
    age_text = age_text.strip().lower()
    try:
        if age_text.endswith("mo"):
            return int(age_text[:-2]) * 30
        if age_text.endswith("y"):
            return int(age_text[:-1]) * 365
        if age_text.endswith("d"):
            return int(age_text[:-1])
    except ValueError:
        return None
    return None


def extract_rows(sections: dict) -> list:
    results = []
    for section_name, html in sections.items():
        soup = BeautifulSoup(html, "html.parser")
        last_company = None
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 5:
                continue
            company_cell, role_cell, loc_cell, app_cell, age_cell = cells[:5]

            company_text = company_cell.get_text(strip=True)
            if company_text in ("", "\u21b3"):  # "\u21b3" = "↳" (same company as row above)
                company = last_company
            else:
                company = company_text.replace("\U0001F525", "").strip()  # strip fire emoji
                last_company = company

            role = role_cell.get_text(strip=True)
            location = loc_cell.get_text(strip=True)
            age = age_cell.get_text(strip=True)
            link_tag = app_cell.find("a")
            link = link_tag["href"] if link_tag else ""

            if not company or not role:
                continue

            combined = f"{company} {role}".lower()
            if not any(kw in combined for kw in KEYWORDS):
                continue

            age_days = parse_age_to_days(age)
            if MAX_AGE_DAYS is not None and age_days is not None and age_days > MAX_AGE_DAYS:
                continue

            results.append({
                "company": company,
                "role": role,
                "location": location,
                "category": section_name,
                "age": age,
                "link": link,
            })
    return results


# ---------------------------------------------------------------------------
# 3. GOOGLE SHEETS
# ---------------------------------------------------------------------------

def get_sheets_service():
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        sys.exit("Missing GOOGLE_SERVICE_ACCOUNT_JSON environment variable.")

    info = json.loads(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def ensure_header(service, sheet_id: str, tab: str):
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"{tab}!A1:Z1"
    ).execute()
    if not result.get("values"):
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{tab}!A1",
            valueInputOption="RAW",
            body={"values": [SHEET_HEADERS]},
        ).execute()


def get_existing_links(service, sheet_id: str, tab: str) -> set:
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=f"{tab}!A:Z"
        ).execute()
    except Exception as e:
        print(f"Warning: could not read existing sheet data ({e}); assuming empty.")
        return set()

    values = result.get("values", [])
    if not values:
        return set()

    header = values[0]
    link_col = header.index("Link") if "Link" in header else len(header) - 1

    existing = set()
    for row in values[1:]:
        if len(row) > link_col:
            existing.add(row[link_col])
    return existing


def append_rows(service, sheet_id: str, tab: str, rows: list):
    if not rows:
        return
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{tab}!A:A",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


# ---------------------------------------------------------------------------
# 4. MAIN
# ---------------------------------------------------------------------------

def main():
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id:
        sys.exit("Missing SHEET_ID environment variable.")
    tab = os.environ.get("SHEET_TAB", "Sheet1")

    print("Fetching README...")
    content = fetch_readme()

    print("Parsing sections...")
    sections = split_sections(content)
    if not sections:
        sys.exit("Could not find any known sections -- the README format may have changed.")

    print("Extracting matching postings...")
    postings = extract_rows(sections)
    print(f"Found {len(postings)} postings matching the keyword/age filter.")

    service = get_sheets_service()
    ensure_header(service, sheet_id, tab)
    existing_links = get_existing_links(service, sheet_id, tab)

    today = datetime.date.today().isoformat()
    new_rows = []
    for p in postings:
        if p["link"] in existing_links:
            continue
        new_rows.append([
            p["company"],       # Company
            p["role"],          # Role / Title
            today,              # Date Applied
            DEFAULT_STATUS,     # Status
            "",                 # Job ID (not available from the README -- fill in manually)
            p["link"],          # Link
            "",                 # OA
            "",                 # Interview Stage
            "",                 # Referral
            p["location"],      # Location
            p["category"],      # Notes (section the posting was matched under)
        ])

    skipped = len(postings) - len(new_rows)
    print(f"{len(new_rows)} new posting(s) to add (skipped {skipped} already tracked).")
    append_rows(service, sheet_id, tab, new_rows)
    print("Done.")


if __name__ == "__main__":
    main()
