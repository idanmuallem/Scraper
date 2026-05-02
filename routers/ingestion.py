from __future__ import annotations

from typing import Any

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from core.database import get_db
from db import models
from schemas.api import (
	ScrapeRequest,
	EntityExtractionBatchResponse,
	ErrorResponse,
	DocumentExtractionResult,
	ExtractedEntitySchema,
)
from services.scraper import fetch_financial_text
from services.ai_processor import AIProcessor

logger = logging.getLogger(__name__)
router = APIRouter()


def _normalize_to_entities(result: object) -> list[ExtractedEntitySchema]:
	"""Validate and normalize the model output into a list of ExtractedEntitySchema."""
	if isinstance(result, dict) and "extracted_entities" in result:
		doc = DocumentExtractionResult.model_validate(result)
		return doc.extracted_entities

	if isinstance(result, dict) and all(k in result for k in ("ticker", "insight")):
		item = ExtractedEntitySchema.model_validate(result)
		return [item]

	if isinstance(result, list):
		entities: list[ExtractedEntitySchema] = []
		for r in result:
			entities.append(ExtractedEntitySchema.model_validate(r))
		return entities
	raise ValueError("Unrecognized LLM response format")


@router.post("/ingest", response_model=EntityExtractionBatchResponse, responses={400: {"model": ErrorResponse}})
async def ingest_document(request: ScrapeRequest, db: Session = Depends(get_db)) -> Any:
	"""Fetch a document, persist raw text, run AI extraction, validate strictly, and persist entities.

	This function will attempt a small number of validation retries when the LLM returns malformed JSON.
	"""
	# Fetch text
	try:
		text = await fetch_financial_text(str(request.source_url))
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

	# Persist raw document if not exists
	existing = db.query(models.RawDocument).filter(models.RawDocument.source_url == str(request.source_url)).first()
	if existing is None:
		raw = models.RawDocument(
			source_url=str(request.source_url), content=text, source_type=request.source_type
		)
		db.add(raw)
		db.commit()
		db.refresh(raw)
	else:
		raw = existing

	processor = AIProcessor()

	# Try to extract and validate; on ValidationError, retry a few times
	max_validation_attempts = 3
	attempts = 0
	last_exc: Exception | None = None
	while attempts < max_validation_attempts:
		try:
			result = processor.extract(text)
			entities = _normalize_to_entities(result)
			break
		except (ValidationError, ValueError) as ve:
			attempts += 1
			last_exc = ve
			logger.warning("LLM output failed schema validation (attempt %s/%s): %s", attempts, max_validation_attempts, ve)
			# Immediate retry and validate
			try:
				retry_result = processor.extract(text)
				entities = _normalize_to_entities(retry_result)
				break
			except (ValidationError, ValueError) as ve2:
				last_exc = ve2
				logger.warning("LLM retry also failed schema validation: %s", ve2)
				# continue loop to allow another round
			except Exception as exc:
				last_exc = exc
				logger.error("LLM call failed during retry: %s", exc)
				raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
		except Exception as exc:
			# Non-validation error from the LLM call
			logger.error("LLM extraction failed: %s", exc)
			raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
	else:
		# Exhausted retries
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(last_exc))

	response_items: list[dict[str, Any]] = []
	for ent_model in entities:
		ent = models.ExtractedEntity(document_id=raw.id, ticker=ent_model.ticker, sentiment=ent_model.sentiment, insight=ent_model.insight)
		db.add(ent)
		db.commit()
		db.refresh(ent)
		response_items.append({"ticker": ent.ticker, "sentiment": ent.sentiment, "insight": ent.insight})

	return {"data": response_items}
