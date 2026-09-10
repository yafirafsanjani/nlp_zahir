"""
exploration.py - Data Understanding & Validation (Fase 3)

Membaca chat_parsed.csv dan melakukan:
- Eksplorasi data dasar
- Analisis panjang pesan
- Identifikasi konten khusus
- Cek duplikat
- Cek urutan waktu
- Cek konsistensi pengirim
- Statistik media
- Laporan dan rekomendasi
"""

import csv
from pathlib import Path
from collections import Counter
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "chat_parsed.csv"


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


def eksplorasi_dasar(data):
    """Eksplorasi data dasar."""
    print_header("1. EKSPLORASI DATA DASAR")

    total = len(data)
    print(f"Total pesan: {total}")
    print()

    file_counts = Counter(row["source_file"] for row in data)
    print("Distribusi per file:")
    for fname, count in file_counts.most_common():
        pct = count / total * 100
        print(f"  {fname}: {count} pesan ({pct:.1f}%)")
    print()

    pengirim_counts = Counter(row["pengirim"] for row in data)
    print("Distribusi per pengirim:")
    for pengirim, count in pengirim_counts.most_common():
        pct = count / total * 100
        print(f"  {pengirim}: {count} pesan ({pct:.1f}%)")
    print()

    pengirim_per_file = {}
    for row in data:
        key = (row["source_file"], row["pengirim"])
        pengirim_per_file[key] = pengirim_per_file.get(key, 0) + 1
    print("Distribusi pengirim per file:")
    current_file = None
    for (fname, pengirim), count in sorted(pengirim_per_file.items()):
        if fname != current_file:
            print(f"  {fname}:")
            current_file = fname
        print(f"    {pengirim}: {count} pesan")
    print()

    dates = []
    for row in data:
        dt = parse_datetime(row["tanggal"], row["waktu"])
        if dt:
            dates.append(dt)

    if dates:
        print(f"Rentang tanggal: {min(dates).strftime('%d/%m/%Y')} - {max(dates).strftime('%d/%m/%Y')}")
        unique_dates = set(d.date() for d in dates)
        print(f"Jumlah hari unik: {len(unique_dates)}")
        unique_months = set((d.year, d.month) for d in dates)
        print(f"Jumlah bulan unik: {len(unique_months)}")


def analisis_panjang_pesan(data):
    """Analisis panjang pesan."""
    print_header("2. ANALISIS PANJANG PESAN")

    lengths = []
    for row in data:
        pesan = row["percakapan"]
        lengths.append(len(pesan))

    if not lengths:
        print("Tidak ada data")
        return

    lengths_sorted = sorted(lengths)
    total = len(lengths)
    avg = sum(lengths) / total
    median = lengths_sorted[total // 2]

    print(f"Rata-rata panjang: {avg:.1f} karakter")
    print(f"Median panjang   : {median} karakter")
    print(f"Terpendek        : {min(lengths)} karakter")
    print(f"Terpanjang       : {max(lengths)} karakter")
    print()

    brackets = [
        (0, 0, "Kosong (0 char)"),
        (1, 10, "Sangat pendek (1-10)"),
        (11, 50, "Pendek (11-50)"),
        (51, 150, "Sedang (51-150)"),
        (151, 500, "Panjang (151-500)"),
        (501, float("inf"), "Sangat panjang (>500)"),
    ]
    print("Distribusi panjang pesan:")
    for low, high, label in brackets:
        count = sum(1 for l in lengths if low <= l <= high)
        pct = count / total * 100
        print(f"  {label}: {count} ({pct:.1f}%)")


def identifikasi_konten_khusus(data):
    """Identifikasi konten khusus."""
    print_header("3. IDENTIFIKASI KONTEN KHUSUS")

    media_omitted = []
    file_terlampir = []
    deleted_msg = []
    system_msg = []
    pesan_pendek = []
    pesan_url = []
    pesan_emoji_only = []

    for row in data:
        pesan = row["percakapan"]
        pengirim = row["pengirim"]

        if "<Media tidak disertakan>" in pesan or "<Media omitted>" in pesan:
            media_omitted.append(row)
        if "(file terlampir)" in pesan:
            file_terlampir.append(row)
        if any(kw in pesan for kw in [
            "Pesan ini telah dihapus",
            "This message was deleted",
            "You deleted this message",
            "Anda menghapus pesan ini",
        ]):
            deleted_msg.append(row)
        if pengirim == "SYSTEM":
            system_msg.append(row)
        if 0 < len(pesan.strip()) <= 5:
            pesan_pendek.append(row)
        if "http://" in pesan or "https://" in pesan:
            pesan_url.append(row)

    print(f"Media omitted (<Media tidak disertakan>): {len(media_omitted)}")
    print(f"File terlampir (ada file fisik)         : {len(file_terlampir)}")
    print(f"Pesan dihapus                           : {len(deleted_msg)}")
    print(f"System message                          : {len(system_msg)}")
    print(f"Pesan sangat pendek (1-5 char)          : {len(pesan_pendek)}")
    print(f"Pesan mengandung URL                    : {len(pesan_url)}")
    print()

    if system_msg:
        print("Detail system message:")
        for row in system_msg:
            pesan = row["percakapan"][:100]
            print(f"  [{row['source_file']}] {pesan}")
    print()

    if deleted_msg:
        print("Detail pesan dihapus:")
        for row in deleted_msg:
            print(f"  [{row['source_file']}] ID {row['id']}: {row['pengirim']}")
    print()

    if pesan_pendek:
        print(f"Contoh pesan sangat pendek (max 10):")
        for row in pesan_pendek[:10]:
            print(f"  ID {row['id']}: \"{row['percakapan']}\" ({row['pengirim']})")


def cek_duplikat(data):
    """Cek apakah ada pesan duplikat."""
    print_header("4. CEK DUPLIKAT")

    seen = {}
    duplicates = []
    for row in data:
        key = (row["source_file"], row["tanggal"], row["waktu"],
               row["pengirim"], row["percakapan"])
        if key in seen:
            duplicates.append((seen[key], row))
        else:
            seen[key] = row

    print(f"Jumlah pesan duplikat (exact match): {len(duplicates)}")
    if duplicates:
        print("Contoh duplikat (max 5):")
        for orig, dup in duplicates[:5]:
            print(f"  ID {orig['id']} & {dup['id']}: "
                  f"\"{dup['percakapan'][:60]}\" ({dup['pengirim']})")


def cek_urutan_waktu(data):
    """Cek apakah urutan waktu kronologis per file."""
    print_header("5. CEK URUTAN WAKTU")

    files = {}
    for row in data:
        fname = row["source_file"]
        if fname not in files:
            files[fname] = []
        files[fname].append(row)

    for fname, rows in files.items():
        anomalies = 0
        prev_dt = None
        anomaly_examples = []
        for row in rows:
            dt = parse_datetime(row["tanggal"], row["waktu"])
            if dt and prev_dt and dt < prev_dt:
                anomalies += 1
                if len(anomaly_examples) < 3:
                    anomaly_examples.append(
                        f"  ID {row['id']}: {row['tanggal']} {row['waktu']} "
                        f"< sebelumnya {prev_dt.strftime('%d/%m/%y %H.%M')}"
                    )
            if dt:
                prev_dt = dt

        status = "KRONOLOGIS" if anomalies == 0 else f"{anomalies} ANOMALI"
        print(f"{fname}: {status}")
        for ex in anomaly_examples:
            print(ex)
    print()


def cek_konsistensi_pengirim(data):
    """Cek konsistensi nama pengirim."""
    print_header("6. CEK KONSISTENSI PENGIRIM")

    pengirim_set = set(row["pengirim"] for row in data)
    print(f"Total pengirim unik: {len(pengirim_set)}")
    for p in sorted(pengirim_set):
        print(f"  - \"{p}\"")
    print()

    pengirim_list = sorted(pengirim_set - {"SYSTEM"})
    potential_issues = []
    for i, p1 in enumerate(pengirim_list):
        for p2 in pengirim_list[i + 1:]:
            p1_lower = p1.lower().strip()
            p2_lower = p2.lower().strip()
            if p1_lower in p2_lower or p2_lower in p1_lower:
                potential_issues.append((p1, p2))

    if potential_issues:
        print("Potensi nama pengirim mirip:")
        for p1, p2 in potential_issues:
            print(f"  \"{p1}\" <-> \"{p2}\"")
    else:
        print("Tidak ada potensi nama pengirim yang mirip/duplikat.")


def statistik_media(data):
    """Statistik media per pengirim."""
    print_header("7. STATISTIK MEDIA")

    media_per_pengirim = Counter()
    media_omitted_per_pengirim = Counter()
    file_terlampir_per_pengirim = Counter()

    for row in data:
        if row["has_media"] == "True":
            pengirim = row["pengirim"]
            media_per_pengirim[pengirim] += 1
            if row["media_path"]:
                file_terlampir_per_pengirim[pengirim] += 1
            else:
                media_omitted_per_pengirim[pengirim] += 1

    total_media = sum(media_per_pengirim.values())
    print(f"Total pesan media: {total_media}")
    print()
    print("Media per pengirim:")
    for pengirim, count in media_per_pengirim.most_common():
        omitted = media_omitted_per_pengirim.get(pengirim, 0)
        attached = file_terlampir_per_pengirim.get(pengirim, 0)
        print(f"  {pengirim}: {count} total ({attached} file ada, {omitted} omitted)")
    print()

    media_with_text = 0
    media_only = 0
    for row in data:
        if row["has_media"] == "True":
            pesan = row["percakapan"].strip()
            clean = pesan.replace("<Media tidak disertakan>", "").strip()
            if "(file terlampir)" in clean:
                idx = clean.find("(file terlampir)")
                after = clean[idx + len("(file terlampir)"):].strip()
                if after:
                    media_with_text += 1
                else:
                    media_only += 1
            elif clean:
                media_with_text += 1
            else:
                media_only += 1

    print(f"Media dengan teks tambahan : {media_with_text}")
    print(f"Media tanpa teks (only)    : {media_only}")


def rekomendasi(data):
    """Cetak rekomendasi untuk fase selanjutnya."""
    print_header("8. REKOMENDASI UNTUK FASE SELANJUTNYA")

    system_count = sum(1 for row in data if row["pengirim"] == "SYSTEM")
    media_omitted_count = sum(
        1 for row in data
        if "<Media tidak disertakan>" in row["percakapan"]
        or "<Media omitted>" in row["percakapan"]
    )
    deleted_count = sum(
        1 for row in data
        if any(kw in row["percakapan"] for kw in [
            "Pesan ini telah dihapus", "This message was deleted",
            "Anda menghapus pesan ini",
        ])
    )
    file_terlampir_count = sum(
        1 for row in data if "(file terlampir)" in row["percakapan"]
    )

    recommendations = []

    if system_count > 0:
        recommendations.append(
            f"- SYSTEM message ({system_count} pesan): pertimbangkan untuk "
            f"dipisahkan/dibuang dari analisis NLP, karena bukan percakapan."
        )

    if media_omitted_count > 0:
        recommendations.append(
            f"- Media omitted ({media_omitted_count} pesan): pesan ini tidak "
            f"punya konten teks berguna. Pertimbangkan untuk ditandai/difilter "
            f"saat training, tapi JANGAN dihapus karena bisa jadi konteks "
            f"dalam thread percakapan."
        )

    if file_terlampir_count > 0:
        recommendations.append(
            f"- File terlampir ({file_terlampir_count} pesan): file gambar "
            f"tersedia. Bisa digunakan untuk OCR/analisis visual di fase "
            f"lanjutan jika diperlukan."
        )

    if deleted_count > 0:
        recommendations.append(
            f"- Pesan dihapus ({deleted_count} pesan): tidak ada konten yang "
            f"bisa dianalisis. Pertimbangkan untuk ditandai."
        )

    recommendations.append(
        "- Fase 4 (Identifikasi Client & Admin): tentukan role berdasarkan "
        "nama pengirim. 'Zahir Surabaya' = ADMIN, sisanya = CLIENT."
    )

    recommendations.append(
        "- Fase 5 (Pembentukan Unit Percakapan): kelompokkan pesan menjadi "
        "conversation threads berdasarkan jeda waktu dan konteks."
    )

    for rec in recommendations:
        print(rec)
        print()


def run():
    """Jalankan seluruh eksplorasi data."""
    if not INPUT_FILE.exists():
        print(f"[ERROR] File tidak ditemukan: {INPUT_FILE}")
        print("Jalankan parser terlebih dahulu: python main.py")
        return

    print("=" * 60)
    print("  FASE 3 - DATA UNDERSTANDING & VALIDATION")
    print(f"  Input: {INPUT_FILE}")
    print("=" * 60)

    data = load_csv(INPUT_FILE)

    eksplorasi_dasar(data)
    analisis_panjang_pesan(data)
    identifikasi_konten_khusus(data)
    cek_duplikat(data)
    cek_urutan_waktu(data)
    cek_konsistensi_pengirim(data)
    statistik_media(data)
    rekomendasi(data)

    print("=" * 60)
    print("  FASE 3 SELESAI")
    print("=" * 60)


if __name__ == "__main__":
    run()
