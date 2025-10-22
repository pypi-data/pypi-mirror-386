# scraper/pertanian.py

from indolaw_scraper.models.document import LegalDocument
import requests
from bs4 import BeautifulSoup
import urllib3

# Nonaktifkan peringatan SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_soup(url):
    """Ambil objek BeautifulSoup dari URL"""
    try:
        res = requests.get(url, verify=False, timeout=10)
        res.raise_for_status()  # Cek status HTTP
        return BeautifulSoup(res.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def get_detail_value(soup, label_name):
    """
    Ambil nilai dari tabel 3 kolom di JDIH Kementerian Pertanian.
    Kolom ke-1: label, ke-3: value.
    """
    for row in soup.select("table tr"):
        th = row.find("th")
        tds = row.find_all("td")
        if th and len(tds) >= 2:
            if label_name.lower() in th.get_text(strip=True).lower():
                return tds[1].get_text(strip=True)  # Kolom ke-3 (index ke-1 karena kolom ke-2 = ":")
    return "N/A"


def get_detail_data(url):
    """Ekstrak semua data detail dari halaman peraturan"""
    soup = get_soup(url)
    if not soup:
        return {}  # Kembalikan dict kosong bukan None
    
    labels = [
        "Tipe Dokumen", "Judul", "T.E.U Badan", "Nomor Peraturan", 
        "Jenis/Bentuk Peraturan", "Singkatan Jenis/Bentuk Peraturan", 
        "Tempat Penetapan", "Tanggal Ditetapkan", "Tanggal Diundangkan", 
        "Sumber", "Subjek", "Status", "Bahasa", "Lokasi", 
        "Bidang Hukum", "Tematik", "Tahun"  # Ditambahkan Tahun
    ]
    
    data = {}
    for label in labels:
        data[label] = get_detail_value(soup, label)
    
    return data

def scrape_putusan_detail(url):
    """Scrape detail dokumen putusan (contoh struktur LegalDocument)"""
    soup = get_soup(url)
    if not soup:
        return None
        
    return LegalDocument(
        title=get_detail_value(soup, "Judul") or soup.find('h1').text.strip(),
        year=get_detail_value(soup, "Tahun"),
        pdf_url=soup.select_one('a[href$=".pdf"]')['href'] if soup.select_one('a[href$=".pdf"]') else None
    )

def get_putusan_links(base_url="https://jdih.pertanian.go.id/front"):
    """Ambil semua link putusan dari halaman indeks"""
    soup = get_soup(f"{base_url}/putusan")
    if not soup:
        return []
        
    return [a['href'] for a in soup.select('a.putusan-link') if a.has_attr('href')]

if __name__ == "__main__":
    test_url = "https://jdih.pertanian.go.id/fp/peraturan/detail/1313/Peraturan-Menteri-Pertanian-Nomor-13-Tahun-2024-tentang-Pembelian-Tandan-Buah-Segar-Kelapa-Sawit-Produksi-Pekebun-Mitra"
    data = get_detail_data(test_url)
    
    if data:  # Cek jika data tidak kosong
        print("=== DETAIL DOKUMEN ===")
        max_len = max(len(k) for k in data.keys()) + 2
        for k, v in data.items():
            print(f"{k.ljust(max_len)}: {v}")
    else:
        print("Gagal mengambil data atau data kosong")
