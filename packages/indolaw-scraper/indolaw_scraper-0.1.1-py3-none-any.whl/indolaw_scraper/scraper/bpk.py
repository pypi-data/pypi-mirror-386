import requests
from bs4 import BeautifulSoup
import urllib3
from indolaw_scraper.models.document import LegalDocument

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Connection': 'keep-alive',
}

def get_soup(url):
    try:
        res = requests.get(url, verify=False, timeout=10, headers=HEADERS)
        res.raise_for_status()
        return BeautifulSoup(res.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def get_detail_value_bpk(soup, label_name):
    rows = soup.select('div.row')
    for row in rows:
        label_div = row.find('div', class_='col-lg-3')
        value_div = row.find('div', class_='col-lg-9')
        if label_div and value_div:
            if label_name.lower() in label_div.get_text(strip=True).lower():
                return value_div.get_text(strip=True)
    return "N/A"

def get_detail_data(soup_or_url):
    soup = get_soup(soup_or_url) if isinstance(soup_or_url, str) else soup_or_url
    if not soup: return {}

    data = {}
    title_tag = soup.find('h3', class_='panel-title') or soup.find('title')
    data['Judul'] = title_tag.get_text(strip=True).replace(' - Database Peraturan | JDIH BPK', '') if title_tag else "N/A"

    labels = [
        "Nomor", "Tahun", "T.E.U. Badan / Pengarang", "Tipe Dokumen", "Bentuk",
        "Singkatan Bentuk", "Tempat Penetapan", "Tanggal Penetapan", "Tanggal Pengundangan",
        "Tanggal Berlaku", "Sumber", "Subjek", "Status", "Bahasa", "Bidang Hukum"
    ]

    for label in labels:
        data[label] = get_detail_value_bpk(soup, label)

    return data

if __name__ == "__main__":
    url = "https://peraturan.bpk.go.id/Details/227490/peraturan-kpk-no-5-tahun-2018"
    print(f"--- SCRAPE: {url} ---")
    result = get_detail_data(url)
    print("=== DETAIL DOKUMEN BPK ===")
    for k, v in result.items():
        print(f"{k}: {v}")

