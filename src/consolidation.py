"""
consolidation.py - Penggabungan Hasil Master Final (Fase 18)

Menggabungkan seluruh hasil analisis pipeline NLP Zahir:
1. client_response (RESPONS / TIDAK_RESPONS)
2. penanganan_remote (REMOTE / NON_REMOTE) & contains_credentials
3. kategori_kendala (Ground-Truth & Hasil Prediksi Model AI Produksi)
4. Statistik pesan (durasi, jumlah pesan klien/admin, cuplikan keluhan)
Menyimpan berkas master lengkap ke data/output/master_conversations_final.csv.
"""

import csv
from pathlib import Path
from collections import Counter
from src.predict import predict_single_text

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "data" / "output"
CATEGORIES_CSV = PROCESSED_DIR / "chat_with_categories.csv"
NORMALIZED_CSV = PROCESSED_DIR / "chat_normalized.csv"
MASTER_FINAL_CSV = OUTPUT_DIR / "master_conversations_final.csv"

def load_data():
    with open(CATEGORIES_CSV, "r", encoding="utf-8") as f:
        cat_rows = list(csv.DictReader(f))

    with open(NORMALIZED_CSV, "r", encoding="utf-8") as f:
        norm_rows = list(csv.DictReader(f))

    return cat_rows, norm_rows

def consolidate_master_dataset(cat_rows, norm_rows):
    # Mapping teks normalisasi per sub_id
    norm_map = {r["sub_conversation_id"]: r for r in norm_rows}

    # Grouping pesan per sub_conversation_id
    sub_map = {}
    for r in cat_rows:
        sub_id = r["sub_conversation_id"]
        if sub_id not in sub_map:
            sub_map[sub_id] = []
        sub_map[sub_id].append(r)

    master_records = []

    for sub_id, msgs in sub_map.items():
        first_m = msgs[0]
        last_m = msgs[-1]

        parent_cid = first_m["conversation_id"]
        source_file = first_m["source_file"]
        client_resp = first_m["client_response"]
        remote_status = first_m["penanganan_remote"]
        gt_category = first_m["kategori_kendala"]

        client_msgs = [m for m in msgs if m["role"] == "CLIENT"]
        admin_msgs = [m for m in msgs if m["role"] == "ADMIN"]

        has_credentials = any(m.get("contains_credentials") == "True" for m in msgs)
        has_media_file = any(m.get("has_media") == "True" for m in msgs)

        first_client_text = client_msgs[0]["percakapan"] if client_msgs else msgs[0]["percakapan"]
        first_client_text_clean = first_client_text.strip().replace("\n", " ")

        # Ambil teks normalisasi untuk inferensi model ML
        norm_info = norm_map.get(sub_id, {})
        normalized_text = norm_info.get("normalized_text", "")

        # Prediksi AI Model Produksi
        ml_res = predict_single_text(normalized_text)
        predicted_cat = ml_res["predicted_category"]
        confidence_score = ml_res["confidence"]
        is_match = (predicted_cat == gt_category)

        master_records.append({
            "sub_conversation_id": sub_id,
            "conversation_id": parent_cid,
            "source_file": source_file,
            "start_time": f"{first_m['tanggal']} {first_m['waktu']}",
            "end_time": f"{last_m['tanggal']} {last_m['waktu']}",
            "total_messages": len(msgs),
            "client_messages_count": len(client_msgs),
            "admin_messages_count": len(admin_msgs),
            "has_media": "True" if has_media_file else "False",
            "contains_credentials": "True" if has_credentials else "False",
            "client_response": client_resp,
            "penanganan_remote": remote_status,
            "kategori_kendala_ground_truth": gt_category,
            "kategori_kendala_ml_predicted": predicted_cat,
            "prediction_confidence": f"{confidence_score:.1f}%",
            "prediction_match": "MATCH" if is_match else "DIFFER",
            "first_complaint_snippet": first_client_text_clean[:120],
        })

    return master_records

def save_master_csv(records, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sub_conversation_id",
        "conversation_id",
        "source_file",
        "start_time",
        "end_time",
        "total_messages",
        "client_messages_count",
        "admin_messages_count",
        "has_media",
        "contains_credentials",
        "client_response",
        "penanganan_remote",
        "kategori_kendala_ground_truth",
        "kategori_kendala_ml_predicted",
        "prediction_confidence",
        "prediction_match",
        "first_complaint_snippet",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    return output_path

def validate(records):
    print("\n=== VALIDASI FASE 18 (PENGGABUNGAN HASIL MASTER DATASET) ===")
    total = len(records)
    print(f"Total Baris Konsolidasi Master : {total} Sub-Percakapan")

    # 1. Statistik Output 1: Client Response
    resp_counts = Counter(r["client_response"] for r in records)
    print("\n1. DISTRIBUSI CLIENT RESPONSE (OUTPUT 1):")
    for k, v in resp_counts.most_common():
        print(f"   - {k:<18}: {v:>3} ({v/total*100:.1f}%)")

    # 2. Statistik Output 3: Penanganan Remote
    remote_counts = Counter(r["penanganan_remote"] for r in records)
    print("\n2. DISTRIBUSI PENANGANAN REMOTE (OUTPUT 3):")
    for k, v in remote_counts.most_common():
        print(f"   - {k:<18}: {v:>3} ({v/total*100:.1f}%)")

    # 3. Statistik Output 2: Kategori Kendala
    cat_counts = Counter(r["kategori_kendala_ground_truth"] for r in records)
    print("\n3. DISTRIBUSI KATEGORI KENDALA (OUTPUT 2):")
    for k, v in cat_counts.most_common():
        print(f"   - {k:<30}: {v:>3} ({v/total*100:.1f}%)")

    # 4. Keselarasan AI Prediction vs Ground Truth
    match_count = sum(1 for r in records if r["prediction_match"] == "MATCH")
    print(f"\n4. KESELARASAN PREDIKSI AI DENGAN GROUND TRUTH:")
    print(f"   - Match / Sesuai : {match_count} / {total} ({match_count/total*100:.1f}%)")
    print(f"   - Differ         : {total - match_count} / {total} ({(total - match_count)/total*100:.1f}%)\n")

    print("CONTOH 3 BARIS DATA MASTER FINAL:")
    for r in records[:3]:
        print(f"\n[Sub-ID: {r['sub_conversation_id']} | File: {r['source_file']}]")
        print(f"  - Response : {r['client_response']} | Remote: {r['penanganan_remote']}")
        print(f"  - Kendala  : {r['kategori_kendala_ground_truth']}")
        print(f"  - AI Pred  : {r['kategori_kendala_ml_predicted']} ({r['prediction_confidence']}) -> {r['prediction_match']}")
        print(f"  - Pesan    : \"{r['first_complaint_snippet']}...\"")
    print()

def run():
    print("=" * 60)
    print("  FASE 18 — PENGGABUNGAN HASIL MASTER DATASET")
    print(f"  Output : {MASTER_FINAL_CSV}")
    print("=" * 60)

    cat_rows, norm_rows = load_data()
    master_records = consolidate_master_dataset(cat_rows, norm_rows)
    save_master_csv(master_records, MASTER_FINAL_CSV)
    validate(master_records)

    print("=" * 60)
    print("  FASE 18 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()