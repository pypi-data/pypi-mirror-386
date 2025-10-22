# indolaw_scraper/kemendag.py


import requests
from bs4 import BeautifulSoup
import json
from indolaw_scraper.models.document import LegalDocument

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_kemendag_data(url):
    """Scrape metadata dokumen dari JDIH Kemendag."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error saat mengambil data: {e}")
        return {}

    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.select("table.table tbody tr")
    data = {}

    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 2:
            label = cols[0].get_text(strip=True)
            value = cols[1].get_text(strip=True)
            data[label] = value

    return data

if __name__ == "__main__":
    test_url = "https://jdih.kemendag.go.id/peraturan/keputusan-menteri-perdagangan-nomor-1484-tahun-2025-tentang-harga-referensi-crude-palm-oil-yang-dikenakan-bea-keluar-dan-tarif-layanan-badan-layanan-umum-badan-pengelola-dana-perkebunan-kelapa-sawit"
    result = get_kemendag_data(test_url)
    print("=== DETAIL DOKUMEN KEMENDAG ===")
    for k, v in result.items():
        print(f"{k}: {v}")


# =============================
# Scrape Banyak Dokumen
# =============================


import requests
from bs4 import BeautifulSoup
import json
import time
import os
from indolaw_scraper.models.document import LegalDocument

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URL = "https://jdih.kemendag.go.id/peraturan"


def get_all_document_links():
    """Ambil semua link dokumen peraturan dari halaman indeks Kemendag"""
    res = requests.get(BASE_URL, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(res.content, 'html.parser')
    link_tags = soup.select("a[href^='https://jdih.kemendag.go.id/peraturan/']")
    return list(set(a['href'] for a in link_tags if a['href'].startswith("https://jdih.kemendag.go.id/peraturan/")))


def scrape_metadata(url):
    """Scrape metadata dari halaman dokumen"""
    res = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(res.content, 'html.parser')
    rows = soup.select("table.table tbody tr")
    metadata = {}
    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 2:
            label = cols[0].get_text(strip=True)
            value = cols[1].get_text(strip=True)
            metadata[label] = value
    metadata["URL"] = url
    return metadata


def scrape_and_save_all(limit=5, delay=1, output_dir="kemendag_metadata"):
    """Scrape dan simpan semua metadata ke file JSON"""
    os.makedirs(output_dir, exist_ok=True)
    links = get_all_document_links()[:limit]
    all_data = []

    for i, link in enumerate(links):
        print(f"[{i+1}] Scraping: {link}")
        try:
            data = scrape_metadata(link)
            all_data.append(data)
            nomor = data.get("Nomor Peraturan", f"doc_{i+1}").replace(" ", "_")
            filename = f"{output_dir}/metadata_{nomor}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            time.sleep(delay)
        except Exception as e:
            print(f"⚠️ Gagal scraping {link}: {e}")

    with open(f"{output_dir}/metadata_kemendag.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"\n📁 Selesai! Metadata disimpan di folder '{output_dir}'.")


if __name__ == "__main__":
    scrape_and_save_all(limit=3)  # Ubah limit sesuai kebutuhan



