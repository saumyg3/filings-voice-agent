# tag -> filing info. One 10-K per company, pinned to a fiscal year so the eval answers stay fixed.
COMPANIES = {
    "nvda": {"name": "NVIDIA", "cik": "1045810", "period": "2025-01-26", "label": "fiscal 2025 10-K"},
    "aapl": {"name": "Apple", "cik": "320193", "period": "2024-09-28", "label": "fiscal 2024 10-K"},
}


def filing_path(tag):
    return f"filings/{tag}_10k_{COMPANIES[tag]['period']}.txt"
