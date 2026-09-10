"""
parser.py - WhatsApp Chat Parser untuk Project NLP Zahir

Fase 1: Parsing dasar (tanggal, waktu, pengirim, percakapan)
Fase 2: Deteksi dan mapping media ke pesan terkait

Membaca file export chat WhatsApp (.txt) dari data/raw/chat/,
menghubungkan media dari data/raw/media/chat_N/,
lalu menyimpan hasil parsing ke data/processed/chat_parsed.csv.

Format yang didukung:
    DD/MM/YY HH.MM - Pengirim: Pesan
    DD/MM/YY HH.MM - System Message (tanpa ':')

Pola media:
    <Media tidak disertakan>         -> media tidak tersedia
    NamaFile.jpg (file terlampir)    -> media tersedia, ada file fisik
"""

import re
import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "chat"
MEDIA_DIR = BASE_DIR / "data" / "raw" / "media"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "chat_parsed.csv"

INVISIBLE_CHARS = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]")

MESSAGE_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2})\s(\d{1,2}\.\d{2})\s-\s(.+?):\s(.*)"
)

SYSTEM_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2})\s(\d{1,2}\.\d{2})\s-\s(.+)"
)

DATE_START_PATTERN = re.compile(
    r"^\d{1,2}/\d{1,2}/\d{2}\s\d{1,2}\.\d{2}\s-\s"
)

MEDIA_OMITTED_PATTERN = re.compile(r"<Media tidak disertakan>|<Media omitted>")

FILE_ATTACHED_PATTERN = re.compile(r"(.+?)\s+\(file terlampir\)")


def clean_line(line):
    """Hapus karakter Unicode tak terlihat (LRM, RLM, dll)."""
    return INVISIBLE_CHARS.sub("", line)


def read_file(filepath):
    """Baca file dengan encoding UTF-8."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.readlines()


def get_media_files(source_file):
    """Dapatkan set nama file media yang tersedia untuk source_file tertentu.

    Mapping: chat_1.txt -> data/raw/media/chat_1/
             chat_2.txt -> data/raw/media/chat_2/
    """
    chat_name = Path(source_file).stem
    media_folder = MEDIA_DIR / chat_name
    if not media_folder.exists():
        return {}
    return {f.name: str(f.relative_to(BASE_DIR)) for f in media_folder.iterdir() if f.is_file()}


def detect_media(percakapan, media_files):
    """Deteksi informasi media dari isi percakapan.

    Returns:
        tuple: (media_type, media_path, has_media, percakapan_bersih)
    """
    if MEDIA_OMITTED_PATTERN.search(percakapan):
        return "image", "", True, percakapan

    match = FILE_ATTACHED_PATTERN.search(percakapan)
    if match:
        filename = match.group(1).strip()
        ext = Path(filename).suffix.lower()

        if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            media_type = "image"
        elif ext in (".mp4", ".3gp", ".avi", ".mov"):
            media_type = "video"
        elif ext in (".opus", ".mp3", ".aac", ".ogg"):
            media_type = "audio"
        elif ext in (".pdf", ".doc", ".docx", ".xls", ".xlsx"):
            media_type = "document"
        else:
            media_type = "file"

        media_path = media_files.get(filename, "")
        return media_type, media_path, True, percakapan

    return "", "", False, percakapan


def parse_lines(lines, source_file):
    """Parse baris-baris chat WhatsApp menjadi list of dict.

    Menangani:
    - Pesan biasa (tanggal - pengirim: pesan)
    - System message (tanggal - pesan tanpa pengirim)
    - Multiline message (baris tanpa tanggal digabung ke pesan sebelumnya)
    - Deteksi media (media omitted dan file terlampir)
    """
    media_files = get_media_files(source_file)
    messages = []
    current = None

    for line in lines:
        line = clean_line(line.rstrip("\n").rstrip("\r"))

        msg_match = MESSAGE_PATTERN.match(line)
        if msg_match:
            if current is not None:
                media_type, media_path, has_media, pesan = detect_media(
                    current["percakapan"], media_files
                )
                current["media_type"] = media_type
                current["media_path"] = media_path
                current["has_media"] = has_media
                messages.append(current)

            current = {
                "source_file": source_file,
                "tanggal": msg_match.group(1),
                "waktu": msg_match.group(2),
                "pengirim": msg_match.group(3).strip(),
                "percakapan": msg_match.group(4),
            }
            continue

        sys_match = SYSTEM_PATTERN.match(line)
        if sys_match and DATE_START_PATTERN.match(line):
            if current is not None:
                media_type, media_path, has_media, pesan = detect_media(
                    current["percakapan"], media_files
                )
                current["media_type"] = media_type
                current["media_path"] = media_path
                current["has_media"] = has_media
                messages.append(current)

            current = {
                "source_file": source_file,
                "tanggal": sys_match.group(1),
                "waktu": sys_match.group(2),
                "pengirim": "SYSTEM",
                "percakapan": sys_match.group(3),
            }
            continue

        if current is not None and line.strip() != "":
            current["percakapan"] += "\n" + line

    if current is not None:
        media_type, media_path, has_media, pesan = detect_media(
            current["percakapan"], media_files
        )
        current["media_type"] = media_type
        current["media_path"] = media_path
        current["has_media"] = has_media
        messages.append(current)

    return messages


def assign_ids(messages):
    """Tambahkan kolom id (1-based) ke setiap pesan."""
    for idx, msg in enumerate(messages, start=1):
        msg["id"] = idx
    return messages


def save_to_csv(messages, output_path):
    """Simpan list of dict ke CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id", "source_file", "tanggal", "waktu", "pengirim",
        "percakapan", "media_type", "media_path", "has_media",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(messages)
    return output_path


def get_txt_files(raw_dir):
    """Dapatkan semua file .txt dari direktori raw/chat."""
    raw_path = Path(raw_dir)
    txt_files = sorted(raw_path.glob("*.txt"))
    return txt_files


def validate(messages, file_counts):
    """Validasi hasil parsing dan cetak laporan."""
    total = len(messages)
    pengirim_unik = set()
    tanpa_tanggal = 0
    tanpa_waktu = 0
    tanpa_pengirim = 0
    pesan_kosong = 0
    pesan_multiline = 0
    pesan_has_media = 0
    pesan_media_omitted = 0
    pesan_file_terlampir = 0
    pesan_media_path_valid = 0

    for msg in messages:
        pengirim_unik.add(msg["pengirim"])
        if not msg.get("tanggal"):
            tanpa_tanggal += 1
        if not msg.get("waktu"):
            tanpa_waktu += 1
        if not msg.get("pengirim"):
            tanpa_pengirim += 1
        if not msg.get("percakapan") or msg["percakapan"].strip() == "":
            pesan_kosong += 1
        if "\n" in msg.get("percakapan", ""):
            pesan_multiline += 1
        if msg.get("has_media"):
            pesan_has_media += 1
            if msg.get("media_path"):
                pesan_file_terlampir += 1
                if (BASE_DIR / msg["media_path"]).exists():
                    pesan_media_path_valid += 1
            else:
                pesan_media_omitted += 1

    print("\n=== VALIDASI HASIL PARSING ===")
    print(f"Total pesan hasil parsing: {total}")
    print()
    print("Jumlah pesan per file:")
    for fname, count in file_counts.items():
        print(f"  {fname}: {count} pesan")
    print()
    print(f"Jumlah pengirim unik: {len(pengirim_unik)}")
    for p in sorted(pengirim_unik):
        print(f"  - {p}")
    print()
    print(f"Pesan tanpa tanggal : {tanpa_tanggal}")
    print(f"Pesan tanpa waktu   : {tanpa_waktu}")
    print(f"Pesan tanpa pengirim: {tanpa_pengirim}")
    print(f"Pesan kosong        : {pesan_kosong}")
    print(f"Pesan multiline     : {pesan_multiline}")
    print()
    print("=== VALIDASI MEDIA ===")
    print(f"Total pesan dengan media   : {pesan_has_media}")
    print(f"  Media omitted (no file)  : {pesan_media_omitted}")
    print(f"  File terlampir (ada file): {pesan_file_terlampir}")
    print(f"  File path valid (exists) : {pesan_media_path_valid}")
    print()

    return {
        "total": total,
        "file_counts": file_counts,
        "pengirim_unik": len(pengirim_unik),
        "tanpa_tanggal": tanpa_tanggal,
        "tanpa_waktu": tanpa_waktu,
        "tanpa_pengirim": tanpa_pengirim,
        "pesan_kosong": pesan_kosong,
        "pesan_multiline": pesan_multiline,
        "pesan_has_media": pesan_has_media,
        "pesan_media_omitted": pesan_media_omitted,
        "pesan_file_terlampir": pesan_file_terlampir,
        "pesan_media_path_valid": pesan_media_path_valid,
    }


def run():
    """Jalankan parser: baca semua .txt dari data/raw/chat, parse, simpan CSV."""
    txt_files = get_txt_files(RAW_DIR)

    if not txt_files:
        print(f"[ERROR] Tidak ada file .txt di {RAW_DIR}")
        return

    print("=== DATA INGESTION - PARSER ===")
    print(f"Direktori raw   : {RAW_DIR}")
    print(f"Direktori media : {MEDIA_DIR}")
    print(f"Output CSV      : {OUTPUT_FILE}")
    print(f"Jumlah file .txt ditemukan: {len(txt_files)}")
    print()

    all_messages = []
    file_counts = {}

    for fpath in txt_files:
        fname = fpath.name
        chat_name = fpath.stem
        media_folder = MEDIA_DIR / chat_name
        media_count = len(list(media_folder.glob("*"))) if media_folder.exists() else 0
        print(f"Memproses: {fname} ({fpath.stat().st_size:,} bytes)")
        print(f"  Media folder: {media_folder.name}/ ({media_count} file)")
        lines = read_file(fpath)
        messages = parse_lines(lines, fname)
        file_counts[fname] = len(messages)
        all_messages.extend(messages)
        print(f"  -> {len(messages)} pesan diekstrak")
        print()

    all_messages = assign_ids(all_messages)

    output = save_to_csv(all_messages, OUTPUT_FILE)
    print(f"Hasil parsing disimpan ke: {output}")

    validate(all_messages, file_counts)

    print("=== PARSER SELESAI ===")


if __name__ == "__main__":
    run()
