# cli.py
import click
import json

# Import semua scraper dengan alias konsisten
from indolaw_scraper.models.document import LegalDocument
from indolaw_scraper.scraper.mahkamah_agung import get_detail_data as scrape_ma
from indolaw_scraper.scraper.kpu import (
    scrape_kpu_regulation_detail,
    map_kpu_data_to_legal_document_format,
)
from indolaw_scraper.scraper.bpk import get_detail_data as scrape_bpk
from indolaw_scraper.scraper.kemendikdasmen import get_detail_data as scrape_kemendikdasmen
from indolaw_scraper.scraper.kementan import get_detail_data as scrape_kementan
from indolaw_scraper.scraper.kkp import get_detail_data_kkp as scrape_kkp
from indolaw_scraper.scraper.kemenkeu import get_detail_data as scrape_kemenkeu
from indolaw_scraper.scraper.kominfo import get_detail_data as scrape_kominfo
from indolaw_scraper.scraper.marves import get_detail_data_marves as scrape_marves
from indolaw_scraper.scraper.kemendag import get_kemendag_data as scrape_kemendag
from indolaw_scraper.scraper.kemenpora import scrape_kemenpora_detail
from indolaw_scraper.scraper.pu import scrape_pu_detail
from indolaw_scraper.scraper.kehutanan import scrape_forestry_document as scrape_kehutanan
from indolaw_scraper.scraper.itb import scrape_itb_detail


@click.command()
@click.option(
    '--source',
    required=True,
    help='Sumber dokumen: ma, kpu, kemendikbud, kementan, kkp, bpk, kemenkeu, kominfo, marves, pu, kemenpora, kehutanan, itb'
)
@click.option('--url', required=True, help='URL detail dokumen yang ingin di-scrape')
def main(source, url):
    """Command Line Interface for IndoLaw Scraper"""
    try:
        if source == "ma":
            data = scrape_ma(url)

        elif source == "kpu":
            raw = scrape_kpu_regulation_detail(url)
            if raw:
                mapped = map_kpu_data_to_legal_document_format(raw)
                data = LegalDocument(**mapped).to_dict()
            else:
                raise ValueError("Gagal mengambil data dari KPU.")

        elif source == "kemendikbud":
            data = scrape_kemendikdasmen(url)

        elif source == "kementan":
            data = scrape_kementan(url)

        elif source == "kkp":
            data = scrape_kkp(url)

        elif source == "bpk":
            data = scrape_bpk(url)

        elif source == "kemenkeu":
            data = scrape_kemenkeu(url)

        elif source == "kominfo":
            data = scrape_kominfo(url)

        elif source == "marves":
            data = scrape_marves(url)

        elif source == "pu":
            data = scrape_pu_detail(url)

        elif source == "kemenpora":
            data = scrape_kemenpora_detail(url)

        elif source == "kehutanan":
            data = scrape_kehutanan(url)

        elif source == "itb":
            data = scrape_itb_detail(url)

        else:
            raise ValueError("Sumber dokumen tidak dikenali.")

        click.secho(f"\n=== DETAIL DOKUMEN {source.upper()} ===", fg="green", bold=True)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    except Exception as e:
        click.secho(f"❌ Terjadi kesalahan: {e}", fg="red")


if __name__ == "__main__":
    main()


