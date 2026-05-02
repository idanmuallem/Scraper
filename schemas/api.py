from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from enum import Enum


class Sentiment(str, Enum):
	Positive = "Positive"
	Negative = "Negative"
	Neutral = "Neutral"


class ExtractedEntitySchema(BaseModel):
	"""
	The strict JSON structure we require the LLM to output 
	for every supply chain or ESG mention it finds.
	"""
	ticker: str = Field(..., description="The stock ticker symbol of the company mentioned.")
	sentiment: Sentiment = Field(..., description="Must be exactly 'Positive', 'Negative', or 'Neutral'.")
	insight: str = Field(..., description="A concise, 1-2 sentence summary of the extracted data point.")


class DocumentExtractionResult(BaseModel):
	"""
	The wrapper schema that holds a list of all entities 
	found in a single raw document.
	"""
	source_url: str
	extracted_entities: List[ExtractedEntitySchema] = Field(default_factory=list)


class APIResponseSchema(BaseModel):
	"""
	The schema used to return data to your paying API customers.
	"""
	id: int
	ticker: str
	sentiment: str
	insight: str
	created_at: datetime

	class Config:
		from_attributes = True


# Backwards-compatible aliases for earlier internal names used in tests and routers
class ScrapeRequest(BaseModel):
	source_url: str
	source_type: str | None = None


class RawDocumentCreate(BaseModel):
	source_url: str
	content: str
	source_type: str | None = None


class RawDocumentRead(BaseModel):
	id: int
	source_url: str
	content: str
	source_type: str | None = None
	scraped_at: datetime


class EntityExtractionResult(ExtractedEntitySchema):
	"""Alias: keep compatibility with previous name used in tests."""


class EntityExtractionBatchResponse(BaseModel):
	data: List[EntityExtractionResult] = Field(default_factory=list)


class ErrorResponse(BaseModel):
	detail: str
	metadata: dict | None = None
