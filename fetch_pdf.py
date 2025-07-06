# File: fetch_pdf.py

import os
import time
import re
import requests
from selenium import webdriver
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse

SCI_HUB_MIRRORS = [
    "https://sci-hub.se",
    "https://sci-hub.st",
    "https://sci-hub.ru",
    "https://sci-hub.hkvisa.net"
]

AD_DOMAINS = [
    "doubleclick.net", "googlesyndication.com", "adsbygoogle", "adnxs.com"
]

def sanitize_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "_", title)

def is_ad_url(url):
    host = urlparse(url).netloc.lower()
    return any(ad in host for ad in AD_DOMAINS)

def download_pdf(identifier):
    downloads_path = str(Path.home() / "Downloads")
    os.makedirs(downloads_path, exist_ok=True)

    options = uc.ChromeOptions()
    options.headless = True
    driver = uc.Chrome(options=options)

    for mirror in SCI_HUB_MIRRORS:
        try:
            print(f"[i] Trying mirror: {mirror}")
            driver.get(f"{mirror}/{identifier}")
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            iframes = soup.find_all("iframe")

            for iframe in iframes:
                src = iframe.get("src", "")
                if not src or is_ad_url(src):
                    continue

                pdf_url = src
                if pdf_url.startswith("//"):
                    pdf_url = "https:" + pdf_url
                elif pdf_url.startswith("/"):
                    pdf_url = mirror + pdf_url

                print(f"[✓] Trying PDF candidate: {pdf_url}")
                pdf_response = requests.get(pdf_url, stream=True, timeout=15)

                content_type = pdf_response.headers.get("Content-Type", "")
                if "pdf" not in content_type.lower():
                    print("[✗] Skipped: Not a valid PDF MIME type.")
                    continue

                first_bytes = pdf_response.raw.read(5)
                if not first_bytes.startswith(b"%PDF-"):
                    print("[✗] Skipped: Not a valid PDF header.")
                    continue

                pdf_response.raw.decode_content = True

                title_tag = soup.find("title")
                title = title_tag.text.strip() if title_tag else "downloaded"
                filename = sanitize_filename(title[:100]) + ".pdf"
                output_path = os.path.join(downloads_path, filename)

                with open(output_path, "wb") as f:
                    f.write(first_bytes)
                    for chunk in pdf_response.iter_content(chunk_size=4096):
                        f.write(chunk)

                print(f"[✓] Saved: {output_path}")
                driver.quit()
                return True

        except Exception as e:
            print(f"[!] Mirror failed: {mirror} - {e}")
            continue

    driver.quit()
    return False
