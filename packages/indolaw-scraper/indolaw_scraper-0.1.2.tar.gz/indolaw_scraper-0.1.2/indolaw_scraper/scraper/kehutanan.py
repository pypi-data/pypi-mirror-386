#indolaw_scraper/scraper/kehutanan.py

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin
from indolaw_scraper.models.document import LegalDocument


@dataclass
class ForestryDocument:
    document_type: str
    title: str
    author: str
    number: str
    regulation_type: str
    abbreviation: str
    enactment_place: str
    enactment_date: str
    promulgation_date: str
    source: str
    subject: str
    status: str
    language: str
    location: str
    legal_field: str
    attachment: str
    initiator: str
    pdf_url: Optional[str]
    abstract_url: Optional[str]

def scrape_forestry_document(url: str) -> Optional[ForestryDocument]:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "id-ID,id;q=0.9"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        def get_table_value(label: str) -> str:
            rows = soup.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3 and cells[0].get_text(strip=True) == label:
                    return cells[2].get_text(strip=True)
            return "N/A"

        def extract_onclick_url(attr: str) -> Optional[str]:
            link = soup.find('a', {'onclick': lambda x: x and attr in x})
            if link and 'onclick' in link.attrs:
                parts = link['onclick'].split("'")
                if len(parts) > 1:
                    return urljoin(url, parts[1])
            return None

        pdf_url = extract_onclick_url('open_indonesia_file')
        abstract_url = extract_onclick_url('open_indonesia_abstrak')

        return ForestryDocument(
            document_type=get_table_value("Tipe"),
            title=get_table_value("Judul"),
            author=get_table_value("T.E.U Badan/Pengarang"),
            number=get_table_value("No. Peraturan"),
            regulation_type=get_table_value("Jenis/Bentuk Peraturan"),
            abbreviation=get_table_value("Singkatan Jenis/Bentuk Peraturan"),
            enactment_place=get_table_value("Tempat Penetapan"),
            enactment_date=get_table_value("Tanggal-Bulan-Tahun Penetapan"),
            promulgation_date=get_table_value("Tanggal-Bulan-Tahun Pengundangan"),
            source=get_table_value("Sumber"),
            subject=get_table_value("Subjek"),
            status=get_table_value("Status Peraturan"),
            language=get_table_value("Bahasa"),
            location=get_table_value("Lokasi"),
            legal_field=get_table_value("Bidang Hukum"),
            attachment=get_table_value("Lampiran"),
            initiator=get_table_value("Pemrakarsa"),
            pdf_url=pdf_url,
            abstract_url=abstract_url
        )

    except Exception as e:
        print(f"[ERROR] {e}")
        return None

# Tes
if __name__ == "__main__":
    test_url = "https://jdih.menlhk.go.id/new2/home/portfolioDetails2/PERPRES_34_2025.pdf/34/2025/3"
    doc = scrape_forestry_document(test_url)
    if doc:
        print("=== DETAIL DOKUMEN KEHUTANAN ===")
        for k, v in doc.__dict__.items():
            print(f"{k}: {v}")
    else:
        print("Gagal melakukan scraping dokumen.")

