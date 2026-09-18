"""
category_labeling.py - Data Labeling & Sub-Conversation Topic Splitting (Fase 9)

Membaca chat_with_remotes.csv, memecah percakapan yang memiliki pergeseran topik
menjadi sub_conversation_id (Opsi A - Sub-Conversation Splitting),
menetapkan 1 kategori_kendala presisi per sub_conversation_id,
lalu menyimpan hasil akhir ke chat_with_categories.csv.
"""

import csv
from pathlib import Path
from collections import Counter

from src.taxonomy import (
    build_category_patterns,
    detect_category,
    get_fallback_category,
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "chat_with_remotes.csv"
OUTPUT_FILE = PROCESSED_DIR / "chat_with_categories.csv"

# Definisi Pattern Kategori Kendala dengan Bobot Prioritas Deteksi.
# Berasal dari config/taxonomy.json (single source of truth) agar selalu sinkron.
CATEGORY_PATTERNS = build_category_patterns()
FALLBACK = get_fallback_category()

def load_csv(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def detect_message_category(text):
    for cat_name, pattern in CATEGORY_PATTERNS:
        if pattern.search(text):
            return cat_name
    return None

def split_and_label_conversation(msgs):
    """
    Memecah 1 conversation thread menjadi 1 atau lebih sub-conversation (sub_conversation_id)
    berdasarkan pergeseran topik kendala dari pesan klien.
    """
    sub_convs = []
    current_sub_msgs = []
    current_cat = None
    sub_index = 1

    for m in msgs:
        text = m["percakapan"]
        role = m["role"]
        detected_cat = detect_message_category(text) if role == "CLIENT" else None

        if not current_sub_msgs:
            current_sub_msgs.append(m)
            if detected_cat:
                current_cat = detected_cat
        else:
            # Jika terdeteksi kategori baru yang berbeda signifikan dari kategori segmen saat ini
            if detected_cat and current_cat and detected_cat != current_cat:
                # Simpan sub-conversation sebelumnya
                sub_convs.append((sub_index, current_cat or FALLBACK, current_sub_msgs))
                sub_index += 1
                current_sub_msgs = [m]
                current_cat = detected_cat
            else:
                current_sub_msgs.append(m)
                if not current_cat and detected_cat:
                    current_cat = detected_cat

    if current_sub_msgs:
        sub_convs.append((sub_index, current_cat or FALLBACK, current_sub_msgs))

    return sub_convs

def process_labeling(data):
    conv_map = {}
    for row in data:
        cid = row["conversation_id"]
        if cid not in conv_map:
            conv_map[cid] = []
        conv_map[cid].append(row)

    processed_rows = []
    sub_conv_summary = {}

    suffix_letters = "abcdefghijklmnopqrstuvwxyz"

    for cid, msgs in conv_map.items():
        sub_convs = split_and_label_conversation(msgs)
        for idx, cat_label, sub_msgs in sub_convs:
            letter = suffix_letters[(idx - 1) % len(suffix_letters)]
            sub_id = f"{cid}_{letter}"
            sub_conv_summary[sub_id] = {
                "parent_cid": cid,
                "category": cat_label,
                "msg_count": len(sub_msgs),
            }
            for m in sub_msgs:
                row_copy = dict(m)
                row_copy["sub_conversation_id"] = sub_id
                row_copy["kategori_kendala"] = cat_label
                processed_rows.append(row_copy)

    return processed_rows, sub_conv_summary

def save_to_csv(data, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id", "conversation_id", "sub_conversation_id", "source_file", "tanggal", "waktu",
        "pengirim", "role", "client_response", "penanganan_remote", "contains_credentials",
        "kategori_kendala", "percakapan", "media_type", "media_path", "has_media",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return output_path

def validate(data, sub_conv_summary):
    print("\n=== VALIDASI FASE 9 (DATA LABELING — OPSI A: SUB-CONVERSATION SPLITTING) ===")

    total_msgs = len(data)
    total_sub_convs = len(sub_conv_summary)
    total_parent_convs = len(set(info["parent_cid"] for info in sub_conv_summary.values()))

    print(f"Total parent conversation (Threshold 4 jam): {total_parent_convs}")
    print(f"Total sub-conversation ID (Topik terpisah): {total_sub_convs}")
    print(f"Total pesan terproses: {total_msgs}\n")

    cat_counts = Counter(info["category"] for info in sub_conv_summary.values())
    print("SEBARAN KATEGORI KENDALA (PER SUB-CONVERSATION):")
    for cat, count in cat_counts.most_common():
        pct = (count / total_sub_convs) * 100
        print(f"  - {cat:<30}: {count} sub-percakapan ({pct:.1f}%)")
    print()

    # Tampilkan contoh pemecahan percakapan
    split_parents = [cid for cid in set(info["parent_cid"] for info in sub_conv_summary.values())
                     if sum(1 for info in sub_conv_summary.values() if info["parent_cid"] == cid) > 1]

    print(f"CONTOH PERCAKAPAN YANG DIPECAH TOPIKNYA ({len(split_parents)} parent conversation dipisah):")
    for parent_cid in split_parents[:3]:
        sub_list = [(sub_id, info) for sub_id, info in sub_conv_summary.items() if info["parent_cid"] == parent_cid]
        print(f"\n  [Parent Conversation: {parent_cid}]")
        for sub_id, info in sub_list:
            print(f"   -> Sub-ID: {sub_id:<20} | Kategori: {info['category']:<28} | Jumlah Pesan: {info['msg_count']}")

    print()

def run():
    if not INPUT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_FILE}")
        print("Jalankan fase 7 terlebih dahulu: python main.py remote")
        return

    print("=" * 60)
    print("  FASE 9 — DATA LABELING (OPSI A: SUB-CONVERSATION SPLITTING)")
    print(f"  Input : {INPUT_FILE}")
    print(f"  Output: {OUTPUT_FILE}")
    print("=" * 60)

    data = load_csv(INPUT_FILE)
    print(f"\nMemuat {len(data)} pesan dari {INPUT_FILE.name}")

    processed_data, sub_summary = process_labeling(data)

    output = save_to_csv(processed_data, OUTPUT_FILE)
    print(f"Hasil disimpan ke: {output}")

    validate(processed_data, sub_summary)

    print("=" * 60)
    print("  FASE 9 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()