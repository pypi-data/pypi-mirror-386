# indolaw_scraper/sources/kemenpora.py

import requests
from bs4 import BeautifulSoup
from indolaw_scraper.models.document import LegalDocument

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://jdih.kemenpora.go.id/",
}


def get_soup(url):
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    return BeautifulSoup(res.content, 'html.parser')

def scrape_kemenpora_detail(url):
    soup = get_soup(url)
    data = {}

    # Ambil baris tabel metadata
    rows = soup.select("table.left_head tr")
    for row in rows:
        th = row.find("th")
        td = row.find("td")
        if th and td:
            label = th.get_text(strip=True)
            value = td.get_text(strip=True)
            data[label] = value

    # Tambahkan URL dokumen dan PDF jika ada
    pdf_preview = soup.select_one("a[href$='.pdf'][id='btn-lihat']")
    pdf_download = soup.select_one("a[href$='.pdf'][id='btn-unduh']")
    data["url_preview"] = pdf_preview["href"] if pdf_preview else None
    data["url_download"] = pdf_download["href"] if pdf_download else None
    data["url"] = url

    return data

if __name__ == "__main__":
    test_url = "https://jdih.kemenpora.go.id/produk_hukum/detail/755/keputusan-menteri-pemuda-dan-olahraga-republik-indonesia-nomor-105-tahun-2025-tentang-penetapan-pemerintah-provinsi-daerah-khusus-ibukota-jakarta-sebagai-tuan-rumah-penyelenggara-pekan-olahraga-pelajar-nasional-xvii-dan-pekan-paralimpik-pelajar-nasional-xi-tahun-2025.html"
    result = scrape_kemenpora_detail(test_url)
    print("=== DETAIL DOKUMEN KEMENPORA ===")
    for k, v in result.items():
        print(f"{k}: {v}")
