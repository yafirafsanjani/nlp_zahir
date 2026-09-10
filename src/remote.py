"""
remote.py - Analisis Penanganan Remote (Fase 7)

Membaca chat_with_responses.csv, menganalisis interaksi per conversation_id
untuk menentukan label penanganan_remote (REMOTE / NON_REMOTE) dan
flag contains_credentials (True / False), lalu menyimpan ke chat_with_remotes.csv.

Prinsip Keamanan:
- Menilai indikator remote & kredensial tanpa menyimpan nilai ID/password asli.
"""

import csv
import re
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "chat_with_responses.csv"
OUTPUT_FILE = PROCESSED_DIR / "chat_with_remotes.csv"

# Indikator aplikasi & aktivitas remote
REMOTE_PATTERNS = re.compile(
    r"\b(remote|remot|diremote|di-remot|di-remote|ultraviewer|ultra\s*viewer|teamviewer|team\s*viewer|anydesk|any\s*desk|ultraviever)\b",
    re.IGNORECASE,
)

# Indikator kredensial (ID/Password/Passcode remote)
CREDENTIAL_PATTERNS = re.compile(
    r"\b(id\s*&\s*pass|id\s*dan\s*pass|id\s*pass|pass\s*remote|id\s*remote)\b|\b(id|pass|password)\s*:\s*[0-9a-zA-Z]+|\b\d{3}\s*\d{3}\s*\d{3}\b|\b\d{8,9}\b",
    re.IGNORECASE,
)

def load_csv(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def analyze_conversation_remote(msgs):
    """Tentukan (penanganan_remote, contains_credentials) untuk satu conversation thread."""
    has_remote_indicator = False
    has_credentials = False

    for m in msgs:
        text = m["percakapan"]
        if REMOTE_PATTERNS.search(text):
            has_remote_indicator = True
        if CREDENTIAL_PATTERNS.search(text):
            has_credentials = True

    # Percakapan berlabel REMOTE jika ada indikator remote atau kredensial remote
    penanganan_remote = "REMOTE" if (has_remote_indicator or has_credentials) else "NON_REMOTE"

    return penanganan_remote, has_credentials

def assign_remote_labels(data):
    conv_map = {}
    for row in data:
        cid = row["conversation_id"]
        if cid not in conv_map:
            conv_map[cid] = []
        conv_map[cid].append(row)

    conv_remote_labels = {}
    conv_cred_labels = {}

    for cid, msgs in conv_map.items():
        remote_label, cred_label = analyze_conversation_remote(msgs)
        conv_remote_labels[cid] = remote_label
        conv_cred_labels[cid] = cred_label

    for row in data:
        cid = row["conversation_id"]
        row["penanganan_remote"] = conv_remote_labels[cid]
        # Deteksi spesifik kredensial per pesan
        msg_has_cred = bool(CREDENTIAL_PATTERNS.search(row["percakapan"]))
        row["contains_credentials"] = str(msg_has_cred)

    return data, conv_remote_labels, conv_cred_labels

def save_to_csv(data, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id", "conversation_id", "source_file", "tanggal", "waktu",
        "pengirim", "role", "client_response", "penanganan_remote",
        "contains_credentials", "percakapan", "media_type", "media_path", "has_media",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return output_path

def validate(data, conv_remote_labels, conv_cred_labels):
    print("\n=== VALIDASI FASE 7 (PENANGANAN REMOTE) ===")

    total_msgs = len(data)
    total_convs = len(conv_remote_labels)

    label_counts = Counter(conv_remote_labels.values())
    print(f"Total percakapan: {total_convs}")
    for label, count in label_counts.most_common():
        pct = count / total_convs * 100
        print(f"  {label}: {count} percakapan ({pct:.1f}%)")
    print()

    msg_label_counts = Counter(row["penanganan_remote"] for row in data)
    print(f"Total pesan: {total_msgs}")
    for label, count in msg_label_counts.most_common():
        pct = count / total_msgs * 100
        print(f"  {label}: {count} pesan ({pct:.1f}%)")
    print()

    cred_msgs = sum(1 for row in data if row["contains_credentials"] == "True")
    print(f"Pesan terdeteksi mengandung kredensial (contains_credentials): {cred_msgs}")
    print()

    file_conv_labels = {}
    for row in data:
        fname = row["source_file"]
        cid = row["conversation_id"]
        label = row["penanganan_remote"]
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

    print("--- CONTOH PERCAKAPAN 'REMOTE' (max 5) ---")
    remote_cids = [cid for cid, lbl in conv_remote_labels.items() if lbl == "REMOTE"]
    for cid in remote_cids[:5]:
        c_msgs = [m for m in data if m["conversation_id"] == cid]
        rel_msgs = [m for m in c_msgs if REMOTE_PATTERNS.search(m["percakapan"]) or CREDENTIAL_PATTERNS.search(m["percakapan"])]
        sample = rel_msgs[0] if rel_msgs else c_msgs[0]
        print(f"[{cid}] ({len(c_msgs)} pesan) - Sampel Pesan Remote ({sample['role']}):")
        print(f"  -> \"{sample['percakapan'][:90]}\"")
    print()

    print("--- CONTOH PERCAKAPAN 'NON_REMOTE' (max 3) ---")
    non_remote_cids = [cid for cid, lbl in conv_remote_labels.items() if lbl == "NON_REMOTE"]
    for cid in non_remote_cids[:3]:
        c_msgs = [m for m in data if m["conversation_id"] == cid]
        sample = c_msgs[0]
        print(f"[{cid}] ({len(c_msgs)} pesan) - Pesan Awal ({sample['role']}):")
        print(f"  -> \"{sample['percakapan'][:90]}\"")
    print()

def run():
    if not INPUT_FILE.exists():
        print(f"[ERROR] File tidak ditemukan: {INPUT_FILE}")
        print("Jalankan fase 6 terlebih dahulu: python main.py responses")
        return

    print("=" * 60)
    print("  FASE 7 - ANALISIS PENANGANAN REMOTE")
    print(f"  Input : {INPUT_FILE}")
    print(f"  Output: {OUTPUT_FILE}")
    print("=" * 60)

    data = load_csv(INPUT_FILE)
    print(f"\nMemuat {len(data)} pesan dari {INPUT_FILE.name}")

    data, conv_remote_labels, conv_cred_labels = assign_remote_labels(data)

    output = save_to_csv(data, OUTPUT_FILE)
    print(f"Hasil disimpan ke: {output}")

    validate(data, conv_remote_labels, conv_cred_labels)

    print("=" * 60)
    print("  FASE 7 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()
