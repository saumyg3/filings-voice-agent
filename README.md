# Filings Voice Agent

Call a phone number and ask about NVIDIA's or Apple's 10-K. The agent runs on SignalWire's
AI Agent runtime, searches the filings in Datasphere, and answers only from what it finds.
A retrieval eval measures how often the right passage actually comes back.

## How it works
- `agent.py`: `AgentBase` agent with one SWAIG tool, `search_filings`. The prompt requires a search before every answer and forbids numbers that aren't in the results.
- `retrieval.py`: Datasphere semantic search filtered by company tag. The agent and the eval share it, so the eval tests the same path a live call uses.
- `fetch_filings.py`: pulls each 10-K from SEC EDGAR and converts it to text.
- `rewrite_tables.py`: the v2 fix. Rewrites every table row as a self-describing sentence (company, statement, fiscal year, units) so search can match it. Also writes a prose-only copy with raw table rows removed. Both get uploaded.
- `check_answers.py`: confirms every expected answer in the question set is really in the filing, so a miss in the eval means retrieval failed, not that the question was wrong.
- `evals/run_eval.py`: 24 questions across income statement items, segment tables, and plain text. Reports hit@1 and hit@3 by type and prints every miss.

## Eval results

24 questions with known answers (checked against the filings by `check_answers.py`). A hit means a chunk containing the exact answer came back in the top 1 or top 3 search results.

| Question type | n | v1 hit@3 | v2 hit@3 | v3 hit@1 | v3 hit@3 |
|---|---|---|---|---|---|
| Income statement | 7 | 0% | 86% | 86% | **100%** |
| Segment tables | 9 | 11% | 22% | 78% | **100%** |
| Plain text | 8 | 75% | 62% | 75% | **88%** |
| **All** | 24 | 29% | 54% | 79% | **96%** |

**v1, raw 10-K text, default chunking.** Text questions were fine but financial numbers were almost never found. Two reasons. Flattened tables lose their context: a row like `Revenue | $ | 130,497 | $ | 60,922` has no company, year or statement name for a question to match. And default chunking cut each 10-K into only 19 to 32 chunks, so every chunk mixed dozens of unrelated topics.

**v2, tables rewritten as sentences** (`rewrite_tables.py`). Each row now carries its company, statement, fiscal year and units: `NVIDIA fiscal 2025 10-K, Consolidated Statements of Income | Revenue: fiscal year ended Jan 26, 2025: $130,497 million; ...`. Income statement questions went from 0% to 86%. Segment tables barely moved, and text questions dropped, because the new sentences were still packed into huge chunks next to table-of-contents and exhibit-index rows.

**v3, chunking fixed.** One table row per chunk, prose in 8-sentence chunks (a few hundred chunks per filing instead of ~25), raw table rows removed from the prose, and non-financial rows (table of contents, exhibit index) dropped. Everything moved up together.

**Remaining miss:** "When did NVIDIA's fiscal year 2025 end?" returns an unrelated table row (a tax reserve balance) whose label says "fiscal year ended Jan 26, 2025". The date is technically there, abbreviated, but the eval is a strict string match on "January 26, 2025" and the prose sentence that states it directly didn't rank, so it counts as a miss.

**Takeaway:** in v1 the retrieval quality problem was mostly a data preparation problem, not a model problem. Measuring by question type showed exactly where it broke.

## Run it
```bash
pip install -r requirements.txt
cp .env.example .env
python fetch_filings.py
python rewrite_tables.py
python check_answers.py
python upload_docs.py
python agent.py
python evals/run_eval.py v3
```
