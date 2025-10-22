from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urlencode
from urllib.request import urlopen


@dataclass
class ExchangeRateApiClient:
    api_key: str
    base_url: str = "https://api.exchangerateapi.com/v1"

    def _get(self, path: str, params: dict) -> dict:
        query = urlencode({**params, "apikey": self.api_key})
        url = f"{self.base_url}{path}?{query}"
        with urlopen(url) as resp:
            data = resp.read().decode("utf-8")
        payload = json.loads(data)
        if isinstance(payload, dict) and payload.get("error"):
            message = payload.get("error", {}).get("message") or "API error"
            raise RuntimeError(message)
        return payload

    def latest(self, *, base: str, symbols: Optional[Iterable[str]] = None) -> dict:
        if not base:
            raise ValueError("base is required")
        params = {"base": base}
        if symbols:
            params["symbols"] = ",".join(symbols)
        return self._get("/latest", params)

    def historical(self, *, date: str, base: str, symbols: Optional[Iterable[str]] = None) -> dict:
        if not date:
            raise ValueError("date is required (YYYY-MM-DD)")
        if not base:
            raise ValueError("base is required")
        params = {"date": date, "base": base}
        if symbols:
            params["symbols"] = ",".join(symbols)
        return self._get("/historical", params)
