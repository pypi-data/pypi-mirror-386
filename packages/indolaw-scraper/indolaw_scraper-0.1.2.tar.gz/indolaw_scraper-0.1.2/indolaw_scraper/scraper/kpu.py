# scraper/kpu.py

import requests
from bs4 import BeautifulSoup
import json
from indolaw_scraper.models.document import LegalDocument

def scrape_kpu_regulation_detail(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    data = {}

    title_tag = soup.find('div', class_='card-body')
    if title_tag and title_tag.find('strong'):
        data['judul'] = title_tag.find('strong').get_text(strip=True)

    table = soup.find('table', class_='table table-hover')
    if table:
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) == 3:
                key = cols[0].get_text(strip=True).replace(' ', '_').replace('/', '_').lower()
                if key == 'keterangan_status':
                    p_tag = cols[2].find('p')
                    if p_tag:
                        data[key] = p_tag.get_text(separator=' ', strip=True)
                        mencabut_link = p_tag.find('a', href=True)
                        if mencabut_link:
                            data['url_peraturan_dicabut'] = mencabut_link['href']
                    else:
                        data[key] = cols[2].get_text(strip=True)
                else:
                    data[key] = cols[2].get_text(strip=True)

    status_box_value = soup.find('div', class_='status__box__value')
    if status_box_value:
        data['status_dokumen'] = status_box_value.get_text(strip=True)

    def extract_file_urls(header_text):
        file_data = {}
        all_mt4_divs = soup.find_all('div', class_='mt-4')
        for div in all_mt4_divs:
            if header_text in div.get_text(strip=True):
                links_div = div.find_next_sibling('div', class_='mt-2')
                if links_div:
                    preview_link = links_div.find('a', class_='link_preview')
                    if preview_link and 'data-src' in preview_link.attrs:
                        file_data['preview'] = preview_link['data-src']
                    download_link = links_div.find('a', href=True, target='_blank')
                    if download_link and ('download_abstrak' in download_link['href'] or '/download/' in download_link['href']):
                        file_data['download'] = download_link['href']
                break
        return file_data

    abstrak_files = extract_file_urls('Abstrak')
    if 'preview' in abstrak_files:
        data['url_abstrak_preview'] = abstrak_files['preview']
    if 'download' in abstrak_files:
        data['url_abstrak_download'] = abstrak_files['download']

    peraturan_files = extract_file_urls('File Peraturan')
    if 'preview' in peraturan_files:
        data['url_file_peraturan_preview'] = peraturan_files['preview']
    if 'download' in peraturan_files:
        data['url_file_peraturan_download'] = peraturan_files['download']

    return data

def map_kpu_data_to_legal_document_format(scraped_data: dict) -> dict:
    mapped_data = scraped_data.copy()

    if 'judul' in mapped_data:
        mapped_data['title'] = mapped_data.pop('judul')

    if 't.e.u_badan___pengarang' in mapped_data:
        mapped_data['teu_badan_pengarang'] = mapped_data.pop('t.e.u_badan___pengarang')

    # Hapus kunci yang tidak digunakan oleh LegalDocument
    for key in ['tipe_dokumen', 'jenis_dokumen', 'sumber', 'asal']:
        mapped_data.pop(key, None)

    return mapped_data

if __name__ == "__main__":
    url_to_scrape = "https://jdih.kpu.go.id/peraturan-kpu/detail/Gi_3l5EQx9OlPFcDpjEFMTNDc1VtNWU5YkhsZTZFUTVQVzJxZVE9PQ"
    scraped_data = scrape_kpu_regulation_detail(url_to_scrape)

    if scraped_data:
        mapped_data_for_legal_doc = map_kpu_data_to_legal_document_format(scraped_data)

        try:
            legal_document_instance = LegalDocument(**mapped_data_for_legal_doc)
            print("\n✅ Objek LegalDocument berhasil dibuat dan dipetakan:")
            if hasattr(legal_document_instance, 'to_dict'):
                print(json.dumps(legal_document_instance.to_dict(), indent=2, ensure_ascii=False))
            else:
                print(json.dumps(legal_document_instance.__dict__, indent=2, ensure_ascii=False))
        except TypeError as e:
            print(f"\n❌ Gagal membuat objek LegalDocument: {e}")
            print("Data yang dipetakan:")
            print(json.dumps(mapped_data_for_legal_doc, indent=2, ensure_ascii=False))
    else:
        print("Gagal mengambil atau mem-parse data dari URL.")

