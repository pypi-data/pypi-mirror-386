#scraper/kkp.py

#perikanan.py

import requests
from bs4 import BeautifulSoup
import urllib3
from indolaw_scraper.models.document import LegalDocument

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_soup(url):
    """Ambil objek BeautifulSoup dari URL"""
    res = requests.get(url, verify=False)
    return BeautifulSoup(res.text, 'html.parser')

def get_detail_value_kkp(soup, label_name):
    """
    Ambil nilai dari tabel 3 kolom di JDIH KKP.
    Kolom ke-1: label, kolom ke-3: nilai.
    """
    for row in soup.select("table tr"):
        tds = row.find_all("td")
        if len(tds) >= 3 and label_name.lower() in tds[0].get_text(strip=True).lower():
            return tds[2].get_text(strip=True)
    return "N/A"


def get_detail_data_kkp(url):
    """Ekstrak semua data dari halaman detail JDIH KKP"""
    soup = get_soup(url)
    if not soup:
        return {}

    # Mapping label HTML -> label standar output
    labels = {
        "Jenis Peraturan": "Jenis/Bentuk Peraturan",
        "Nomor": "Nomor Peraturan",
        "Tahun": "Tahun",
        "Judul": "Judul",
        "T.E.U": "T.E.U Badan",
        "Singkatan Jenis": "Singkatan Jenis/Bentuk Peraturan",
        "Tempat Terbit": "Tempat Penetapan",
        "Tanggal Penetapan": "Tanggal Ditetapkan",
        "Tanggal Pengundangan": "Tanggal Diundangkan",
        "Subjek": "Subjek",
        "Status": "Status",
        "Sumber": "Sumber",
        "Bahasa": "Bahasa",
        "Lokasi": "Lokasi",
        "Bidang Hukum": "Bidang Hukum",
        "Keterangan": "Keterangan"
    }

    data = {}
    for label_html, label_output in labels.items():
        data[label_output] = get_detail_value_kkp(soup, label_html)

    return data


def scrape_putusan_detail(url):
    """Scrape detail dokumen putusan (contoh struktur LegalDocument)"""
    soup = get_soup(url)
    return LegalDocument(
        title=soup.find('h1').text.strip(),
        year=get_detail_value(soup, "Tahun"),
        pdf_url=soup.select_one('a[href$=".pdf"]')['href']
    )

def get_putusan_links(base_url="https://jdih.kkp.go.id"):
    """Ambil semua link putusan dari halaman indeks"""
    soup = get_soup(f"{base_url}/putusan")
    return [a['href'] for a in soup.select('a.putusan-link')]

# --- BAGIAN INI HANYA AKAN JALAN KETIKA FILE INI DIEKSEKUSI LANGSUNG ---
if __name__ == "__main__":
    url = "https://jdih.kkp.go.id/Homedev/DetailPeraturan/6523"
    data = get_detail_data_kkp(url)
    print("=== DETAIL DOKUMEN KKP ===")
    for k, v in data.items():
        print(f"{k}: {v}")

        
        
        
        
        
