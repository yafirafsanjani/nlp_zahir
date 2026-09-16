"""
normalization.py - Normalisasi Bahasa Chat (Fase 11)
Metode Berjenjang (Cascaded Normalization):
- Layer 0: Proteksi Domain Whitelist Zahir (Zero Distortion)
- Layer 1: Korpus Resmi Library indo-normalizer (1.284+ entri slang)
- Layer 2: Reduksi Huruf Berulang (Elongated Words Reduction)
- Layer 3: Kamus Dialek Chat WhatsApp & Typo Lokal
- Layer 4: Kamus Domain Spesifik Zahir & Akuntansi
"""

import csv
import re
from pathlib import Path
from collections import Counter
import indo_normalizer

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "chat_preprocessed.csv"
OUTPUT_FILE = PROCESSED_DIR / "chat_normalized.csv"

# ----------------------------------------------------
# LAYER 0: DOMAIN WHITELIST ZAHIR (TIDAK BOLEH DIUBAH)
# ----------------------------------------------------
DOMAIN_WHITELIST = {
    "zahir", "firebird", "dongle", "ultraviewer", "teamviewer", "anydesk",
    "po", "do", "sn", "inv", "invoice", "ip", "rtd", "neraca", "faktur",
    "server", "client", "induk", "anakan", "database", "posting", "giro"
}

# ----------------------------------------------------
# LAYER 1: LOAD OFFICIAL INDO-NORMALIZER CORPUS
# ----------------------------------------------------
def load_indo_normalizer_corpus():
    pkg_dir = Path(indo_normalizer.__file__).parent
    slangs_file = pkg_dir / "corpus" / "slangs.csv"
    corpus_dict = {}
    if slangs_file.exists():
        with open(slangs_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    k = row[0].strip().lower()
                    v = row[1].strip().lower()
                    # Jangan masukkan jika menabrak domain whitelist Zahir
                    if k not in DOMAIN_WHITELIST:
                        corpus_dict[k] = v
    return corpus_dict

INDO_NORMALIZER_SLANGS = load_indo_normalizer_corpus()

# ----------------------------------------------------
# LAYER 3 & 4: DIALEK CHAT LOKAL + DOMAIN SPESIFIK ZAHIR
# ----------------------------------------------------
DOMAIN_AND_LOCAL_SLANGS = {
    # Negasi & Tanya
    "gak": "tidak", "ga": "tidak", "nggak": "tidak", "ngga": "tidak", "g": "tidak",
    "kaga": "tidak", "kagak": "tidak", "tdak": "tidak", "tidka": "tidak", "tdk": "tidak",
    "gmna": "bagaimana", "gmn": "bagaimana", "gmana": "bagaimana", "gimana": "bagaimana", "bapake": "bapak",
    "kx": "kenapa", "kok": "kenapa", "ko": "kenapa", "knp": "kenapa", "knpa": "kenapa",
    "tanyank": "tanya", "tny": "tanya", "nyank": "tanya", "nanya": "tanya",

    # Waktu, Tanggal & Status
    "dlu": "dulu", "dl": "dulu",
    "blum": "belum", "blm": "belum", "belom": "belum",
    "udh": "sudah", "sdh": "sudah", "uda": "sudah", "sudh": "sudah", "sudha": "sudah",
    "audha": "sudah", "usdha": "sudah", "udah": "sudah",
    "kmrn": "kemarin", "kmarin": "kemarin", "kemaren": "kemarin",
    "klau": "kalau", "klo": "kalau", "kl": "kalau", "kalo": "kalau", "klu": "kalau",
    "skrg": "sekarang", "skr": "sekarang", "now": "sekarang",
    "bbrp": "beberapa", "berati": "berarti",
    "bsok": "besok", "tgl": "tanggal", "thn": "tahun", "bln": "bulan", "nomer": "nomor",

    # Subjek & Objek
    "sya": "saya", "sy": "saya", "syaa": "saya", "ak": "aku", "aq": "aku",
    "km": "kamu", "kmu": "kamu", "lu": "kamu", "lo": "kamu",
    "tak": "saya",

    # Bantuan, Kata Kerja & Komunikasi
    "tlng": "tolong", "tlg": "tolong",
    "bntu": "bantu", "bantuu": "bantu", "dibntu": "dibantu",
    "bsa": "bisa", "bs": "bisa", "bisaa": "bisa",
    "bkin": "membuat", "bikin": "membuat",
    "nyarik": "mencari", "nyari": "mencari", "cari": "mencari",
    "nyamakan": "menyamakan",
    "ilang": "hilang", "ilangin": "menghilangkan",
    "bener": "benar", "benerin": "memperbaiki", "beneran": "benar",
    "narik": "menarik",
    "blas": "balas", "diblas": "dibalas",
    "kluar": "keluar",
    "liat": "lihat",
    "kekunci": "terkunci",
    "cbanya": "mencoba", "cobanya": "mencoba",

    # Partikel, Penghubung & Sapaan
    "yg": "yang", "yng": "yang",
    "aja": "saja", "aj": "saja",
    "jg": "juga", "jga": "juga",
    "tp": "tetapi", "tpi": "tetapi", "tapi": "tetapi",
    "krn": "karena", "karna": "karena",
    "sm": "sama", "dg": "dengan", "dgn": "dengan",
    "utk": "untuk", "untk": "untuk", "unutk": "untuk",
    "pdhl": "padahal", "pdahal": "padahal",
    "gtu": "begitu", "gitu": "begitu",
    "gni": "begini", "gini": "begini",
    "siank": "siang", "siankk": "siang",
    "ksih": "kasih",
    "makasih": "terimakasih", "mksih": "terimakasih", "makasi": "terimakasih",
    "cuma": "hanya",
    "kayak": "seperti", "kek": "seperti", "kyk": "seperti",
    "tetep": "tetap",
    "trus": "terus", "trs": "terus",
    "banyank": "banyak",

    # Istilah Khusus Zahir, Remote & Akuntansi
    "nyantol": "menggantung",
    "nyantolnya": "menggantung",
    "kmputer": "komputer",
    "kompter": "komputer",
    "kompternya": "komputernya",
    "pituang": "piutang",
    "remot": "remote",
    "tiem": "teamviewer",
}

def load_csv(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def reduce_elongated_words(word):
    if word in DOMAIN_WHITELIST:
        return word
    return re.sub(r"(.)\1{2,}", r"\1", word)

def normalize_token_cascaded(w):
    """
    Menjalankan normalisasi berjenjang (Cascaded Normalization) per kata:
    0. Cek Domain Whitelist Zahir (jika cocok -> biarkan)
    1. Cek Kamus Dialek & Zahir Domain Slangs (prioritas konteks bisnis)
    2. Reduksi huruf berulang (elongated words)
    3. Cek Korpus Resmi Library indo-normalizer (1.284 entri)
    """
    # 0. Domain Whitelist
    if w in DOMAIN_WHITELIST:
        return w, False

    # 1. Prioritas Domain & Dialek Lokal
    if w in DOMAIN_AND_LOCAL_SLANGS:
        return DOMAIN_AND_LOCAL_SLANGS[w], True

    # 2. Reduksi huruf berulang (misal: 'bisaaa' -> 'bisa', 'errooor' -> 'error')
    reduced_w = reduce_elongated_words(w)
    was_reduced = (reduced_w != w)

    if reduced_w in DOMAIN_WHITELIST:
        return reduced_w, was_reduced

    if reduced_w in DOMAIN_AND_LOCAL_SLANGS:
        return DOMAIN_AND_LOCAL_SLANGS[reduced_w], True

    # 3. Layer Library indo-normalizer
    if reduced_w in INDO_NORMALIZER_SLANGS:
        return INDO_NORMALIZER_SLANGS[reduced_w], True
    if w in INDO_NORMALIZER_SLANGS:
        return INDO_NORMALIZER_SLANGS[w], True

    return reduced_w, was_reduced

def normalize_text_cascaded(text):
    if not text:
        return "", 0

    words = text.split()
    normalized_words = []
    normalized_count = 0

    for w in words:
        norm_word, is_changed = normalize_token_cascaded(w)
        normalized_words.append(norm_word)
        if is_changed:
            normalized_count += 1

    return " ".join(normalized_words), normalized_count

def process_normalization(data):
    processed = []
    total_words_normalized = 0

    for row in data:
        clean_text = row["clean_text"]
        normalized_text, count = normalize_text_cascaded(clean_text)
        total_words_normalized += count

        row_copy = dict(row)
        row_copy["normalized_text"] = normalized_text
        row_copy["normalized_words_count"] = count
        processed.append(row_copy)

    return processed, total_words_normalized

def save_to_csv(data, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sub_conversation_id",
        "conversation_id",
        "source_file",
        "client_response",
        "penanganan_remote",
        "kategori_kendala",
        "raw_text",
        "clean_text",
        "normalized_text",
        "token_count",
        "normalized_words_count",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return output_path

def validate(data, total_normalized):
    print("\n=== VALIDASI FASE 11 (CASCADED NORMALIZATION WITH INDO-NORMALIZER) ===")
    total_docs = len(data)
    docs_with_norm = sum(1 for r in data if int(r["normalized_words_count"]) > 0)

    print(f"Status Library: indo-normalizer v{indo_normalizer.__version__} aktif.")
    print(f"Ukuran Korpus Library: {len(INDO_NORMALIZER_SLANGS)} pasangan slang terintegrasi.")
    print(f"Total Dokumen Diproses: {total_docs}")
    print(f"Total Kata Slang yang Berhasil Dinormalisasi: {total_normalized} kata")
    print(f"Dokumen yang Mengandung Normalisasi: {docs_with_norm} ({docs_with_norm/total_docs*100:.1f}%)\n")

    print("CONTOH HASIL NORMALISASI BERJENJANG (3 SAMPEL):")
    sample_cids = ["chat_1_conv_001_e", "chat_1_conv_008_b", "chat_1_conv_005_b"]
    for cid in sample_cids:
        row = next((r for r in data if r["sub_conversation_id"] == cid), None)
        if row:
            print(f"\n[Sub-ID: {row['sub_conversation_id']} | Kategori: {row['kategori_kendala']}]")
            print(f"  CLEAN      : \"{row['clean_text'][:110]}...\"")
            print(f"  NORMALIZED : \"{row['normalized_text'][:110]}...\"")
            print(f"  KATA DINORMALISASI: {row['normalized_words_count']} kata")
    print()

def run():
    if not INPUT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_FILE}")
        print("Jalankan fase 10 terlebih dahulu: python main.py preprocess")
        return

    print("=" * 60)
    print("  FASE 11 — CASCADED NORMALIZATION (INDO-NORMALIZER + ZAHIR)")
    print(f"  Input : {INPUT_FILE}")
    print(f"  Output: {OUTPUT_FILE}")
    print("=" * 60)

    data = load_csv(INPUT_FILE)
    print(f"\nMemuat {len(data)} baris dokumen dari {INPUT_FILE.name}")

    processed_data, total_normalized = process_normalization(data)
    output = save_to_csv(processed_data, OUTPUT_FILE)
    print(f"Hasil disimpan ke: {output}")

    validate(processed_data, total_normalized)

    print("=" * 60)
    print("  FASE 11 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()