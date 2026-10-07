# Filings Voice Agent

Call a phone number and ask about NVIDIA's or Apple's 10-K. The agent runs on SignalWire's
AI Agent runtime, searches the filings in Datasphere, and answers only from what it finds.
A retrieval eval measures how often the right passage actually comes back.

## How it works
- `agent.py`: `AgentBase` agent with one SWAIG tool, `search_filings`. The prompt requires a search before every answer and forbids numbers that aren't in the results.
- `retrieval.py`: Datasphere semantic search filtered by company tag. The agent and the eval share it, so the eval tests the same path a live call uses.
- `fetch_filings.py`: pulls each 10-K from SEC EDGAR and converts it to text.
- `check_answers.py`: confirms every expected answer in the question set is really in the filing, so a miss in the eval means retrieval failed, not that the question was wrong.
- `evals/run_eval.py`: 24 questions across income statement items, segment tables, and plain text. Reports hit@1 and hit@3 by type and prints every miss.

## Eval results
_paste evals/results_table.md here_

**What I learned:** _1 to 3 sentences on where retrieval broke and why_

## Run it
```bash
pip install -r requirements.txt
cp .env.example .env
python fetch_filings.py
python check_answers.py
python upload_docs.py
python agent.py
python evals/run_eval.py
```
