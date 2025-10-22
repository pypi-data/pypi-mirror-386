# scraper/kemenkeu.py

import requests
from bs4 import BeautifulSoup
import urllib3
from indolaw_scraper.models.document import LegalDocument


# =============================
        # Scrape untuk Satu Dokumen
# =============================

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_soup(url):
    res = requests.get(url, verify=False)
    return BeautifulSoup(res.text, 'html.parser')

def get_detail_data(url):
    soup = get_soup(url)
    
    field_map = {
        "Kode": "Nomor Peraturan",
        "Judul/Tentang": "Judul",
        "Nomor": "Nomor",
        "Tahun": "Tahun",
        "Jenis": "Jenis/Bentuk Peraturan",
        "Tajuk Entri Utama": "T.E.U Badan",
        "Bidang": "Bidang Hukum",
        "Subyek": "Subjek",
        "Penetapan": "Tanggal Ditetapkan",
        "Pengundangan": "Tanggal Diundangkan",
        "Tgl. Berlaku": "Tanggal Berlaku",
        "Tempat Terbit": "Tempat Penetapan",
        "Sumber": "Sumber",
        "Lokasi": "Lokasi"
    }

    data = {}
    for row in soup.select('.row.dok-item'):
        label_el = row.select_one('.col-4')
        value_el = row.select_one('.col-8')
        if label_el and value_el:
            label = label_el.get_text(strip=True)
            value = value_el.get_text(strip=True).replace('\n', ' ').strip()
            if label in field_map:
                data[field_map[label]] = value

    return data

def scrape_putusan_detail(url):
    soup = get_soup(url)
    return LegalDocument(
        title=get_detail_data(url).get("Judul"),
        year=get_detail_data(url).get("Tahun"),
        pdf_url=soup.select_one('a[href$=".pdf"]')['href'] if soup.select_one('a[href$=".pdf"]') else None
    )

# Test
if __name__ == "__main__":
    url = "https://jdih.kemenkeu.go.id/dok/-kep-173-bc-2025"
    data = get_detail_data(url)
    print("=== DETAIL DOKUMEN KEMENKEU ===")
    for k, v in data.items():
        print(f"{k}: {v}")
        
        
        

# =============================
# Scrape Banyak Dokumen
# =============================

import requests
from bs4 import BeautifulSoup
import urllib3
from indolaw_scraper.models.document import LegalDocument

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://jdih.kemenkeu.go.id"

def get_soup(url):
    """Ambil dan parsing HTML dari sebuah URL"""
    res = requests.get(url, verify=False)
    return BeautifulSoup(res.text, 'html.parser')

def get_all_kemenkeu_links(page=1):
    """Ambil semua link dokumen dari halaman pencarian (default: halaman pertama)"""
    index_url = f"{BASE_URL}/search?order=desc&page={page}"
    soup = get_soup(index_url)
    links = []
    for a in soup.select('a[href^="/dok/"]'):
        href = a.get('href')
        if href:
            full_url = BASE_URL + href
            if full_url not in links:
                links.append(full_url)
    return links

def get_detail_data(url):
    """Ambil metadata detail dari halaman dokumen"""
    soup = get_soup(url)
    field_map = {
        "Kode": "Nomor Peraturan",
        "Judul/Tentang": "Judul",
        "Nomor": "Nomor",
        "Tahun": "Tahun",
        "Jenis": "Jenis/Bentuk Peraturan",
        "Tajuk Entri Utama": "T.E.U Badan",
        "Bidang": "Bidang Hukum",
        "Subyek": "Subjek",
        "Penetapan": "Tanggal Ditetapkan",
        "Pengundangan": "Tanggal Diundangkan",
        "Tgl. Berlaku": "Tanggal Berlaku",
        "Tempat Terbit": "Tempat Penetapan",
        "Sumber": "Sumber",
        "Lokasi": "Lokasi"
    }

    data = {}
    for row in soup.select('.row.dok-item'):
        label_el = row.select_one('.col-4')
        value_el = row.select_one('.col-8')
        if label_el and value_el:
            label = label_el.get_text(strip=True)
            value = value_el.get_text(strip=True).replace('\n', ' ').strip()
            if label in field_map:
                data[field_map[label]] = value
    return data

def scrape_putusan_detail(url):
    """Bangun model LegalDocument dari sebuah halaman dokumen"""
    soup = get_soup(url)
    data = get_detail_data(url)
    pdf_el = soup.select_one('a[href$=".pdf"]')
    return LegalDocument(
        title=data.get("Judul"),
        year=data.get("Tahun"),
        pdf_url=pdf_el["href"] if pdf_el else None
    )

# =========================
# MAIN TEST
# =========================
if __name__ == "__main__":
    print("🔎 Mengambil semua link peraturan dari Kementerian Keuangan ...")
    links = get_all_kemenkeu_links()

    print(f"✅ Ditemukan {len(links)} dokumen (contoh 5 ditampilkan):")
    for i, url in enumerate(links[:5], 1):
        print(f"\n📄 [{i}] {url}")
        try:
            data = get_detail_data(url)
            for k, v in data.items():
                print(f"{k}: {v}")
        except Exception as e:
            print(f"❌ Gagal memproses {url}: {e}")

