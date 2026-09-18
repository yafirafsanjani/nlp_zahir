"""
taxonomy.py - Single Source of Truth Taksonomi Kategori Kendala

Membaca config/taxonomy.json (definisi kategori + kata kunci + frasa) dan
membangun pola regex otomatis. Digunakan bersama oleh pipeline regex (Fase 8/9)
dan modul LLM labeling (Fase 9+) sehingga taksonomi selalu sinkron.

Menambah/mengubah kategori cukup dengan mengedit config/taxonomy.json
tanpa perlu mengubah kode.
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = BASE_DIR / "config" / "taxonomy.json"

_DEFAULT_FALLBACK = "LAINNYA_UNCATEGORIZED"


def load_taxonomy():
    """Memuat taksonomi dari config/taxonomy.json (mengembalikan dict)."""
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_fallback_category():
    """Mengembalikan nama kategori fallback (bila tidak ada yang cocok)."""
    data = load_taxonomy()
    return data.get("fallback_category", _DEFAULT_FALLBACK)


def _build_pattern_for_category(cat):
    parts = []
    for kw in cat.get("keywords", []):
        parts.append(r"\b" + re.escape(kw) + r"\b")
    for phrase in cat.get("phrases", []):
        words = phrase.strip().split()
        parts.append(r"\b" + r"\s+".join(re.escape(w) for w in words) + r"\b")
    return re.compile("|".join(parts), re.IGNORECASE)


def build_category_patterns():
    """
    Membangun pasangan (nama_kategori, pola_regex) secara terurut sesuai
    urutan di config/taxonomy.json. Urutan menentukan prioritas deteksi:
    kategori pertama yang cocok akan menang.
    """
    data = load_taxonomy()
    result = []
    for cat in data.get("categories", []):
        result.append((cat["name"], _build_pattern_for_category(cat)))
    return result


def build_category_dict():
    """Versi dict dari build_category_patterns() untuk lookup by nama."""
    return dict(build_category_patterns())


def list_category_names():
    """Mengembalikan daftar nama kategori (tanpa fallback)."""
    return [name for name, _ in build_category_patterns()]


def detect_category(text, patterns=None):
    """
    Mendeteksi kategori pertama yang cocok pada teks.
    Mengembalikan nama kategori, atau fallback bila tidak cocok.
    """
    if patterns is None:
        patterns = build_category_patterns()
    for cat_name, pattern in patterns:
        if pattern.search(text):
            return cat_name
    return get_fallback_category()


if __name__ == "__main__":
    print("=== VALIDASI TAKSONOMI (FASE TAXONOMY CONFIG) ===")
    cats = load_taxonomy()
    print(f"Versi taksonomi : {cats.get('version')}")
    print(f"Fallback        : {get_fallback_category()}")
    print(f"Jumlah kategori : {len(cats.get('categories', []))}\n")

    patterns = build_category_patterns()
    for name, pat in patterns:
        print(f"  - {name}: {pat.pattern}")

    print("\nContoh deteksi:")
    samples = [
        ("database error firebird saat buka", "DATABASE_SYSTEM_ERROR"),
        ("dongle tidak terbaca untuk aktivasi lisensi", "LISENSI_DONGLE_REGISTRASI"),
        ("cara install server untuk network client", "INSTALASI_SETUP_NETWORK"),
        ("laporan laba rugi tidak seimbang saat cetak pdf", "LAPORAN_REPORTING"),
        ("input faktur penjualan stok tidak masuk", "TRANSAKSI_INPUT_DATA"),
        ("tanya bagaimana cara buat modul persediaan", "PERTANYAAN_UMUM_FITUR"),
        ("halo selamat pagi", "LAINNYA_UNCATEGORIZED"),
    ]
    for text, expected in samples:
        got = detect_category(text, patterns)
        status = "OK" if got == expected else f"BERBEDA (harusnya {expected})"
        print(f"  [{status}] '{text}' -> {got}")