import time
import logging
import httpx

log = logging.getLogger(__name__)


class OpenCloudClient:
    """Thin wrapper around Roblox Open Cloud v1 and v2 HTTP endpoints."""

    BASE_URL = "https://apis.roblox.com"

    def __init__(self, api_key: str, timeout: float = 10.0, max_retries: int = 4):
        self.api_key = api_key
        self.max_retries = max_retries
        self.session = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "x-api-key": self.api_key,
                "User-Agent": "roblox-panel-cli/0.2",
            },
            timeout=timeout,
        )

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        attempt = 0
        delay = 0.5
        while True:
            attempt += 1
            try:
                # print(f"DEBUG: {method} {path} attempt={attempt}")
                res = self.session.request(method, path, **kwargs)
                if res.status_code in (429, 503) and attempt <= self.max_retries:
                    retry_header = res.headers.get("Retry-After")
                    if retry_header and retry_header.isdigit():
                        sleep_sec = float(retry_header)
                    else:
                        sleep_sec = delay
                        delay *= 2
                    log.debug("rate limited on %s, sleeping %.1fs (attempt %d)", path, sleep_sec, attempt)
                    time.sleep(sleep_sec)
                    continue

                res.raise_for_status()
                return res
            except httpx.NetworkError as exc:
                if attempt > self.max_retries:
                    raise
                time.sleep(delay)
                delay *= 2

    def get_universe_info(self, universe_id: int) -> dict:
        r = self._request("GET", f"/universes/v1/universes/{universe_id}")
        return r.json()

    def get_place_stats(self, universe_id: int) -> dict:
        # public endpoint for live player counts per universe
        # not technically open cloud v2 but reliable and doesn't eat key quota
        r = self._request("GET", f"https://games.roblox.com/v1/games?universeIds={universe_id}")
        data = r.json().get("data", [])
        return data[0] if data else {}

    def list_datastores(self, universe_id: int, prefix: str = "", limit: int = 50, cursor: str | None = None) -> dict:
        params = {
            "maxItems": min(limit, 100),
        }
        if prefix:
            params["prefix"] = prefix
        # roblox sometimes gives empty string cursor when reaching the last page
        if cursor and cursor.strip():
            params["cursor"] = cursor

        r = self._request("GET", f"/datastores/v1/universes/{universe_id}/standard-datastores", params=params)
        data = r.json()
        if "nextPageCursor" in data and not data["nextPageCursor"]:
            data["nextPageCursor"] = None
        return data

    def list_keys(self, universe_id: int, datastore: str, prefix: str = "", limit: int = 50, cursor: str | None = None, scope: str = "global") -> dict:
        # TODO: handle multi-key ordering if roblox ever fixes cursor pagination on ordered datastores
        params = {
            "datastoreName": datastore,
            "scope": scope,
            "maxItems": min(limit, 100),
        }
        if prefix:
            params["prefix"] = prefix
        if cursor and cursor.strip():
            params["cursor"] = cursor

        r = self._request("GET", f"/datastores/v1/universes/{universe_id}/standard-datastores/datastore/entries", params=params)
        data = r.json()
        if "nextPageCursor" in data and not data["nextPageCursor"]:
            data["nextPageCursor"] = None
        return data

    def get_datastore_entry(self, universe_id: int, datastore: str, key: str, scope: str = "global") -> tuple[bytes, dict]:
        params = {
            "datastoreName": datastore,
            "entryKey": key,
            "scope": scope,
        }
        r = self._request("GET", f"/datastores/v1/universes/{universe_id}/standard-datastores/datastore/entries/entry", params=params)
        meta = {
            "version": r.headers.get("roblox-entry-version"),
            "created": r.headers.get("roblox-entry-created-time"),
            "attributes": r.headers.get("roblox-entry-attributes"),
        }
        return r.content, meta

    def close(self):
        self.session.close()
