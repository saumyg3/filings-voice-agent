"""Load the filings into Datasphere. Run after pushing the repo to GitHub (it must be public).

Uploads two documents per company, both tagged with the company:
  - the 10-K text
  - the same 10-K's tables rewritten as sentences (from rewrite_tables.py)
Any existing documents with these tags are deleted first, so re-running is safe.
"""
import os
import pathlib
import sys
import time

from dotenv import load_dotenv

load_dotenv()
from companies import COMPANIES, filing_path, tables_path  # noqa: E402
from retrieval import client  # noqa: E402

repo = os.environ.get("GITHUB_REPO")
if not repo:
    sys.exit("Set GITHUB_REPO in .env")

docs = client().datasphere.documents

# clear old uploads for these companies
existing = docs.list().get("data", [])
for d in existing:
    if set(d.get("tags") or []) & set(COMPANIES):
        docs.delete(d["id"])
        print(f"deleted old document {d['id']} {d.get('tags')}")

for tag in COMPANIES:
    for path in (filing_path(tag), tables_path(tag)):
        if not pathlib.Path(path).exists():
            sys.exit(f"{path} missing. Run fetch_filings.py and rewrite_tables.py first.")
        url = f"https://raw.githubusercontent.com/{repo}/main/{path}"
        doc = docs.create({"url": url, "tags": [tag]})
        print(f"{tag}: uploading {path}")
        for _ in range(120):
            info = docs.get(doc["id"])
            if info.get("status") == "completed":
                print(f"  ready, {info.get('number_of_chunks', '?')} chunks")
                break
            if info.get("status") in ("error", "failed"):
                sys.exit(f"  failed. Is the repo public and the file pushed? {info}")
            time.sleep(5)
        else:
            sys.exit("  timed out waiting for Datasphere")
