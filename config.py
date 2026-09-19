# Tunable settings for fetch_internships.py. This is the file to edit
# when you want to change keywords, filters, sheet columns, or the source list.

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
    "software engineering", "software engineer",
    "software development",  "software development engineer",
    "backend", "full stack", "frontend",
    "robot", "robotics", "manipulation", "autonom", "embodied",
    "machine learning", " ml ", "ml intern", "artificial intelligence",
    " ai ", "ai/ml", "deep learning", "reinforcement learning",
    "computer vision", "nlp", "natural language", "perception",
    "self-driving", "autonomous vehicle", "vla", "llm",
    "large language model", "distributed systems", "cuda", "gpu inference",
]

# Drop roles that look PhD-only. Titles that also mention MS / Master's
# (e.g. "Software Engineer Intern - MS/PhD") are kept.
EXCLUDE_PHD_ONLY = True

# Drop roles whose title contains any of these (case-insensitive).
# "embedded" covers embedded system / software / engineer / firmware.
EXCLUDE_ROLE_KEYWORDS = [
    "embedded",
    "firmware",
    "hardware",
]

# Drop co-op / coop titles, including "Intern/Co-op". Matched as a whole
# term on the role only, so company names like PricewaterhouseCoopers stay.
EXCLUDE_COOP = True

# Drop postings tagged 🇺🇸 in the README ("Requires U.S. Citizenship").
# Continuation rows (↳) inherit the flag from the company row above.
EXCLUDE_US_CITIZEN = True

# Only keep postings at most this many days old (based on the README's "Age"
# column: "0d", "3d", "1mo", ...). Set to None to disable age filtering.
# Keep this reasonably small once the sheet is populated -- it just limits
# how far back a fresh run looks, not how often the script runs.
MAX_AGE_DAYS = 13

# Column layout written to the sheet. If you already have a header row with
# different column names, either rename your header row to match this, or
# edit this list to match your header row.
SHEET_HEADERS = [
    "Company", "Role / Title", "Date Applied", "Status", "Job ID",
    "Link", "OA", "Interview Stage", "Referral", "Location", "Notes",
    "Date Posted",
]

DEFAULT_STATUS = "\u5f85\u6295\u9012"  # "To apply" -- change to English if you prefer

FIRE_EMOJI = "\U0001F525"            # 🔥 FAANG+
US_CITIZEN_EMOJI = "\U0001F1FA\U0001F1F8"  # 🇺🇸 Requires U.S. Citizenship
SAME_COMPANY_MARK = "\u21b3"         # ↳
