"""
conversation.py - Pembentukan Unit Percakapan (Fase 5)

Membaca chat_with_roles.csv, menganalisis jeda waktu antar pesan,
mengelompokkan pesan menjadi conversation threads berdasarkan
threshold jeda waktu, lalu menyimpan ke chat_with_conversations.csv.

Langkah:
1. Analisis distribusi jeda waktu antar pesan per file
2. Tentukan threshold pemisah percakapan
3. Assign conversation_id ke setiap pesan
4. Validasi hasil pembentukan percakapan
"""

import csv
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "chat_with_roles.csv"
OUTPUT_FILE = PROCESSED_DIR / "chat_with_conversations.csv"

THRESHOLD_HOURS = None


def load_csv(filepath):
    """Baca CSV dan kembalikan list of dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def parse_datetime(tanggal, waktu):
    """Konversi tanggal DD/MM/YY dan waktu HH.MM ke datetime object."""
    try:
        return datetime.strptime(f"{tanggal} {waktu}", "%d/%m/%y %H.%M")
    except ValueError:
        return None


def print_header(title):
    """Cetak header section."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def analyze_time_gaps(data):
    """Analisis distribusi jeda waktu antar pesan per file.

    Menghitung jeda waktu antara setiap pesan berturut-turut
    dalam satu file, lalu menampilkan distribusinya.
    """
    print_header("LANGKAH 1: ANALISIS JEDA WAKTU ANTAR PESAN")

    files = {}
    for row in data:
        fname = row["source_file"]
        if fname not in files:
            files[fname] = []
        files[fname].append(row)

    all_gaps_minutes = []

    for fname, rows in sorted(files.items()):
        print(f"\n--- {fname} ---")
        gaps = []
        prev_dt = None

        for row in rows:
            dt = parse_datetime(row["tanggal"], row["waktu"])
            if dt and prev_dt:
                gap = dt - prev_dt
                gap_minutes = gap.total_seconds() / 60
                if gap_minutes >= 0:
                    gaps.append(gap_minutes)
                    all_gaps_minutes.append(gap_minutes)
            if dt:
                prev_dt = dt

        if not gaps:
            print("  Tidak ada data jeda waktu")
            continue

        brackets = [
            (0, 1, "0-1 menit"),
            (1, 5, "1-5 menit"),
            (5, 15, "5-15 menit"),
            (15, 30, "15-30 menit"),
            (30, 60, "30-60 menit"),
            (60, 120, "1-2 jam"),
            (120, 360, "2-6 jam"),
            (360, 720, "6-12 jam"),
            (720, 1440, "12-24 jam"),
            (1440, 4320, "1-3 hari"),
            (4320, 10080, "3-7 hari"),
            (10080, 43200, "1-4 minggu"),
            (43200, float("inf"), "> 1 bulan"),
        ]

        print(f"  Total jeda: {len(gaps)}")
        print(f"  Jeda terpendek: {min(gaps):.0f} menit")
        print(f"  Jeda terpanjang: {max(gaps):.0f} menit ({max(gaps)/60:.1f} jam / {max(gaps)/1440:.1f} hari)")
        print(f"  Rata-rata: {sum(gaps)/len(gaps):.0f} menit ({sum(gaps)/len(gaps)/60:.1f} jam)")
        print()
        print(f"  Distribusi jeda waktu:")
        for low, high, label in brackets:
            count = sum(1 for g in gaps if low <= g < high)
            if count > 0:
                pct = count / len(gaps) * 100
                bar = "#" * int(pct / 2)
                print(f"    {label:>15}: {count:4d} ({pct:5.1f}%) {bar}")

    print_header("RINGKASAN JEDA WAKTU (SEMUA FILE)")

    if not all_gaps_minutes:
        print("Tidak ada data")
        return all_gaps_minutes

    sorted_gaps = sorted(all_gaps_minutes)
    total = len(sorted_gaps)

    print(f"Total jeda: {total}")
    print(f"Jeda terpendek: {sorted_gaps[0]:.0f} menit")
    print(f"Jeda terpanjang: {sorted_gaps[-1]:.0f} menit ({sorted_gaps[-1]/1440:.1f} hari)")
    print()

    percentiles = [50, 75, 90, 95, 99]
    print("Percentile jeda waktu:")
    for p in percentiles:
        idx = int(total * p / 100)
        if idx >= total:
            idx = total - 1
        val = sorted_gaps[idx]
        print(f"  P{p}: {val:.0f} menit ({val/60:.1f} jam)")
    print()

    threshold_candidates = [1, 2, 3, 4, 6, 8, 12, 24]
    print("Simulasi jumlah percakapan per threshold:")
    print(f"  {'Threshold':>12} | {'Percakapan':>12} | {'Rata-rata pesan':>15}")
    print(f"  {'-'*12} | {'-'*12} | {'-'*15}")

    files_for_sim = {}
    for row in data:
        fname = row["source_file"]
        if fname not in files_for_sim:
            files_for_sim[fname] = []
        files_for_sim[fname].append(row)

    for hours in threshold_candidates:
        threshold_min = hours * 60
        total_convs = 0
        total_msgs = 0

        for fname, rows in files_for_sim.items():
            conv_count = 1
            prev_dt = None
            for row in rows:
                dt = parse_datetime(row["tanggal"], row["waktu"])
                if dt and prev_dt:
                    gap = (dt - prev_dt).total_seconds() / 60
                    if gap >= threshold_min:
                        conv_count += 1
                if dt:
                    prev_dt = dt
            total_convs += conv_count
            total_msgs += len(rows)

        avg_msgs = total_msgs / total_convs if total_convs > 0 else 0
        print(f"  {hours:>10} jam | {total_convs:>12} | {avg_msgs:>15.1f}")

    return all_gaps_minutes


def assign_conversations(data, threshold_hours):
    """Assign conversation_id ke setiap pesan berdasarkan threshold.

    Aturan:
    - Pesan SYSTEM di awal file (sebelum pesan pertama CLIENT/ADMIN)
      mendapat conversation_id tersendiri
    - Pesan pertama non-SYSTEM di file = mulai percakapan baru
    - Jika jeda ke pesan berikutnya >= threshold -> percakapan baru
    - Format: chat_1_conv_001, chat_1_conv_002, dst.
    """
    threshold_min = threshold_hours * 60

    files = {}
    for row in data:
        fname = row["source_file"]
        if fname not in files:
            files[fname] = []
        files[fname].append(row)

    for fname, rows in sorted(files.items()):
        chat_name = Path(fname).stem
        conv_num = 0
        prev_dt = None

        for row in rows:
            dt = parse_datetime(row["tanggal"], row["waktu"])

            if row["role"] == "SYSTEM":
                if conv_num == 0:
                    conv_num = 1
                row["conversation_id"] = f"{chat_name}_conv_{conv_num:03d}"
                continue

            if prev_dt is None:
                conv_num += 1 if conv_num == 0 else 0
                if conv_num == 0:
                    conv_num = 1
            elif dt and prev_dt:
                gap = (dt - prev_dt).total_seconds() / 60
                if gap >= threshold_min:
                    conv_num += 1

            row["conversation_id"] = f"{chat_name}_conv_{conv_num:03d}"

            if dt:
                prev_dt = dt

    return data


def save_to_csv(data, output_path):
    """Simpan list of dict ke CSV dengan kolom conversation_id."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id", "conversation_id", "source_file", "tanggal", "waktu",
        "pengirim", "role", "percakapan", "media_type", "media_path",
        "has_media",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return output_path


def validate(data):
    """Validasi hasil pembentukan percakapan."""
    print_header("VALIDASI HASIL PEMBENTUKAN PERCAKAPAN")

    total = len(data)
    conv_ids = set(row["conversation_id"] for row in data)
    total_convs = len(conv_ids)

    print(f"Total pesan: {total}")
    print(f"Total percakapan: {total_convs}")
    print(f"Rata-rata pesan per percakapan: {total / total_convs:.1f}")
    print()

    conv_per_file = {}
    for row in data:
        fname = row["source_file"]
        conv_id = row["conversation_id"]
        if fname not in conv_per_file:
            conv_per_file[fname] = set()
        conv_per_file[fname].add(conv_id)

    print("Percakapan per file:")
    for fname, convs in sorted(conv_per_file.items()):
        msgs_in_file = sum(1 for row in data if row["source_file"] == fname)
        print(f"  {fname}: {len(convs)} percakapan ({msgs_in_file} pesan)")
    print()

    conv_sizes = Counter(row["conversation_id"] for row in data)
    sizes = list(conv_sizes.values())
    sizes_sorted = sorted(sizes)

    print(f"Pesan per percakapan:")
    print(f"  Terpendek : {min(sizes)} pesan")
    print(f"  Terpanjang: {max(sizes)} pesan")
    print(f"  Median    : {sizes_sorted[len(sizes_sorted)//2]} pesan")
    print()

    brackets = [
        (1, 1, "1 pesan"),
        (2, 5, "2-5 pesan"),
        (6, 15, "6-15 pesan"),
        (16, 30, "16-30 pesan"),
        (31, 50, "31-50 pesan"),
        (51, float("inf"), "> 50 pesan"),
    ]
    print("Distribusi ukuran percakapan:")
    for low, high, label in brackets:
        count = sum(1 for s in sizes if low <= s <= high)
        if count > 0:
            pct = count / len(sizes) * 100
            print(f"  {label:>12}: {count} percakapan ({pct:.1f}%)")
    print()

    no_conv = sum(1 for row in data if not row.get("conversation_id"))
    print(f"Pesan tanpa conversation_id: {no_conv}")

    single_msg_convs = [cid for cid, count in conv_sizes.items() if count == 1]
    if single_msg_convs:
        print(f"\nPercakapan dengan hanya 1 pesan ({len(single_msg_convs)}):")
        for cid in single_msg_convs[:10]:
            row = next(r for r in data if r["conversation_id"] == cid)
            pesan = row["percakapan"][:60]
            print(f"  {cid}: [{row['role']}] {pesan}")
    print()

    conv_roles = {}
    for row in data:
        cid = row["conversation_id"]
        if cid not in conv_roles:
            conv_roles[cid] = set()
        conv_roles[cid].add(row["role"])

    admin_only = sum(1 for roles in conv_roles.values() if roles == {"ADMIN"})
    client_only = sum(1 for roles in conv_roles.values() if roles == {"CLIENT"})
    system_only = sum(1 for roles in conv_roles.values() if roles == {"SYSTEM"})
    both = sum(1 for roles in conv_roles.values() if "ADMIN" in roles and "CLIENT" in roles)

    print("Komposisi role per percakapan:")
    print(f"  ADMIN + CLIENT (dialog): {both}")
    print(f"  Hanya ADMIN            : {admin_only}")
    print(f"  Hanya CLIENT           : {client_only}")
    print(f"  Hanya SYSTEM           : {system_only}")


def run_analyze():
    """Jalankan hanya analisis jeda waktu (sebelum menentukan threshold)."""
    if not INPUT_FILE.exists():
        print(f"[ERROR] File tidak ditemukan: {INPUT_FILE}")
        print("Jalankan fase 4 terlebih dahulu: python main.py roles")
        return

    print("=" * 60)
    print("  FASE 5 - ANALISIS JEDA WAKTU")
    print(f"  Input: {INPUT_FILE}")
    print("=" * 60)

    data = load_csv(INPUT_FILE)
    print(f"\nMemuat {len(data)} pesan")

    analyze_time_gaps(data)

    print()
    print("=" * 60)
    print("  Tentukan threshold berdasarkan data di atas.")
    print("  Lalu jalankan: python main.py conversations <jam>")
    print("  Contoh: python main.py conversations 4")
    print("=" * 60)


def run(threshold_hours=None):
    """Jalankan pembentukan percakapan dengan threshold tertentu."""
    if threshold_hours is None:
        run_analyze()
        return

    if not INPUT_FILE.exists():
        print(f"[ERROR] File tidak ditemukan: {INPUT_FILE}")
        print("Jalankan fase 4 terlebih dahulu: python main.py roles")
        return

    print("=" * 60)
    print("  FASE 5 - PEMBENTUKAN UNIT PERCAKAPAN")
    print(f"  Input    : {INPUT_FILE}")
    print(f"  Output   : {OUTPUT_FILE}")
    print(f"  Threshold: {threshold_hours} jam")
    print("=" * 60)

    data = load_csv(INPUT_FILE)
    print(f"\nMemuat {len(data)} pesan")

    data = assign_conversations(data, threshold_hours)

    output = save_to_csv(data, OUTPUT_FILE)
    print(f"Hasil disimpan ke: {output}")

    validate(data)

    print()
    print("=" * 60)
    print("  FASE 5 SELESAI")
    print("=" * 60)


if __name__ == "__main__":
    run()
