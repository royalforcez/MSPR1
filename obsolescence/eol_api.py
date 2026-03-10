import json
import os
import time
import requests
from .utils import ensure_output_dir

EOL_API_BASE = "https://endoflife.date/api/v1"
CACHE_TTL_SECONDS = 86400


class EOLClient:

    def __init__(self):

        ensure_output_dir()

        self.cache_path = os.path.join("outputs", "obsolescence", "eol_cache.json")
        self._cache = self._load_cache()

    def _load_cache(self):

        if not os.path.exists(self.cache_path):
            return {}

        try:
            with open(self.cache_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_cache(self):

        with open(self.cache_path, "w") as f:
            json.dump(self._cache, f)

    def _is_fresh(self, key):

        entry = self._cache.get(key)

        if not entry:
            return False

        fetched_at = entry.get("_fetched_at_epoch")

        if not fetched_at:
            return False

        return (time.time() - fetched_at) < CACHE_TTL_SECONDS

    def get_product(self, product):

        cache_key = f"product:{product}"

        if self._is_fresh(cache_key):
            return self._cache[cache_key]["data"]

        url = f"{EOL_API_BASE}/products/{product}"

        r = requests.get(url)

        if r.status_code != 200:
            raise RuntimeError("Erreur API endoflife")

        data = r.json()

        self._cache[cache_key] = {
            "_fetched_at_epoch": int(time.time()),
            "data": data
        }

        self._save_cache()

        return data

    def list_releases(self, product):

        data = self.get_product(product)

        return (data.get("result") or {}).get("releases") or []