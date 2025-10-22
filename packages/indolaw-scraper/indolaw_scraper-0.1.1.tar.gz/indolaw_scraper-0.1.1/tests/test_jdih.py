
from indolaw_scraper.scraper.mahkamah_agung import get_detail_data

if __name__ == "__main__":
    url = "https://jdih.mahkamahagung.go.id/legal-product/se-sekma-nomor-4-tahun-2025/detail"
    data = get_detail_data(url)
    print("=== DETAIL DOKUMEN ===")
    for k, v in data.items():
        print(f"{k}: {v}")
