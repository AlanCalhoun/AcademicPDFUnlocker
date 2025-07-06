# File: resolver.py

import requests

CROSSREF_API = "https://api.crossref.org/works"
UNPAYWALL_API = "https://api.unpaywall.org/v2"

def resolve_title_to_doi(title):
    try:
        params = {"query.title": title, "rows": 1}
        response = requests.get(CROSSREF_API, params=params, timeout=10)
        response.raise_for_status()
        items = response.json().get("message", {}).get("items", [])
        if items:
            return items[0].get("DOI")
    except Exception as e:
        print(f"[!] CrossRef failed: {e}")
    return None

def get_unpaywall_pdf_url(doi):
    try:
        # Use a valid email (required by Unpaywall)
        response = requests.get(f"{UNPAYWALL_API}/{doi}?email=open@localhost", timeout=10)
        response.raise_for_status()
        oa_info = response.json()
        best = oa_info.get("best_oa_location")
        if best and best.get("url_for_pdf"):
            return best["url_for_pdf"]
    except Exception as e:
        print(f"[!] Unpaywall failed: {e}")
    return None
