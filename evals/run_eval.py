"""Step 7: retrieval eval. For each question, does Datasphere return a passage that contains the answer?
Reports hit@1 / hit@3 overall and by question type, and shows what came back for every miss."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
import retrieval  # noqa: E402

K = 3
questions = json.loads((ROOT / "evals/questions.json").read_text())


def norm(s):
    return s.lower().replace(",", "").replace("$", "")


results = []
for q in questions:
    chunks = retrieval.search(q["question"], q["company"], count=K)
    rank = next((i + 1 for i, c in enumerate(chunks) if all(norm(e) in norm(c["text"]) for e in q["expected"])), None)
    results.append({**q, "rank": rank, "top_chunk": chunks[0]["text"][:400] if chunks else ""})
    print(f"{'HIT ' if rank else 'MISS'} @{rank or '-'}  {q['id']}  {q['question']}")

lines = ["| Question type | n | hit@1 | hit@3 |", "|---|---|---|---|"]
for t in sorted({r["type"] for r in results}) + ["all"]:
    sub = results if t == "all" else [r for r in results if r["type"] == t]
    h1 = sum(r["rank"] == 1 for r in sub) / len(sub)
    hk = sum(r["rank"] is not None for r in sub) / len(sub)
    lines.append(f"| {'**all**' if t == 'all' else t} | {len(sub)} | {h1:.0%} | {hk:.0%} |")
table = "\n".join(lines)
print("\n" + table)

(ROOT / "evals/results.json").write_text(json.dumps(results, indent=2))
(ROOT / "evals/results_table.md").write_text(table + "\n")
print("\nMisses (what came back instead):")
for r in results:
    if not r["rank"]:
        print(f"\n- {r['id']} expected {r['expected']}\n  got: {r['top_chunk'][:250]!r}")
