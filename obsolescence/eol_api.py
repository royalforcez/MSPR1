import requests

EOL_API_BASE = "https://endoflife.date/api"


class EOLClient:
    """
    Client simple pour interroger l'API endoflife.date
    (sans cache, appel direct)
    """

    def list_releases(self, product):
        """
        Retourne la liste des versions d'un produit
        """

        url = f"{EOL_API_BASE}/{product}.json"

        response = requests.get(url)

        if response.status_code != 200:
            raise RuntimeError(f"Produit inconnu ou API indisponible : {product}")

        return response.json()