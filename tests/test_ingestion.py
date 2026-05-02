from __future__ import annotations

import pytest

from services.scraper import fetch_financial_text


class _FakeResponse:
	def __init__(self, text: str) -> None:
		self.text = text

	def raise_for_status(self) -> None:
		return None


class _FakeAsyncClient:
	def __init__(self, *, proxies=None) -> None:
		self.proxies = proxies

	async def __aenter__(self) -> "_FakeAsyncClient":
		return self

	async def __aexit__(self, exc_type, exc, tb) -> None:
		return None

	async def get(self, url: str, headers: dict[str, str], timeout: float) -> _FakeResponse:
		assert url == "https://example.com/report"
		assert "User-Agent" in headers
		assert timeout == 15.0
		return _FakeResponse("<html><body><h1>Quarterly filing</h1><p>Revenue grew.</p></body></html>")


@pytest.mark.asyncio
async def test_fetch_financial_text_strips_html(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr("services.scraper.httpx.AsyncClient", _FakeAsyncClient)

	text = await fetch_financial_text("https://example.com/report")

	assert "Quarterly filing" in text
	assert "Revenue grew." in text
	assert "<html>" not in text
