from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from db import models
from schemas.api import ExtractedEntityRead, ErrorResponse

router = APIRouter()


@router.get("/entities", response_model=list[ExtractedEntityRead], responses={404: {"model": ErrorResponse}})
def list_entities(limit: int = 50, db: Session = Depends(get_db)) -> Any:
	items = db.query(models.ExtractedEntity).limit(limit).all()
	return items


@router.get("/entities/{entity_id}", response_model=ExtractedEntityRead, responses={404: {"model": ErrorResponse}})
def get_entity(entity_id: int, db: Session = Depends(get_db)) -> Any:
	ent = db.query(models.ExtractedEntity).filter(models.ExtractedEntity.id == entity_id).first()
	if not ent:
		raise HTTPException(status_code=404, detail="Entity not found")
	return ent
