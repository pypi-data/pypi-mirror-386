# indolaw_scraper/sources/itb.py


from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from indolaw_scraper.models.document import LegalDocument

BASE_URL = "https://jdih.itb.ac.id"

def get_soup(url: str) -> BeautifulSoup:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def scrape_itb_detail(url: str) -> LegalDocument:
    soup = get_soup(url)
    metadata = {}
    
    # Coba beberapa pola selector yang mungkin
    # Pola 1: Untuk metadata di card-body
    for row in soup.select(".card-body .row"):
        cols = row.select("div.col-md-4, div.col-md-8")
        if len(cols) == 2:
            key = cols[0].get_text(strip=True).replace(":", "")
            val = cols[1].get_text(strip=True)
            metadata[key] = val
    
    # Pola 2: Untuk tabel metadata
    if not metadata:
        for row in soup.select("table tr"):
            cols = row.select("td")
            if len(cols) == 2:
                key = cols[0].get_text(strip=True).replace(":", "")
                val = cols[1].get_text(strip=True)
                metadata[key] = val
    
    # Debug: Cetak metadata yang ditemukan
    print("Metadata extracted:", metadata)
    
    # Ambil file PDF
    pdf_url = None
    pdf_btn = soup.find("a", href=lambda x: x and x.endswith(".pdf"))
    if pdf_btn:
        pdf_url = urljoin(BASE_URL, pdf_btn["href"])
    
    # Ambil judul dari tag h2 atau h3 jika ada
    title = soup.select_one("h2, h3")
    if title:
        metadata["Judul"] = title.get_text(strip=True)
    
    return LegalDocument(
        title=metadata.get("Judul"),
        tahun=metadata.get("Tahun") or (metadata.get("Tanggal Penetapan")[:4] if metadata.get("Tanggal Penetapan") else None),
        nomor=metadata.get("Nomor"),
        jenis=metadata.get("Jenis"),
        bentuk=metadata.get("Bentuk Peraturan"),
        tanggal_ditetapkan=metadata.get("Tanggal Penetapan"),
        pemrakarsa=metadata.get("Pemrakarsa"),
        pdf_url=pdf_url,
        lokasi="Institut Teknologi Bandung",
        sumber="JDIH ITB",
    )

# Contoh penggunaan
if __name__ == "__main__":
    doc = scrape_itb_detail("https://jdih.itb.ac.id/detail/81a5659cadae764d2cea250c130164a2")
    print("\n=== HASIL SCRAPING ===")
    print(doc.to_dict())
    
    
