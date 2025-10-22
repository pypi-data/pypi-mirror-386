# scraper/mahkamah_agung.py

import requests
from bs4 import BeautifulSoup
import urllib3
from indolaw_scraper.models.document import LegalDocument

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================
# Scrape untuk Satu Dokumen
# =============================

def get_soup(url):
    """Ambil objek BeautifulSoup dari URL"""
    res = requests.get(url, verify=False)
    return BeautifulSoup(res.text, 'html.parser')

def get_detail_value(soup, label_name):
    """Helper untuk mengambil nilai dari label tertentu"""
    el = soup.find(string=label_name)
    if el:
        next_el = el.find_next()
        return next_el.get_text(strip=True) if next_el else "N/A"
    return "N/A"

def get_detail_data(url):
    """Extract all detailed data from the regulations page"""
    soup = get_soup(url)
    labels = [
        "Judul", "Nomor", "Tahun", "Jenis", "Singkatan Jenis",
        "Tanggal Ditetapkan", "Tanggal Diundangkan", "Penandatangan",
        "Pemrakarsa", "Sumber", "T.E.U.", "Tempat Penetapan", "Lokasi",
        "Bahasa", "Bidang Hukum", "Urusan Pemerintah", "Subjek", "Status"
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

def get_putusan_links(base_url="https://jdih.mahkamahagung.go.id"):
    """Fetch all ruling links from index page"""
    soup = get_soup(f"{base_url}/putusan")
    return [a['href'] for a in soup.select('a.putusan-link')]

# --- THIS PART WILL ONLY RUN WHEN THIS FILE IS EXECUTED DIRECTLY ---
if __name__ == "__main__":
    url = "https://jdih.mahkamahagung.go.id/legal-product/perma-nomor-1-tahun-2025/detail"
    data = get_detail_data(url)
    print("=== DETAIL DOKUMEN ===")
    for k, v in data.items():
        print(f"{k}: {v}")



# =============================
# Scrape Banyak Dokumen
# =============================
import requests
from bs4 import BeautifulSoup

BASE = "https://jdih.mahkamahagung.go.id/"

def get_soup(url):
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")

def get_all_perma_entries():
    url = f"{BASE}/dokumen-hukum/peraturan-perundang-undangan/PERMA"
    soup = get_soup(url)
    articles = soup.select("article.blog_item")
    entries = []

    for art in articles:
        title = art.select_one("h2").get_text(strip=True)
        link = art.select_one("a.d-inline-block")["href"]
        full_link = link if link.startswith("http") else BASE + link
        desc = art.select_one("p").get_text(strip=True)
        items = art.select("ul.blog-info-link li")
        tanggal = items[0].get_text(strip=True) if len(items) > 0 else "N/A"

        pdf_link = None
        for a in art.select("a"):
            onclick = a.get("onclick", "")
            if "onClick(" in onclick and "perma" in onclick.lower():
                perma_id = onclick.split("'")[1]
                pdf_link = f"{BASE}/pdf/{perma_id}.pdf"

        entries.append({
            "Judul": desc,
            "Nomor": title.split("NOMOR")[-1].split("TAHUN")[0].strip(),
            "Tahun": title.split("TAHUN")[-1].strip(),
            "Jenis": "Peraturan Mahkamah Agung",
            "Singkatan Jenis": "PERMA",
            "Tanggal Ditetapkan": tanggal,
            "Sumber": "JDIH Mahkamah Agung",
            "Link Detail": full_link,
            "PDF": pdf_link
        })

    return entries

def scrape_all_perma():
    print("🔎 Mengambil semua PERMA Mahkamah Agung...")
    docs = get_all_perma_entries()
    print(f"✅ Ditemukan {len(docs)} dokumen (coba tampilkan 5)")
    for i, doc in enumerate(docs[:3], 1):
        print(f"\n📄 [{i}] {doc['Link Detail']}")
        print("=== DETAIL DOKUMEN MAHKAMAH AGUNG ===")
        for key in [
            "Judul", "Nomor", "Tahun", "Jenis", "Singkatan Jenis",
            "Tanggal Ditetapkan", "Sumber", "PDF"
        ]:
            print(f"{key}: {doc.get(key, '-')}")


# =============================
# Main Executor
# =============================
if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "one":
        # ex URL adjustment according to the needs
        sample_url = "https://jdih.mahkamahagung.go.id/dokumen-hukum/peraturan-perundang-undangan/PERMA"
        scrape_perma_single(sample_url)
    else:
        scrape_all_perma()


