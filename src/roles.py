"""
roles.py - Identifikasi Client & Admin (Fase 4)

Membaca chat_parsed.csv, menambahkan kolom 'role' berdasarkan
mapping nama pengirim, lalu menyimpan ke chat_with_roles.csv.

Mapping role:
    Zahir Surabaya     -> ADMIN
    CV Omega Sejahtera -> CLIENT
    riza Bravo Eterna  -> CLIENT
    Rosaria / DAYARA   -> CLIENT
    SYSTEM             -> SYSTEM

Pengirim baru yang belum terdaftar akan ditandai UNKNOWN
dan dilaporkan agar bisa ditentukan secara manual.
"""

import csv
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "chat_parsed.csv"
OUTPUT_FILE = PROCESSED_DIR / "chat_with_roles.csv"

ROLE_MAP = {
    "Zahir Surabaya": "ADMIN",
    "CV Omega Sejahtera": "CLIENT",
    "riza Bravo Eterna": "CLIENT",
    "Rosaria / DAYARA": "CLIENT",
    "SYSTEM": "SYSTEM",
}


def load_csv(filepath):
    """Baca CSV dan kembalikan list of dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def assign_roles(data):
    """Tambahkan kolom 'role' ke setiap baris berdasarkan ROLE_MAP.

    Pengirim yang tidak ada di ROLE_MAP akan mendapat role 'UNKNOWN'.
    """
    unknown_senders = set()

    for row in data:
        pengirim = row["pengirim"]
        role = ROLE_MAP.get(pengirim, None)

        if role is None:
            role = "UNKNOWN"
            unknown_senders.add(pengirim)

        row["role"] = role

    return data, unknown_senders


def save_to_csv(data, output_path):
    """Simpan list of dict ke CSV dengan kolom role."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id", "source_file", "tanggal", "waktu", "pengirim", "role",
        "percakapan", "media_type", "media_path", "has_media",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return output_path


def validate(data_before, data_after, unknown_senders):
    """Validasi hasil penambahan role."""
    print("\n=== VALIDASI FASE 4 ===")

    total_before = len(data_before)
    total_after = len(data_after)
    print(f"Total pesan sebelum : {total_before}")
    print(f"Total pesan sesudah : {total_after}")
    print(f"Data konsisten      : {'YA' if total_before == total_after else 'TIDAK'}")
    print()

    role_counts = Counter(row["role"] for row in data_after)
    print("Distribusi role:")
    for role, count in role_counts.most_common():
        pct = count / total_after * 100
        print(f"  {role}: {count} pesan ({pct:.1f}%)")
    print()

    role_per_file = {}
    for row in data_after:
        key = (row["source_file"], row["role"])
        role_per_file[key] = role_per_file.get(key, 0) + 1
    print("Distribusi role per file:")
    current_file = None
    for (fname, role), count in sorted(role_per_file.items()):
        if fname != current_file:
            print(f"  {fname}:")
            current_file = fname
        print(f"    {role}: {count} pesan")
    print()

    pengirim_role = {}
    for row in data_after:
        pengirim = row["pengirim"]
        role = row["role"]
        if pengirim not in pengirim_role:
            pengirim_role[pengirim] = set()
        pengirim_role[pengirim].add(role)

    print("Mapping pengirim -> role:")
    for pengirim, roles in sorted(pengirim_role.items()):
        roles_str = ", ".join(sorted(roles))
        status = "OK" if len(roles) == 1 else "KONFLIK"
        print(f"  {pengirim} -> {roles_str} [{status}]")
    print()

    no_role = sum(1 for row in data_after if not row.get("role"))
    print(f"Pesan tanpa role: {no_role}")

    if unknown_senders:
        print()
        print(f"[PERINGATAN] Pengirim UNKNOWN ({len(unknown_senders)}):")
        for s in sorted(unknown_senders):
            print(f"  - \"{s}\"")
        print("  Tambahkan pengirim ini ke ROLE_MAP di src/roles.py")
    else:
        print("Semua pengirim berhasil di-mapping ke role.")
    print()


def run():
    """Jalankan Fase 4: assign role ke setiap pesan."""
    if not INPUT_FILE.exists():
        print(f"[ERROR] File tidak ditemukan: {INPUT_FILE}")
        print("Jalankan parser terlebih dahulu: python main.py")
        return

    print("=" * 60)
    print("  FASE 4 - IDENTIFIKASI CLIENT & ADMIN")
    print(f"  Input : {INPUT_FILE}")
    print(f"  Output: {OUTPUT_FILE}")
    print("=" * 60)

    data_before = load_csv(INPUT_FILE)
    print(f"\nMemuat {len(data_before)} pesan dari {INPUT_FILE.name}")

    print("\nMapping role yang digunakan:")
    for pengirim, role in sorted(ROLE_MAP.items()):
        print(f"  {pengirim} -> {role}")

    data_after, unknown_senders = assign_roles(data_before)

    output = save_to_csv(data_after, OUTPUT_FILE)
    print(f"\nHasil disimpan ke: {output}")

    validate(data_before, data_after, unknown_senders)

    print("=" * 60)
    print("  FASE 4 SELESAI")
    print("=" * 60)


if __name__ == "__main__":
    run()
