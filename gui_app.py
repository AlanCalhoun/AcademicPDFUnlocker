# File: gui_app.py

import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, simpledialog, ttk
from resolver import resolve_title_to_doi, get_unpaywall_pdf_url
from fetch_pdf import download_pdf
import os
import requests
import webbrowser
import csv
import pandas as pd
import re
import sys

CROSSREF_API = "https://api.crossref.org/works"
download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

class TextRedirector:
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.insert(tk.END, str)
        self.widget.see(tk.END)
        self.widget.update_idletasks()

    def flush(self):
        pass

def extract_doi(text):
    doi_pattern = r"(10\.\d{4,9}/[\S]+)"
    match = re.search(doi_pattern, text)
    return match.group(1) if match else text.strip()

def looks_like_doi_or_title(text):
    if not text or not isinstance(text, str):
        return False
    if text.startswith("10.") or "doi.org/" in text:
        return True
    words = text.split()
    return len(words) >= 3 and any(c.isalpha() for c in text)

def get_column_data(rows):
    if not rows or not isinstance(rows[0], list):
        return []
    first_cell = rows[0][0]
    if looks_like_doi_or_title(first_cell):
        return [row[0] for row in rows if row]
    else:
        return [row[0] for row in rows[1:] if row]

def save_pdf_from_url(url, title):
    filename = title[:100].replace(" ", "_") + ".pdf"
    output_path = os.path.join(download_dir, filename)
    if os.path.exists(output_path):
        print(f"[→] Skipped (exists): {filename}")
        return True
    with requests.get(url, stream=True, timeout=15) as r:
        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("application/pdf"):
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=4096):
                    f.write(chunk)
            print(f"[✓] OA PDF saved: {output_path}")
            webbrowser.open("file://" + output_path)
            return True
    print("[✗] OA link found, but not a valid PDF.")
    return False

def preview_metadata(query):
    query = extract_doi(query)
    if query.startswith("10."):
        doi = query
    else:
        response = requests.get(CROSSREF_API, params={"query.title": query, "rows": 1}, timeout=10)
        items = response.json().get("message", {}).get("items", [])
        if not items:
            print("[✗] No metadata found.")
            return
        doi = items[0].get("DOI")

    response = requests.get(f"{CROSSREF_API}/{doi}", timeout=10)
    data = response.json()["message"]

    title = data.get("title", [""])[0]
    authors = ", ".join(
        f"{a.get('given', '')} {a.get('family', '')}".strip()
        for a in data.get("author", [])
    )
    journal = data.get("container-title", [""])[0]
    year = data.get("issued", {}).get("date-parts", [[None]])[0][0]

    print(f"[📄] Title: {title}")
    print(f"[👤] Authors: {authors}")
    print(f"[📚] Journal: {journal} ({year})")
    print(f"[🔗] DOI: {doi}\n")

def run_download(query):
    query = extract_doi(query)
    try:
        if query.startswith("10."):
            doi = query
        else:
            print("[i] Resolving title via CrossRef...")
            doi = resolve_title_to_doi(query)
            if not doi:
                print("[✗] Could not resolve title to DOI.")
                return
            print(f"[✓] Title resolved to DOI: {doi}")

        print("[i] Checking Unpaywall for OA copy...")
        pdf_url = get_unpaywall_pdf_url(doi)
        if pdf_url:
            print(f"[✓] OA found: {pdf_url}")
            if save_pdf_from_url(pdf_url, doi):
                return

        print("[i] Falling back to Sci-Hub...")
        if download_pdf(doi):
            print("[✓] PDF downloaded via Sci-Hub.")
        else:
            print("[✗] Failed from all sources.")
            with open(os.path.join(download_dir, "download_failures.txt"), "a") as f:
                f.write(query + "\n")

    except Exception as e:
        print(f"[!] Error: {e}")

def pick_folder(label):
    global download_dir
    folder = filedialog.askdirectory(initialdir=download_dir)
    if folder:
        download_dir = folder
        label.config(text=f"Download Folder: {download_dir}")

def batch_download(progress_bar, root):
    file_path = filedialog.askopenfilename(
        filetypes=[
            ("Supported files", "*.txt *.csv *.xlsx"),
            ("Text files", "*.txt"),
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx"),
            ("All files", "*.*")
        ]
    )
    if not file_path:
        return

    entries = []
    try:
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                entries = [line.strip() for line in f if line.strip()]
        elif file_path.endswith(".csv"):
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                entries = get_column_data(rows)
        elif file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path, header=None)
            rows = df.values.tolist()
            entries = get_column_data(rows)
    except Exception as e:
        print(f"[!] Failed to load file: {e}")
        return

    if not entries:
        print("[✗] No valid entries found.")
        return

    print(f"[i] Processing {len(entries)} items...")
    progress_bar["value"] = 0
    progress_bar["maximum"] = len(entries)
    progress_bar.pack(pady=5)
    root.update_idletasks()

    for i, entry in enumerate(entries, 1):
        print(f"\n[{i}/{len(entries)}] {entry}")
        root.update_idletasks()
        run_download(entry)
        progress_bar["value"] = i
        root.update_idletasks()

    progress_bar.pack_forget()
    print("\n[✓] Batch complete.")

def run_gui():
    root = tk.Tk()
    try:
        icon_path = os.path.join("assets", "pdf_unlocker_icon.png")
        icon_img = tk.PhotoImage(file=icon_path)
        root.iconphoto(True, icon_img)
    except Exception as e:
        print(f"[!] Could not load icon: {e}")

    root.title("Academic PDF Unlocker")

    instructions = (
        "🔍 Preview Metadata: Displays article title, authors, journal, and year.\n"
        "💾 Download PDF: Checks Unpaywall first, falls back to Sci-Hub.\n"
        "📂 Folder Picker: Choose where to save PDFs (default: Downloads).\n"
        "📁 Batch Download: Accepts .txt, .csv, or .xlsx (first column only).\n"
        "✔️ Existing files are skipped. Failures are logged to 'download_failures.txt'.\n"
    )
    tk.Label(root, text=instructions, justify="left", fg="blue").pack(padx=10, pady=5)

    tk.Label(root, text="Enter DOI or Article Title (or URL):").pack(padx=10, pady=2)
    input_frame = tk.Frame(root)
    input_frame.pack(padx=10, pady=2)
    entry = tk.Entry(input_frame, width=70)
    entry.pack(side=tk.LEFT, padx=5)
    tk.Button(input_frame, text="Download PDF", command=lambda: run_download(entry.get().strip())).pack(side=tk.LEFT)

    folder_label = tk.Label(root, text=f"Download Folder: {download_dir}")
    folder_label.pack(padx=10, pady=2)
    tk.Button(root, text="Select Folder", command=lambda: pick_folder(folder_label)).pack(pady=2)

    progress_bar = ttk.Progressbar(root, length=400, mode="determinate")
    progress_bar.pack(padx=10, pady=5)
    progress_bar.pack_forget()

    status_box = scrolledtext.ScrolledText(root, width=100, height=20)
    status_box.pack(padx=10, pady=10)

    sys.stdout = TextRedirector(status_box)
    sys.stderr = TextRedirector(status_box)

    tk.Button(root, text="🧹 Clear Output", command=lambda: status_box.delete(1.0, tk.END)).pack(pady=5)

    button_frame = tk.Frame(root)
    button_frame.pack()
    tk.Button(button_frame, text="Preview Metadata", command=lambda: preview_metadata(entry.get().strip())).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="📁 Batch Download", command=lambda: batch_download(progress_bar, root)).pack(side=tk.LEFT, padx=10)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
