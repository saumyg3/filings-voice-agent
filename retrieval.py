"""Datasphere search, shared by the agent and the eval so the eval tests the exact path a call uses."""
from signalwire.rest import RestClient

_client = None


def client():
    global _client
    if _client is None:
        _client = RestClient()  # reads SIGNALWIRE_PROJECT_ID / SIGNALWIRE_API_TOKEN / SIGNALWIRE_SPACE
    return _client


def search(query, company=None, count=3):
    tags = [company.lower()] if company else None
    res = client().datasphere.documents.search(query_string=query, tags=tags, count=count)
    return [{"text": c.get("text", ""), "document_id": c.get("document_id")} for c in res.get("chunks", [])]
