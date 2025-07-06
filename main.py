# File: main.py

import sys
import os
import requests
from resolver import resolve_title_to_doi, get_unpaywall_pdf_url
from fetch_pdf import download_pdf

def save_pdf_from_url(url, title):
    try:
        filename = title[:100].replace(" ", "_") + ".pdf"
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)
        with requests.get(url, stream=True, timeout=15) as r:
            if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("application/pdf"):
                with open(downloads_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=4096):
                        f.write(chunk)
                print(f"[✓] OA PDF saved to: {downloads_path}")
                return True
        print("[✗] OA link found, but not a valid PDF.")
    except Exception as e:
        print(f"[!] Download failed: {e}")
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <DOI or article title>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    # Step 1: Is it a DOI?
    if query.startswith("10."):
        doi = query
    else:
        print("[i] Resolving title via CrossRef...")
        doi = resolve_title_to_doi(query)
        if not doi:
            print("[✗] Could not resolve title to DOI.")
            sys.exit(1)
        print(f"[✓] Title resolved to DOI: {doi}")

    # Step 2: Try Unpaywall
    print("[i] Checking Unpaywall for open access copy...")
    pdf_url = get_unpaywall_pdf_url(doi)
    if pdf_url:
        print(f"[✓] Found OA copy: {pdf_url}")
        if save_pdf_from_url(pdf_url, doi):
            return

    # Step 3: Fallback to Sci-Hub
    print("[i] Falling back to Sci-Hub...")
    success = download_pdf(doi)
    if success:
        print("[✓] PDF downloaded successfully via Sci-Hub.")
    else:
        print("[✗] Failed to download from all sources.")

if __name__ == "__main__":
    main()
