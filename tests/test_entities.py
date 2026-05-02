from datetime import datetime

import pytest
from pydantic import ValidationError

from schemas.api import EntityExtractionResult, RawDocumentCreate, RawDocumentRead, ScrapeRequest


def test_scrape_request_accepts_source_url_and_source_type() -> None:
	request = ScrapeRequest(source_url="https://example.com/doc", source_type="10-K")

	assert str(request.source_url) == "https://example.com/doc"
	assert request.source_type == "10-K"


def test_raw_document_read_requires_expected_fields() -> None:
	document = RawDocumentRead(
		id=1,
		source_url="https://example.com/doc",
		content="raw text",
		source_type="Earnings Call",
		scraped_at=datetime(2026, 5, 2),
	)

	assert document.id == 1
	assert document.content == "raw text"


def test_entity_extraction_result_rejects_missing_insight() -> None:
	with pytest.raises(ValidationError):
		EntityExtractionResult(ticker="AAPL", sentiment="Positive")


def test_raw_document_create_accepts_minimal_payload() -> None:
	payload = RawDocumentCreate(source_url="https://example.com/doc", content="content")

	assert payload.source_type is None
	assert payload.content == "content"
