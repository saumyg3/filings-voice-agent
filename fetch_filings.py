"""Step 1: download each company's 10-K from SEC EDGAR and save it as plain text in filings/."""
import html
import pathlib
import re
import sys

import requests

from companies import COMPANIES, filing_path

# SEC requires a User-Agent with a contact email.
HEADERS = {"User-Agent": "Saumya Goyal saumyg3@uci.edu"}


def find_10k(cik, period):
    url = f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
    recent = requests.get(url, headers=HEADERS, timeout=30).json()["filings"]["recent"]
    for form, acc, doc, rep in zip(recent["form"], recent["accessionNumber"], recent["primaryDocument"], recent["reportDate"]):
        if form == "10-K" and rep == period:
            return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}"
    sys.exit(f"No 10-K found for CIK {cik} period {period}")


def html_to_text(raw):
    raw = re.sub(r"(?is)<(script|style|ix:header).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)</(p|div|tr|li|h\d)>|<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?i)</t[dh]>", " | ", raw)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw)).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"(\s*\|\s*)+\n", "\n", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


for tag, c in COMPANIES.items():
    url = find_10k(c["cik"], c["period"])
    print(f"{c['name']}: {url}")
    text = html_to_text(requests.get(url, headers=HEADERS, timeout=60).text)
    out = pathlib.Path(filing_path(tag))
    out.write_text(f"{c['name']} {c['label']}\n\n{text}", encoding="utf-8")
    print(f"  saved {out} ({len(text) // 1000} KB)")
