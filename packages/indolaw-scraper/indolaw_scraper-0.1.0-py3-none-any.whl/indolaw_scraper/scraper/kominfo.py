# indolaw_scraper/sources/kominfo.py

import requests
from bs4 import BeautifulSoup
import urllib3
from indolaw_scraper.models.document import LegalDocument

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_soup(url):
    res = requests.get(url, verify=False)
    return BeautifulSoup(res.text, 'html.parser')

def get_detail_data(url):
    soup = get_soup(url)
    field_map = {
        "Tipe Dokumen": "Tipe Dokumen",
        "Judul": "Judul",
        "T.E.U. Badan/Pengarang": "T.E.U Badan",
        "Nomor Peraturan": "Nomor Peraturan",
        "Jenis / Bentuk Peraturan": "Jenis/Bentuk Peraturan",
        "Singkatan Jenis/Bentuk Peraturan": "Singkatan Jenis/Bentuk Peraturan",
        "Tempat Penetapan": "Tempat Penetapan",
        "Tanggal-Bulan-Tahun Penetapan/Pengundangan": "Tanggal Ditetapkan / Diundangkan",
        "Sumber": "Sumber",
        "Subjek": "Subjek",
        "Status Peraturan": "Status",
        "Bahasa": "Bahasa",
        "Lokasi": "Lokasi",
        "Bidang Hukum": "Bidang Hukum",
        "Lampiran": "Lampiran"
    }
    
    data = {}
    for row in soup.select("table tr"):
        cols = row.find_all("td")
        if len(cols) >= 2:
            label = cols[0].get_text(strip=True)
            value = cols[1].get_text(strip=True).replace("\n", " ")
            if label in field_map:
                data[field_map[label]] = value
    return data

def scrape_putusan_detail(url):
    soup = get_soup(url)
    data = get_detail_data(url)
    return LegalDocument(
        title=data.get("Judul"),
        year=data.get("Tanggal Ditetapkan / Diundangkan", "")[:4],
        pdf_url=soup.select_one('a.btn[href*="unduh"]')['href'] if soup.select_one('a.btn[href*="unduh"]') else None,
        metadata=data
    )

def inspect_labels(url):
    soup = get_soup(url)
    for p in soup.select("div.tx-14 p"):
        strong = p.find("strong")
        if strong:
            label = strong.get_text(strip=True).rstrip(':')
            print(f"🔎 Ditemukan label: {label}")

if __name__ == "__main__":
    url = "https://jdih.komdigi.go.id/produk_hukum/view/id/954/t/keputusan+menteri+komunikasi+dan+digital+nomor+44+tahun+2025"
    data = get_detail_data(url)
    print("=== DETAIL DOKUMEN KOMINFO ===")
    for k, v in data.items():
        print(f"{k}: {v}")


