"""Step 4: load the filings into Datasphere. Run after pushing the repo to GitHub (it must be public)."""
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()
from companies import COMPANIES, filing_path  # noqa: E402
from retrieval import client  # noqa: E402

repo = os.environ.get("GITHUB_REPO")
if not repo:
    sys.exit("Set GITHUB_REPO in .env")

for tag in COMPANIES:
    url = f"https://raw.githubusercontent.com/{repo}/main/{filing_path(tag)}"
    doc = client().datasphere.documents.create({"url": url, "tags": [tag]})
    print(f"{tag}: uploading {url}")
    for _ in range(120):
        info = client().datasphere.documents.get(doc["id"])
        if info.get("status") == "completed":
            print(f"  ready, {info.get('number_of_chunks', '?')} chunks")
            break
        if info.get("status") in ("error", "failed"):
            sys.exit(f"  failed. Is the repo public and the file pushed? {info}")
        time.sleep(5)
    else:
        sys.exit("  timed out waiting for Datasphere")
