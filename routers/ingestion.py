from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from db import models
from schemas.api import (
	ScrapeRequest,
	RawDocumentCreate,
	ExtractedEntityCreate,
	EntityExtractionBatchResponse,
	EntityExtractionResponse,
	ErrorResponse,
)
from services.scraper import fetch_financial_text
from services.ai_processor import AIProcessor

router = APIRouter()


@router.post("/ingest", response_model=EntityExtractionBatchResponse, responses={400: {"model": ErrorResponse}})
async def ingest_document(request: ScrapeRequest, db: Session = Depends(get_db)) -> Any:
	"""Fetch a document, persist raw text, run AI extraction, and persist extracted entities."""
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

	# Run AI extraction
	processor = AIProcessor()
	try:
		result = processor.extract(text)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

	# Normalize result into list of dicts
	if isinstance(result, dict):
		items = [result]
	else:
		items = list(result)

	response_items: list[dict[str, Any]] = []
	for item in items:
		ticker = item.get("ticker") or item.get("symbol") or ""
		insight = item.get("insight") or item.get("text") or ""
		sentiment = item.get("sentiment")

		if not ticker or not insight:
			# skip malformed items
			continue

		ent = models.ExtractedEntity(document_id=raw.id, ticker=ticker, sentiment=sentiment, insight=insight)
		db.add(ent)
		db.commit()
		db.refresh(ent)

		response_items.append({"ticker": ent.ticker, "sentiment": ent.sentiment, "insight": ent.insight})

	return {"data": response_items}
