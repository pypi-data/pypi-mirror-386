import httpx
import os
from typing import Any, Dict


class OpenEarth:
	def __init__(self, base_url: str = None, timeout: float = 15.0):
		if base_url is None:
			base_url = os.getenv("OPENEARTH_BASE_URL", "https://openearth.onrender.com")
		self.base_url = base_url.rstrip("/")
		self._client = httpx.Client(timeout=timeout)

	def health(self) -> Dict[str, Any]:
		r = self._client.get(f"{self.base_url}/health"); r.raise_for_status(); return r.json()

	def query(self, query: str) -> Dict[str, Any]:
		r = self._client.post(f"{self.base_url}/query", json={"query": query}); r.raise_for_status(); return r.json()

	def close(self) -> None:
		self._client.close()
