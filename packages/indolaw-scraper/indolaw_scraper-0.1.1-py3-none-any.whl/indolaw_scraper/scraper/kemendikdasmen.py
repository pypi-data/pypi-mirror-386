# scraper/kemendikdasmen.py

import requests
from bs4 import BeautifulSoup
import urllib3
from indolaw_scraper.models.document import LegalDocument

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_soup(url):
    """Ambil objek BeautifulSoup dari URL"""
    res = requests.get(url, verify=False)
    return BeautifulSoup(res.text, 'html.parser')

def get_detail_value(soup, label_name):
    """Cari nilai dari tabel berdasarkan label"""
    for row in soup.select("table tr"):
        cols = row.find_all("td")
        if len(cols) >= 2 and label_name.lower() in cols[0].get_text(strip=True).lower():
            return cols[1].get_text(strip=True)
    return "N/A"

def get_detail_data(url):
    """Ekstrak semua data detail dari halaman peraturan"""
    soup = get_soup(url)
    labels = [
        "Tipe Dokumen", "Judul", "Tajuk Entri Utama", "Nomor", "Tahun", "Jenis",
        "Singkatan Jenis", "Tempat Penetapan", "Tanggal Penetapan", "Tanggal Pengundangan",
        "Sumber", "Nomor Sumber", "Status Peraturan", "Detail Status",
        "Bahasa", "Lokasi", "Bidang Hukum", "Subjek"
    ]

    data = {}
    for label in labels:
        data[label] = get_detail_value(soup, label)
    return data


def scrape_putusan_detail(url):
    """Scrape detail dokumen putusan (contoh struktur LegalDocument)"""
    soup = get_soup(url)
    return LegalDocument(
        title=soup.find('h1').text.strip(),
        year=get_detail_value(soup, "Tahun"),
        pdf_url=soup.select_one('a[href$=".pdf"]')['href']
    )

def get_putusan_links(base_url="https://jdih.kemendikdasmen.go.id/"):
    """Ambil semua link putusan dari halaman indeks"""
    soup = get_soup(f"{base_url}/putusan")
    return [a['href'] for a in soup.select('a.putusan-link')]

# --- BAGIAN INI HANYA AKAN JALAN KETIKA FILE INI DIEKSEKUSI LANGSUNG ---
if __name__ == "__main__":
    url = "https://jdih.kemendikdasmen.go.id/detail_peraturan?main=3527"
    data = get_detail_data(url)
    print("=== DETAIL DOKUMEN ===")
    for k, v in data.items():
        print(f"{k}: {v}")

        
        
