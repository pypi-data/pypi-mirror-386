# indolaw_scraper/indolaw_scraper/models/document.py
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class LegalDocument:
    # --- Atribut Umum ---
    title: str
    tahun: Optional[str] = None
    nomor: Optional[str] = None
    jenis: Optional[str] = None
    singkatan_jenis: Optional[str] = None
    tipe_dokumen: Optional[str] = None
    bentuk: Optional[str] = None
    singkatan_bentuk: Optional[str] = None

    # --- Tanggal & Penetapan ---
    tanggal_ditetapkan: Optional[str] = None
    tanggal_diundangkan: Optional[str] = None
    tanggal_berlaku: Optional[str] = None
    tempat_penetapan: Optional[str] = None
    penandatangan: Optional[str] = None

    # --- Identitas Lembaga & Pengarang ---
    pemrakarsa: Optional[str] = None
    teu_badan_pengarang: Optional[str] = None
    lokasi: Optional[str] = None

    # --- Metadata Tambahan ---
    sumber: Optional[str] = None
    nomor_sumber: Optional[str] = None
    bahasa: Optional[str] = None
    bidang_hukum: Optional[str] = None
    urusan_pemerintah: Optional[str] = None
    subjek: Optional[str] = None
    status: Optional[str] = None
    detail_status: Optional[str] = None

    # --- File atau Link ---
    pdf_url: Optional[str] = None
    url_abstrak_preview: Optional[str] = None
    url_abstrak_download: Optional[str] = None
    url_file_peraturan_preview: Optional[str] = None
    url_file_peraturan_download: Optional[str] = None
    url_peraturan_dicabut: Optional[str] = None

    # --- Metode untuk bantu konversi ke dict ---
    def to_dict(self):
        return asdict(self)

def build_legal_document(metadata: dict, url: str = None, file_url: str = None, pemrakarsa: str = None) -> LegalDocument:
    return LegalDocument(
        # --- Atribut Umum ---
        title=metadata.get("Judul", ""),
        nomor=metadata.get("Nomor", ""),
        tahun=metadata.get("Tanggal Penetapan", "").split("-")[-1] if metadata.get("Tanggal Penetapan") else None,
        jenis=metadata.get("Jenis", ""),
        tipe_dokumen=metadata.get("Tipe Dokumen", ""),
        bentuk=metadata.get("Bentuk", ""),

        # --- Tanggal & Penetapan ---
        tanggal_ditetapkan=metadata.get("Tanggal Penetapan", ""),
        tanggal_diundangkan=metadata.get("Tanggal Pengundangan", ""),
        tanggal_berlaku=metadata.get("Tanggal Berlaku", ""),
        tempat_penetapan=metadata.get("Tempat Penetapan", ""),
        penandatangan=metadata.get("Penandatangan", ""),

        # --- Identitas ---
        pemrakarsa=pemrakarsa or metadata.get("Pemrakarsa", ""),
        teu_badan_pengarang=metadata.get("Pengarang", ""),
        lokasi=metadata.get("Lokasi", ""),

        # --- Metadata tambahan ---
        sumber=metadata.get("Sumber", ""),
        nomor_sumber=metadata.get("Nomor Sumber", ""),
        bahasa=metadata.get("Bahasa", ""),
        bidang_hukum=metadata.get("Bidang Hukum", ""),
        urusan_pemerintah=metadata.get("Urusan Pemerintah", ""),
        subjek=metadata.get("Subjek", ""),
        status=metadata.get("Status", ""),
        detail_status=metadata.get("Detail Status", ""),

        # --- Link dan File ---
        pdf_url=file_url,
        url_abstrak_preview=url,
        url_abstrak_download=metadata.get("URL Abstrak Download", ""),
        url_file_peraturan_preview=metadata.get("URL Dokumen Preview", ""),
        url_file_peraturan_download=metadata.get("URL Dokumen Download", ""),
        url_peraturan_dicabut=metadata.get("URL Peraturan Dicabut", "")
    )

