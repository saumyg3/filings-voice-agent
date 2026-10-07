# Filings Voice Agent

Call a phone number and ask about NVIDIA's or Apple's 10-K. The agent runs on SignalWire's
AI Agent runtime, searches the filings in Datasphere, and answers only from what it finds.
A retrieval eval measures how often the right passage actually comes back.

## How it works
- `agent.py`: `AgentBase` agent with one SWAIG tool, `search_filings`. The prompt requires a search before every answer and forbids numbers that aren't in the results.
- `retrieval.py`: Datasphere semantic search filtered by company tag. The agent and the eval share it, so the eval tests the same path a live call uses.
- `fetch_filings.py`: pulls each 10-K from SEC EDGAR and converts it to text.
- `rewrite_tables.py`: the v2 fix. Rewrites every table row as a self-describing sentence (company, statement, fiscal year, units) so search can match it. Uploaded next to the original text.
- `check_answers.py`: confirms every expected answer in the question set is really in the filing, so a miss in the eval means retrieval failed, not that the question was wrong.
- `evals/run_eval.py`: 24 questions across income statement items, segment tables, and plain text. Reports hit@1 and hit@3 by type and prints every miss.

## Eval results

**v1, raw 10-K text:** 29% hit@3 overall. Plain-text questions did fine (75%), but income statement questions hit 0% and segment tables 11%.
Flattened tables lose their context: a row like `Revenue | $ | 130,497 | $ | 60,922` has no company, year or statement name, so a question like "what was NVIDIA's revenue in fiscal 2025" has nothing to match.

**v2, tables rewritten as sentences:** _paste evals/results_table_v2.md_

_What changed and what still misses:_

## Run it
```bash
pip install -r requirements.txt
cp .env.example .env
python fetch_filings.py
python rewrite_tables.py
python check_answers.py
python upload_docs.py
python agent.py
python evals/run_eval.py v2
```
