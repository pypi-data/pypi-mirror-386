# indolaw_scraper/marves.py 

import requests
from bs4 import BeautifulSoup
import urllib3
from indolaw_scraper.models.document import LegalDocument

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_soup(url):
    res = requests.get(url, verify=False, timeout=10)
    res.raise_for_status()
    return BeautifulSoup(res.text, 'html.parser')

def get_detail_data_marves(url):
    soup = get_soup(url)
    field_map = {
        "Tipe": "Tipe Dokumen",
        "Judul": "Judul",
        "T.E.U. Badan / Pengarang": "T.E.U Badan",
        "No. Peraturan": "Nomor Peraturan",
        "Jenis/Bentuk Peraturan": "Jenis/Bentuk Peraturan",
        "Singkatan Jenis/Bentuk Peraturan": "Singkatan Jenis/Bentuk Peraturan",
        "Tempat Penetapan": "Tempat Penetapan",
        "Tanggal-Bulan-Tahun Penetapan": "Tanggal Ditetapkan",
        "Tanggal-Bulan-Tahun Pengundangan": "Tanggal Diundangkan",
        "Sumber": "Sumber",
        "Subjek": "Subjek",
        "Status Peraturan": "Status",
        "Bahasa": "Bahasa",
        "Lokasi": "Lokasi",
        "Bidang Hukum": "Bidang Hukum",
        "Lampiran": "Lampiran",
    }

    data = {}
    for row in soup.select("div.content-page table tr"):
        cols = row.find_all("td")
        if len(cols) >= 2:
            label = cols[0].get_text(strip=True).rstrip(':')
            value = cols[1].get_text(separator=' ', strip=True)
            if label in field_map:
                data[field_map[label]] = value

    return data

def scrape_marves_detail(url):
    data = get_detail_data_marves(url)
    return LegalDocument(
        title=data.get("Judul"),
        year=data.get("Tahun") or data.get("Nomor Peraturan")[:4],  # fallback
        pdf_url=None  # tambahkan jika ada di page file/iframe
    )

# Test
if __name__ == "__main__":
    url = "https://jdih.maritim.go.id/uu-no-2-tahun-2024"  # ganti ID aktual
    d = get_detail_data_marves(url)
    for k, v in d.items():
        print(f"{k}: {v}")
        
        


