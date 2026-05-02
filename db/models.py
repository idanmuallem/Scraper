from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from core.database import Base


class RawDocument(Base):
	"""
	Stores the raw, unstructured text scraped from the web.
	"""

	__tablename__ = "raw_documents"

	id = Column(Integer, primary_key=True, index=True)
	source_url = Column(String, unique=True, index=True, nullable=False)
	content = Column(Text, nullable=False)
	source_type = Column(String)
	scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

	entities = relationship("ExtractedEntity", back_populates="document")


class ExtractedEntity(Base):
	"""
	Stores the clean, JSON-structured data parsed by the AI.
	"""

	__tablename__ = "extracted_entities"

	id = Column(Integer, primary_key=True, index=True)
	document_id = Column(Integer, ForeignKey("raw_documents.id"))
	ticker = Column(String, index=True, nullable=False)
	sentiment = Column(String)
	insight = Column(Text, nullable=False)
	created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

	document = relationship("RawDocument", back_populates="entities")
