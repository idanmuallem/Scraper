from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from tenacity import before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from core.config import get_settings

logger = logging.getLogger(__name__)

RETRYABLE_LLM_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError, TimeoutError)


class ExtractionBackend(Protocol):
    def extract(self, text: str) -> Mapping[str, Any]:
        """Extract structured financial entities from free-form text."""


class BaseExtractionBackend(ABC):
    @abstractmethod
    def extract(self, text: str) -> Mapping[str, Any]:
        raise NotImplementedError


@dataclass(slots=True)
class OpenAIExtractionBackend(BaseExtractionBackend):
    client: OpenAI
    model: str

    def extract(self, text: str) -> Mapping[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured financial entities from text and return only valid JSON. "
                        "Use short, consistent keys such as entities, amounts, dates, tickers, and notes."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)


class AIProcessor:
    """Thin orchestration layer around an interchangeable entity extraction backend."""

    def __init__(self, backend: ExtractionBackend | None = None) -> None:
        settings = get_settings()
        self._settings = settings
        self._backend = backend or self._build_default_backend(settings)

    @staticmethod
    def _build_default_backend(settings: Any) -> ExtractionBackend:
        client_kwargs: dict[str, Any] = {}
        if settings.openai_api_key:
            client_kwargs["api_key"] = settings.openai_api_key
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        return OpenAIExtractionBackend(client=OpenAI(**client_kwargs), model=settings.openai_model)

    @retry(
        retry=retry_if_exception_type(RETRYABLE_LLM_ERRORS),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def extract(self, text: str) -> Mapping[str, Any]:
        return self._backend.extract(text)

    @property
    def backend_name(self) -> str:
        return type(self._backend).__name__


__all__ = ["AIProcessor", "BaseExtractionBackend", "ExtractionBackend", "OpenAIExtractionBackend"]