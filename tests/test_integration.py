from __future__ import annotations

import pytest

from schemas.api import ScrapeRequest
from routers.ingestion import ingest_document
from services.ai_processor import AIProcessor


class FakeDB:
    def __init__(self):
        self.raws = []
        self.ents = []

    def query(self, model):
        class Q:
            def __init__(self, parent):
                self.parent = parent

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return None

            def limit(self, n):
                return []

        return Q(self)

    def add(self, obj):
        if obj.__class__.__name__ == 'RawDocument':
            obj.id = 1
            self.raws.append(obj)
        elif obj.__class__.__name__ == 'ExtractedEntity':
            obj.id = len(self.ents) + 1
            self.ents.append(obj)

    def commit(self):
        return None

    def refresh(self, obj):
        return None


@pytest.mark.asyncio
async def test_ingest_retries_on_validation_and_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    # Fake scraper returns some text; patch the function reference used by the router
    async def _fake_fetch(url: str):
        return "Some financial text"

    monkeypatch.setattr("routers.ingestion.fetch_financial_text", _fake_fetch)

    # Fake AIProcessor.extract: first return malformed, then valid
    responses = [
        {"ticker": "AAPL", "sentiment": "Positive"},  # missing insight -> validation error
        {"ticker": "AAPL", "sentiment": "Positive", "insight": "Revenue up 10%"},
    ]

    def fake_extract(self, text: str):
        return responses.pop(0)

    monkeypatch.setattr(AIProcessor, "extract", fake_extract)

    db = FakeDB()
    req = ScrapeRequest(source_url="https://example.com/doc")

    res = await ingest_document(req, db=db)

    assert isinstance(res, dict)
    assert "data" in res
    assert len(res["data"]) == 1
    assert res["data"][0]["ticker"] == "AAPL"