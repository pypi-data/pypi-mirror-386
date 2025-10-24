"""Main API client for TrackID.net."""

import httpx

from trackidnet_client.models import Tracklist, SearchResult


class TrackIDNet:
    """Client for interacting with the TrackID.net API."""

    def __init__(
        self,
        base_url: str = "https://trackid.net:8001/api/public",
        timeout: float = 5.0,
        headers: dict[str, str] | None = None,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self._default_headers = {
            "User-Agent": "trackidnet-client/0.1.0",
            "Accept": "*/*",
            "Origin": "https://trackid.net",
            "Referer": "https://trackid.net/",
        }
        if headers:
            self._default_headers.update(headers)

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._default_headers,
        )

    def search_tracklist(
        self,
        keywords: str,
        current_page: int = 0,
        page_size: int = 20,
        **kwargs,
    ) -> SearchResult:
        """Search for tracklists"""
        params = {
            "keywords": keywords,
            "currentPage": current_page,
            "pageSize": page_size,
        }
        params.update(kwargs)

        data = self._client.get("/audiostreams", params=params)
        results = data.json().get("result")
        return SearchResult.model_validate(results)

    def get_tracklist(self, slug: str) -> Tracklist:
        """Get a specific tracklist by slug."""
        
        data = self._client.get(f"/audiostreams/{slug}")
        result = data.json().get("result")
        return Tracklist.model_validate(result)

