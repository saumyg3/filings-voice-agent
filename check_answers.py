"""Step 2: make sure every expected answer in evals/questions.json actually appears in the filing.
If one doesn't, the question is wrong (not the agent), so fix or drop it before running the eval."""
import json
import pathlib

from companies import filing_path


def norm(s):
    return s.lower().replace(",", "").replace("$", "")


questions = json.loads(pathlib.Path("evals/questions.json").read_text())
texts = {}
bad = 0
for q in questions:
    tag = q["company"]
    texts.setdefault(tag, norm(pathlib.Path(filing_path(tag)).read_text(encoding="utf-8")))
    missing = [e for e in q["expected"] if norm(e) not in texts[tag]]
    if missing:
        bad += 1
        print(f"FIX  {q['id']}: {missing} not found in filing")
print(f"\n{len(questions) - bad}/{len(questions)} questions verified against the filings")
