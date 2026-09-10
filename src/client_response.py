"""
client_response.py - Analisis Respons Klien (Fase 6) - Updated Logic

Membaca chat_with_conversations.csv, menganalisis interaksi per
conversation_id untuk menentukan label client_response (RESPONS / TIDAK_RESPONS),
lalu menyimpan hasil ke chat_with_responses.csv.
"""

import csv
import re
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "chat_with_conversations.csv"
OUTPUT_FILE = PROCESSED_DIR / "chat_with_responses.csv"

# Kata-kata penutup / kesopanan dari Admin yang menunjukkan tidak perlu balasan lagi dari Klien
ADMIN_CLOSING_KEYWORDS = re.compile(
    r"\b(sama[- ]*sama|sama2|terima\s+kasih|terimakasih|baik\s+(bu|pak|kak|ibu|mbak)|sama2\s+(bu|pak|kak|ibu|mbak)|baik\s+ibu|baik\s+pak|siap)\b",
    re.IGNORECASE,
)

# Kata-kata di mana Admin menanti kejelasan / pertanyaan / aksi lanjutan dari Klien
ADMIN_WAITING_KEYWORDS = re.compile(
    r"\?|bagaimana|apakah|bisa|mohon|dapat|dicoba|konfirmasi|ditunggu|boleh|dibantu|silahkan|silakan|perpanjangan|dijalankan",
    re.IGNORECASE,
)

def load_csv(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def determine_conversation_response(msgs):
    client_msgs = [m for m in msgs if m["role"] == "CLIENT"]
    admin_msgs = [m for m in msgs if m["role"] == "ADMIN"]

    # Jika tidak ada pesan Klien sama sekali
    if not client_msgs:
        return "TIDAK_RESPONS"

    # Jika tidak ada pesan Admin sama sekali (hanya Klien bertanya)
    if not admin_msgs:
        return "RESPONS"

    last_msg = msgs[-1]

    # Jika pesan terakhir dikirim oleh CLIENT -> RESPONS
    if last_msg["role"] == "CLIENT":
        return "RESPONS"

    # Jika pesan terakhir dikirim oleh ADMIN:
    last_admin_text = last_msg["percakapan"].strip()

    # Jika Admin hanya mengucapkan penutup (sama-sama / baik bu / baik kak) dan tidak mengajukan pertanyaan baru
    if ADMIN_CLOSING_KEYWORDS.search(last_admin_text) and not ADMIN_WAITING_KEYWORDS.search(last_admin_text):
        return "RESPONS"

    # Cek apakah sebelum pesan Admin terakhir, Klien sudah memberikan jawaban/konfirmasi/terima kasih
    # Jika pesan Klien terakhir berada tepat sebelum pesan penutup Admin -> RESPONS
    last_client_idx = max(i for i, m in enumerate(msgs) if m["role"] == "CLIENT")
    last_admin_idx = len(msgs) - 1

    # Jika setelah pesan Klien terakhir, Admin mengirim pesan yang sifatnya pertanyaan/solusi yang tidak dijawab Klien
    if last_admin_idx > last_client_idx:
        # Jika pesan Admin setelah Klien hanya 1-2 pesan penutup pendek
        remaining_admin_msgs = msgs[last_client_idx + 1:]
        all_short_closings = all(
            len(m["percakapan"].strip()) <= 30 or ADMIN_CLOSING_KEYWORDS.search(m["percakapan"])
            for m in remaining_admin_msgs
        )
        if all_short_closings and not any(ADMIN_WAITING_KEYWORDS.search(m["percakapan"]) for m in remaining_admin_msgs):
            return "RESPONS"
        return "TIDAK_RESPONS"

    return "RESPONS"

def assign_client_responses(data):
    conv_map = {}
    for row in data:
        cid = row["conversation_id"]
        if cid not in conv_map:
            conv_map[cid] = []
        conv_map[cid].append(row)

    conv_labels = {}
    for cid, msgs in conv_map.items():
        label = determine_conversation_response(msgs)
        conv_labels[cid] = label

    for row in data:
        cid = row["conversation_id"]
        row["client_response"] = conv_labels[cid]

    return data, conv_labels

def save_to_csv(data, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id", "conversation_id", "source_file", "tanggal", "waktu",
        "pengirim", "role", "client_response", "percakapan", "media_type",
        "media_path", "has_media",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return output_path

def validate(data, conv_labels):
    print("\n=== VALIDASI FASE 6 (CLIENT RESPONSE - PERBAIKAN) ===")

    total_msgs = len(data)
    total_convs = len(conv_labels)

    label_counts = Counter(conv_labels.values())
    print(f"Total percakapan: {total_convs}")
    for label, count in label_counts.most_common():
        pct = count / total_convs * 100
        print(f"  {label}: {count} percakapan ({pct:.1f}%)")
    print()

    msg_label_counts = Counter(row["client_response"] for row in data)
    print(f"Total pesan: {total_msgs}")
    for label, count in msg_label_counts.most_common():
        pct = count / total_msgs * 100
        print(f"  {label}: {count} pesan ({pct:.1f}%)")
    print()

    file_conv_labels = {}
    for row in data:
        fname = row["source_file"]
        cid = row["conversation_id"]
        label = row["client_response"]
        if fname not in file_conv_labels:
            file_conv_labels[fname] = {}
        file_conv_labels[fname][cid] = label

    print("Distribusi per file:")
    for fname, cdict in sorted(file_conv_labels.items()):
        fcounts = Counter(cdict.values())
        print(f"  {fname}: {len(cdict)} percakapan")
        for lbl, cnt in fcounts.most_common():
            print(f"    - {lbl}: {cnt}")
    print()

    print("--- CONTOH PERCAKAPAN 'TIDAK_RESPONS' (max 5) ---")
    tidak_respons_cids = [cid for cid, lbl in conv_labels.items() if lbl == "TIDAK_RESPONS"]
    for cid in tidak_respons_cids[:5]:
        c_msgs = [m for m in data if m["conversation_id"] == cid]
        last_m = c_msgs[-1]
        print(f"[{cid}] ({len(c_msgs)} pesan) - Pesan Terakhir ({last_m['role']}):")
        print(f"  -> \"{last_m['percakapan'][:90]}\"")
    print()

    print("--- CONTOH PERCAKAPAN 'RESPONS' (max 5) ---")
    respons_cids = [cid for cid, lbl in conv_labels.items() if lbl == "RESPONS"]
    for cid in respons_cids[:5]:
        c_msgs = [m for m in data if m["conversation_id"] == cid]
        last_m = c_msgs[-1]
        print(f"[{cid}] ({len(c_msgs)} pesan) - Pesan Terakhir ({last_m['role']}):")
        print(f"  -> \"{last_m['percakapan'][:90]}\"")
    print()

def run():
    if not INPUT_FILE.exists():
        print(f"[ERROR] File tidak ditemukan: {INPUT_FILE}")
        print("Jalankan fase 5 terlebih dahulu: python main.py conversations 4")
        return

    print("=" * 60)
    print("  FASE 6 - ANALISIS RESPONS KLIEN (PERBAIKAN LOGIKA)")
    print(f"  Input : {INPUT_FILE}")
    print(f"  Output: {OUTPUT_FILE}")
    print("=" * 60)

    data = load_csv(INPUT_FILE)
    print(f"\nMemuat {len(data)} pesan dari {INPUT_FILE.name}")

    data, conv_labels = assign_client_responses(data)

    output = save_to_csv(data, OUTPUT_FILE)
    print(f"Hasil disimpan ke: {output}")

    validate(data, conv_labels)

    print("=" * 60)
    print("  FASE 6 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()
