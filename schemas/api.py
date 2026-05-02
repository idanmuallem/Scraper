from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ScrapeRequest(BaseModel):
	"""Request body for scraping a financial document from a URL."""

	source_url: HttpUrl
	source_type: str | None = Field(default=None, examples=["10-K", "Earnings Call"])


class RawDocumentCreate(BaseModel):
	"""Payload used when persisting raw scraped content."""

	source_url: HttpUrl
	content: str
	source_type: str | None = None


class RawDocumentRead(BaseModel):
	"""Response shape for a stored raw document."""

	model_config = ConfigDict(from_attributes=True)

	id: int
	source_url: HttpUrl
	content: str
	source_type: str | None = None
	scraped_at: datetime


class ExtractedEntityBase(BaseModel):
	"""Shared fields for extracted AI entity data."""

	ticker: str = Field(..., examples=["AAPL", "MSFT"])
	sentiment: str | None = Field(default=None, examples=["Positive", "Negative", "Neutral"])
	insight: str = Field(..., description="The extracted business or financial insight.")


class ExtractedEntityCreate(ExtractedEntityBase):
	"""Payload used when storing AI extracted entities."""

	document_id: int


class ExtractedEntityRead(ExtractedEntityBase):
	"""Response shape for extracted entities."""

	model_config = ConfigDict(from_attributes=True)

	id: int
	document_id: int
	created_at: datetime


class EntityExtractionRequest(BaseModel):
	"""Input text sent to the AI extraction step."""

	text: str = Field(..., min_length=1)


class EntityExtractionResult(BaseModel):
	"""Strict JSON contract for the LLM extraction response."""

	ticker: str = Field(..., examples=["AAPL", "MSFT"])
	sentiment: str | None = Field(default=None, examples=["Positive", "Negative", "Neutral"])
	insight: str = Field(..., description="A concise extracted insight in plain English.")


class EntityExtractionResponse(BaseModel):
	"""Wrapper around a single validated extraction result."""

	model_config = ConfigDict(from_attributes=True)

	data: EntityExtractionResult


class EntityExtractionBatchResponse(BaseModel):
	"""Wrapper for multiple extracted entities."""

	model_config = ConfigDict(from_attributes=True)

	data: list[EntityExtractionResult]


class ErrorResponse(BaseModel):
	"""Standard API error payload."""

	detail: str
	metadata: dict[str, Any] | None = None
