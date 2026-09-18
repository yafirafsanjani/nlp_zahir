"""
category_exploration.py - Eksplorasi Kategori Kendala (Fase 8)

Membaca chat_with_remotes.csv, menganalisis isi percakapan klien per conversation_id,
melakukan analisis kata kunci / N-gram, memetakan ke kandidat taksonomi kategori kendala Zahir,
serta menampilkan statistik distribusi data untuk persiapan Fase 9 (Data Labeling).
"""

import csv
import re
from pathlib import Path
from collections import Counter

from src.taxonomy import (
    build_category_dict,
    get_fallback_category,
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "chat_with_remotes.csv"

# Definisi Kata Kunci Kandidat Kategori Kendala Zahir.
# Berasal dari config/taxonomy.json (single source of truth) agar selalu sinkron.
CATEGORY_PATTERNS = build_category_dict()
FALLBACK = get_fallback_category()

STOPWORDS = {
    "yang", "di", "ke", "dari", "ini", "itu", "dan", "atau", "untuk", "dengan", "pada", "adalah", "ada",
    "bisa", "tidak", "gak", "nggak", "nga", "ngga", "ya", "sudah", "udah", "mau", "akan", "kalau", "kalo",
    "jika", "saya", "kami", "pak", "bu", "kak", "ibu", "bapak", "mas", "mbak", "tolong", "bantu", "mohon",
    "lagi", "biar", "agar", "nya", "sama", "aja", "saja", "terima", "kasih", "makasih",
    "siap", "baik", "selamat", "pagi", "siang", "sore", "malam", "halo", "hallo", "haloo", "hi", "hey",
    "media", "disertakan", "file", "terlampir", "img", "jpg", "wa", "pesan", "dihapus", "diedit", "png"
}

def load_csv(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def clean_text(text):
    text = text.lower()
    text = re.sub(r"<media\s+tidak\s+disertakan>", "", text)
    text = re.sub(r"img-\d+-wa\d+\.\w+", "", text)
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if len(t) > 1 and not t.isdigit() and t not in STOPWORDS]

def extract_ngrams(tokens, n):
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

def analyze_categories(data):
    conv_map = {}
    for row in data:
        cid = row["conversation_id"]
        if cid not in conv_map:
            conv_map[cid] = []
        conv_map[cid].append(row)

    total_convs = len(conv_map)
    conv_categories = {}
    conv_client_text = {}
    all_client_tokens = []
    all_bigrams = []
    all_trigrams = []

    for cid, msgs in conv_map.items():
        client_msgs = [m["percakapan"] for m in msgs if m["role"] == "CLIENT"]
        combined_text = " ".join(client_msgs) if client_msgs else " ".join([m["percakapan"] for m in msgs])
        conv_client_text[cid] = combined_text

        tokens = clean_text(combined_text)
        all_client_tokens.extend(tokens)
        all_bigrams.extend(extract_ngrams(tokens, 2))
        all_trigrams.extend(extract_ngrams(tokens, 3))

        matched_cats = []
        for cat, pattern in CATEGORY_PATTERNS.items():
            if pattern.search(combined_text):
                matched_cats.append(cat)

        if not matched_cats:
            matched_cats = [FALLBACK]

        conv_categories[cid] = matched_cats

    return {
        "total_convs": total_convs,
        "conv_categories": conv_categories,
        "conv_client_text": conv_client_text,
        "unigrams": Counter(all_client_tokens),
        "bigrams": Counter(all_bigrams),
        "trigrams": Counter(all_trigrams),
        "conv_map": conv_map
    }

def print_exploration_results(results):
    print("\n" + "=" * 60)
    print("  FASE 8 — EKSPLORASI KATEGORI KENDALA ZAHIR")
    print("=" * 60)

    print(f"\n1. RINGKASAN DATA PERCAKAPAN")
    print(f"   Total Unit Percakapan: {results['total_convs']}")

    print("\n2. FREKUENSI KATA KUNCI PADA PESAN KLIEN (TOP 15 UNIGRAM)")
    for word, freq in results["unigrams"].most_common(15):
        print(f"   - {word:<20}: {freq} kali")

    print("\n3. FREKUENSI FRASA DUA KATA (TOP 10 BIGRAM)")
    for phrase, freq in results["bigrams"].most_common(10):
        print(f"   - {phrase:<25}: {freq} kali")

    print("\n4. FREKUENSI FRASA TIGA KATA (TOP 10 TRIGRAM)")
    for phrase, freq in results["trigrams"].most_common(10):
        print(f"   - {phrase:<30}: {freq} kali")

    cat_counter = Counter()
    for cat_list in results["conv_categories"].values():
        for cat in cat_list:
            cat_counter[cat] += 1

    print("\n5. ESTIMASI SEBARAN KANDIDAT KATEGORI KENDALA (BOLEH MULTI-MATCH SEBELUM LABELING FASE 9)")
    for cat, count in cat_counter.most_common():
        pct = (count / results["total_convs"]) * 100
        print(f"   - {cat:<30}: {count} percakapan ({pct:.1f}%)")

    print("\n6. CONTOH KELUHAN KLIEN PER KANDIDAT KATEGORI (MAX 2 SAMPLE)")
    for cat in list(CATEGORY_PATTERNS.keys()) + [FALLBACK]:
        samples = [cid for cid, cats in results["conv_categories"].items() if cat in cats]
        if samples:
            print(f"\n   [Kategori: {cat}] ({len(samples)} percakapan)")
            for cid in samples[:2]:
                text_sample = results["conv_client_text"][cid][:120].strip().replace("\n", " ")
                print(f"   - [{cid}] \"{text_sample}...\"")

def run():
    if not INPUT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_FILE}")
        print("Jalankan fase 7 terlebih dahulu: python main.py remote")
        return

    print(f"Memuat data dari: {INPUT_FILE}")
    data = load_csv(INPUT_FILE)
    results = analyze_categories(data)
    print_exploration_results(results)

    print("\n" + "=" * 60)
    print("  FASE 8 SELESAI — SIAP LANJUT KE FASE 9 (DATA LABELING)")
    print("=" * 60)

if __name__ == "__main__":
    run()