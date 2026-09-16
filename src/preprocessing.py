"""
preprocessing.py - Text Preprocessing (Fase 10)

Membaca chat_with_categories.csv, mengagregasi teks per sub_conversation_id,
melakukan pembersihan teks (case folding, pembersihan artefak WhatsApp, tanda baca, URL, angka isolated, spasi ganda),
lalu menyimpan hasil teks yang telah dibersihkan ke chat_preprocessed.csv.
"""

import csv
import re
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "chat_with_categories.csv"
OUTPUT_FILE = PROCESSED_DIR / "chat_preprocessed.csv"

def load_csv(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def clean_text_advanced(text):
    if not text:
        return ""

    # 1. Case Folding
    text = text.lower()

    # 2. Hapus artefak media & sistem WhatsApp
    text = re.sub(r"<media\s+tidak\s+disertakan>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"img-\d+-wa\d+\.\w+", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"pesan\s+ini\s+dihapus", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"pesan\s+ini\s+diedit", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\(file\s+terlampir\)", " ", text, flags=re.IGNORECASE)

    # 3. Hapus URL / Link
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # 4. Hapus karakter non-alphanumeric (tanda baca, simbol, emoji), pertahankan spasi
    text = re.sub(r"[^\w\s]", " ", text)

    # 5. Hapus angka yang berdiri sendiri (pertahankan istilah alfanumerik bila ada)
    text = re.sub(r"\b\d+\b", " ", text)

    # 6. Normalisasi Whitespace & newline
    text = re.sub(r"\s+", " ", text).strip()

    return text

def aggregate_and_preprocess(data):
    sub_map = {}
    for row in data:
        sub_id = row["sub_conversation_id"]
        if sub_id not in sub_map:
            sub_map[sub_id] = {
                "parent_conversation_id": row["conversation_id"],
                "source_file": row["source_file"],
                "client_response": row["client_response"],
                "penanganan_remote": row["penanganan_remote"],
                "kategori_kendala": row["kategori_kendala"],
                "client_messages": [],
                "all_messages": [],
            }
        text = row["percakapan"]
        if row["role"] == "CLIENT":
            sub_map[sub_id]["client_messages"].append(text)
        sub_map[sub_id]["all_messages"].append(text)

    processed_rows = []
    for sub_id, info in sub_map.items():
        # Prioritaskan pesan Klien sebagai teks analisis keluhan; jika tidak ada klien, gunakan semua pesan
        raw_text = " ".join(info["client_messages"]) if info["client_messages"] else " ".join(info["all_messages"])
        clean_text = clean_text_advanced(raw_text)

        processed_rows.append({
            "sub_conversation_id": sub_id,
            "conversation_id": info["parent_conversation_id"],
            "source_file": info["source_file"],
            "client_response": info["client_response"],
            "penanganan_remote": info["penanganan_remote"],
            "kategori_kendala": info["kategori_kendala"],
            "raw_text": raw_text,
            "clean_text": clean_text,
            "token_count": len(clean_text.split()) if clean_text else 0,
        })

    return processed_rows

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
        "token_count",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return output_path

def validate(data):
    print("\n=== VALIDASI FASE 10 (TEXT PREPROCESSING) ===")
    total_docs = len(data)
    print(f"Total Sub-Conversation Dokumen: {total_docs}")

    tokens = [row["token_count"] for row in data]
    avg_tokens = sum(tokens) / total_docs if total_docs else 0
    min_tokens = min(tokens) if tokens else 0
    max_tokens = max(tokens) if tokens else 0

    print(f"Statistik Jumlah Token per Dokumen:")
    print(f"  - Rata-rata token : {avg_tokens:.1f}")
    print(f"  - Minimal token   : {min_tokens}")
    print(f"  - Maksimal token  : {max_tokens}\n")

    empty_docs = sum(1 for row in data if row["token_count"] == 0)
    print(f"Dokumen dengan clean_text kosong: {empty_docs}\n")

    print("CONTOH PERBANDINGAN SEBELUM & SESUDAH PREPROCESSING (3 SAMPEL):")
    for row in data[:3]:
        print(f"\n[Sub-ID: {row['sub_conversation_id']} | Kategori: {row['kategori_kendala']}]")
        print(f"  RAW   : \"{row['raw_text'][:110]}...\"")
        print(f"  CLEAN : \"{row['clean_text'][:110]}...\"")
        print(f"  TOKEN : {row['token_count']} kata")
    print()

def run():
    if not INPUT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_FILE}")
        print("Jalankan fase 9 terlebih dahulu: python main.py label")
        return

    print("=" * 60)
    print("  FASE 10 — TEXT PREPROCESSING")
    print(f"  Input : {INPUT_FILE}")
    print(f"  Output: {OUTPUT_FILE}")
    print("=" * 60)

    data = load_csv(INPUT_FILE)
    print(f"\nMemuat {len(data)} baris pesan dari {INPUT_FILE.name}")

    processed_data = aggregate_and_preprocess(data)
    output = save_to_csv(processed_data, OUTPUT_FILE)
    print(f"Hasil disimpan ke: {output}")

    validate(processed_data)

    print("=" * 60)
    print("  FASE 10 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()