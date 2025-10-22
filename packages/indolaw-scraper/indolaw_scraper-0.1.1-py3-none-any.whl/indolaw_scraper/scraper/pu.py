# indolaw_scraper/scraper/pu.py


# indolaw_scraper/scraper/pu.py

from bs4 import BeautifulSoup
import requests
import urllib3
from dataclasses import dataclass
from typing import Optional
from indolaw_scraper.models.document import LegalDocument

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class PUDocument:
    document_type: str
    title: str
    author: str
    document_number: str
    regulation_type: str
    regulation_abbreviation: str
    enactment_place: str
    enactment_date: str
    source: str
    subject: str
    status: str
    language: str
    location: str
    legal_field: str
    abstract: Optional[str] = None
    abstract_url: Optional[str] = None
    full_text_url: Optional[str] = None
    download_count: Optional[int] = None
    view_count: Optional[int] = None
    publish_date: Optional[str] = None

class PUScraper:
    BASE_URL = "https://jdih.pu.go.id"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def get_soup(self, url: str) -> BeautifulSoup:
        try:
            response = self.session.get(url, verify=False, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def scrape_document(self, url: str) -> Optional[PUDocument]:
        soup = self.get_soup(url)
        if not soup:
            return None

        metadata = {}
        rows = soup.select('table.table-striped tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                metadata[key] = value

        publish_info = soup.select_one('.tab-pane p i')
        download_count = view_count = publish_date = None
        if publish_info:
            publish_text = publish_info.get_text()
            parts = [p.strip() for p in publish_text.split('|')]
            for part in parts:
                if 'download' in part.lower():
                    download_count = int(''.join(filter(str.isdigit, part)))
                elif 'eye' in part.lower():
                    view_count = int(''.join(filter(str.isdigit, part)))
                elif any(m in part.lower() for m in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep']):
                    publish_date = part.split()[-1]

        abstract_url = full_text_url = None
        abstract_input = soup.find('input', {'id': 'path_abstrak'})
        full_text_input = soup.find('input', {'id': 'path_upload'})

        if abstract_input:
            abstract_url = f"{self.BASE_URL}/internal/assets/assets/produk/{abstract_input['value']}"
        if full_text_input:
            full_text_url = f"{self.BASE_URL}/internal/assets/assets/produk/{full_text_input['value']}"

        return PUDocument(
            document_type=metadata.get('Tipe Dokumen', 'N/A'),
            title=metadata.get('Judul', 'N/A'),
            author=metadata.get('T.E.U. Badan / Pengarang', 'N/A'),
            document_number=metadata.get('Nomor', 'N/A'),
            regulation_type=metadata.get('Jenis Peraturan', 'N/A'),
            regulation_abbreviation=metadata.get('Singkatan Jenis', 'N/A'),
            enactment_place=metadata.get('Tempat Penetapan', 'N/A'),
            enactment_date=metadata.get('Tanggal Ditetapkan', 'N/A'),
            source=metadata.get('Sumber', 'N/A'),
            subject=metadata.get('Subjek', 'N/A'),
            status=metadata.get('Status', 'N/A'),
            language=metadata.get('Bahasa', 'N/A'),
            location=metadata.get('Lokasi', 'N/A'),
            legal_field=metadata.get('Bidang Hukum', 'N/A'),
            abstract=metadata.get('Abstrak', None),
            abstract_url=abstract_url,
            full_text_url=full_text_url,
            download_count=download_count,
            view_count=view_count,
            publish_date=publish_date
        )

    def scrape_document_list(self, list_url: str) -> list:
        soup = self.get_soup(list_url)
        if not soup:
            return []

        documents = []
        items = soup.select('#div_produk_hukum .list-item')
        for item in items:
            title = item.select_one('h3 a')
            if title:
                doc_url = title['href']
                if not doc_url.startswith('http'):
                    doc_url = self.BASE_URL + doc_url
                documents.append(doc_url)
        return documents

# ✅ Fungsi wrapper yang bisa diimport dari luar
def scrape_pu_detail(url: str):
    scraper = PUScraper()
    return scraper.scrape_document(url)


# Example usage
if __name__ == "__main__":
    scraper = PUScraper()
    
    # Example document URL
    doc_url = "https://jdih.pu.go.id/detail-dokumen/SESekjenPU-nomor-5SESJ2025-tahun-2025-Penamaan-Unit-Pelaksana-Teknis-dan-Kode-Identifikasi-Otoritas-Pejabat-Penanda-Tangan-Naskah-Dinas-bagi-Pimpinan-Unit-Pelaksana-Teknis"
    document = scraper.scrape_document(doc_url)
    
    if document:
        print("=== DOCUMENT DETAILS ===")
        print(f"Title: {document.title}")
        print(f"Number: {document.document_number}")
        print(f"Type: {document.regulation_type} ({document.regulation_abbreviation})")
        print(f"Enactment Date: {document.enactment_date}")
        print(f"Status: {document.status}")
        print(f"Full Text URL: {document.full_text_url}")
        print(f"Download Count: {document.download_count}")
        print(f"View Count: {document.view_count}")
    else:
        print("Failed to scrape document")


  

