import json
import os
import time
import requests
from .utils import ensure_output_dir

EOL_API_BASE = "https://endoflife.date/api/v1"
CACHE_TTL_SECONDS = 86400  # 24h


class EOLClient:
    """
    Client pour interroger l'API endoflife.date avec gestion de cache local.
    """

    def __init__(self):
        # Création du dossier de sortie si nécessaire
        ensure_output_dir()

        # Chemin du cache JSON
        self.cache_path = os.path.join("outputs", "obsolescence", "eol_cache.json")

        # Chargement du cache en mémoire
        self._cache = self._load_cache()

    # =========================================================
    # GESTION DU CACHE
    # =========================================================

    def _load_cache(self):
        """
        Charge le cache depuis le disque.
        """
        if not os.path.exists(self.cache_path):
            return {}

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_cache(self):
        """
        Sauvegarde le cache sur le disque.
        """
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=4, ensure_ascii=False)
        except Exception:
            pass  # on évite de bloquer l'appli si le cache échoue

    def _is_fresh(self, key):
        """
        Vérifie si une entrée du cache est encore valide.
        """
        entry = self._cache.get(key)

        if not entry:
            return False

        fetched_at = entry.get("_fetched_at_epoch")

        if not fetched_at:
            return False

        return (time.time() - fetched_at) < CACHE_TTL_SECONDS

    # =========================================================
    # APPEL API
    # =========================================================

    def get_product(self, product):
        """
        Récupère les données d’un produit depuis l’API (avec cache).
        """

        cache_key = f"product:{product}"

        # -------------------------------
        # 1. Vérification cache
        # -------------------------------
        if self._is_fresh(cache_key):
            return self._cache[cache_key]["data"]

        # -------------------------------
        # 2. Appel API
        # -------------------------------
        url = f"{EOL_API_BASE}/products/{product}"

        try:
            response = requests.get(url, timeout=5)
        except requests.RequestException as e:
            raise RuntimeError(f"Erreur réseau API : {e}")

        if response.status_code != 200:
            raise RuntimeError(f"Erreur API endoflife (HTTP {response.status_code})")

        try:
            data = response.json()
        except Exception:
            raise RuntimeError("Réponse API invalide (JSON)")

        # -------------------------------
        # 3. Mise en cache
        # -------------------------------
        self._cache[cache_key] = {
            "_fetched_at_epoch": int(time.time()),
            "data": data
        }

        self._save_cache()

        return data

    def list_releases(self, product):
        """
        Retourne la liste des versions d’un produit.
        """
        data = self.get_product(product)

        return (data.get("result") or {}).get("releases") or []