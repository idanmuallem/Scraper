import logging

import httpx
from bs4 import BeautifulSoup

from core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_financial_text(url: str) -> str:
	"""
	Fetch a raw financial document asynchronously and return cleaned plain text.
	"""

	settings = get_settings()
	headers = {
		"User-Agent": "AlternativeDataAPI/1.0 (Contact: dev@yourdomain.com)",
	}
	proxies = None
	if settings.http_proxy or settings.https_proxy:
		proxies = {
			"http://": settings.http_proxy,
			"https://": settings.https_proxy,
		}

	try:
		async with httpx.AsyncClient(proxies=proxies) as client:
			response = await client.get(url, headers=headers, timeout=15.0)
			response.raise_for_status()

			soup = BeautifulSoup(response.text, "html.parser")
			text_content = soup.get_text(separator=" ", strip=True)

			logger.info("Successfully scraped %s characters from %s", len(text_content), url)
			return text_content
	except httpx.HTTPStatusError:
		logger.exception("HTTP error occurred while scraping %s", url)
		raise
	except Exception:
		logger.exception("An unexpected error occurred while scraping %s", url)
		raise
