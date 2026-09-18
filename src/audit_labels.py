"""
audit_labels.py - Audit Non-Destruktif Ground Truth Hasil LLM

Memindai data/processed/llm_labels.csv dan mengelompokkan setiap label menjadi:
    KONSISTEN            - label selaras dengan sinyal teks
    AMBIGU               - ada sinyal dua arah / teks kunci rendah, perlu cek manual
    BERISIKO_SALAH       - indikasi kuat label tidak sesuai definisi kategori
                           (contoh: teks ber-IP/firewall tapi dinilai PERTANYAAN_UMUM_FITUR,
                           atau kerusakan database tapi dilabel INSTALASI_SETUP_NETWORK)

Audit ini TIDAK mengubah ground truth. Output hanya laporan diagnostik:
    data/processed/label_audit.csv

Penilaian memakai heuristik sinyal kata (bukan alasan tunggal) sebagai ALARM
untuk review manusia/LLM ulang — bukan keputusan final.
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "llm_labels.csv"
OUTPUT_FILE = PROCESSED_DIR / "label_audit.csv"

# sinyal: indikator masalah aktif yang sedang ditangani (bukan sekadar kata kunci)
ACTIVE_PROBLEM = re.compile(
    r"tidak\s+bisa|tdk\s+bisa|gak\s+bisa|nggak\s+bisa|ga\s+bisa|tidak\s+terhubung|"
    r"tidak\s+konek|tidak\s+connect|\bgagal\b|\berror\b|loading\s*lama|\bgantung\b|"
    r"\bhang\b|\bcrash\b|\bcorrupt\b|\brusak\b|\bmati\b|\bputus\b|\btidak\s+terbaca\b|"
    r"\btdk\s+connect\b|\bmacul\b|\btidak\s+jalan\b|\bgak\s+jalan\b|\bbermasalah\b"
)

# sinyal topik jaringan/server-client
NET_SIGNAL = re.compile(
    r"\bip\b|\balamat\s+ip\b|\blan\b|\bjaringan\b|\bnetwork\b|\bfirewall\b|"
    r"\bserver\b|\bclient\b|\bkonek|\bconnect\b|\bterhubung\b|\bsharing\b|"
    r"\bremote\b|\brouter\b|\banak\b|\binduk\b|\bzahir\s+server\b"
)

# sinyal kerusakan/error internal database
DB_SIGNAL = re.compile(
    r"\bcorrupt\b|\bdatabase\b|\bdb\b|\bfirebird\b|\brtd\b|\baccess\s+violation\b|"
    r"\btable\b|\bkernel\b|\bengine\b|\bbasis\s+data\b|\btidak\s+bisa\s+dibuka\b|"
    r"\bdata\s+rusak\b"
)

# sinyal kerusakan/error internal database
DB_SIGNAL = re.compile(
    r"\bcorrupt\b|\bdatabase\b|\bdb\b|\bfirebird\b|\brtd\b|\baccess\s+violation\b|"
    r"\btable\b|\bkernel\b|\bengine\b|\bbasis\s+data\b|\btidak\s+bisa\s+dibuka\b|"
    r"\blog\b|\bdata\s+rusak\b"
)

# pola pertanyaan penggunaan biasa (reported-seek)
QUESTION_PATTERN = re.compile(
    r"\bapa\s+itu\b|\bapa\.?\b.*\bitu\b|\bapa\s+enaknya\b|\bbagaimana\s+cara\b|"
    r"\bgimana\s+cara\b|\bcaranya\b|\bcara\s+menggunakan\b|"
    r"\bbisa\s+(nggak|gak|ngga|ga|tidak)\b|\btanya\b|\bminta\s+penjelasan\b|"
    r"\bpanduan\b|\btutorial\b"
)

ISSUE_LABELS = {
    "PERTANYAAN_UMUM_FITUR",
    "INSTALASI_SETUP_NETWORK",
    "DATABASE_SYSTEM_ERROR",
    "LISENSI_DONGLE_REGISTRASI",
    "LAPORAN_REPORTING",
    "TRANSAKSI_INPUT_DATA",
    "LAINNYA_UNCATEGORIZED",
}


def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def classify(ilabel, text):
    """
    Mengembalikan (verdict, signals, note).
    verdict: KONSISTEN / AMBIGU / BERISIKO_SALAH
    """
    signals = []
    if NET_SIGNAL.search(text):
        signals.append("network")
    if DB_SIGNAL.search(text):
        signals.append("database")
    has_active = bool(ACTIVE_PROBLEM.search(text))
    is_question = bool(QUESTION_PATTERN.search(text))
    if has_active:
        signals.append("masalah_aktif")

    low_text = len(text.strip()) < 12
    has_signal = bool(signals)

    # ---- aturan deteksi "berisiko salah"
    # (1) teks berindikasi jaringan + DB + masalah aktif, tapi dilabel pertanyaan umum
    if ilabel == "PERTANYAAN_UMUM_FITUR" and has_active and ("network" in signals):
        return ("BERISIKO_SALAH", signals,
                "Konteks masalah aktif jaringan (IP/firewall/server) tapi dilabel pertanyaan umum.")
    if ilabel == "PERTANYAAN_UMUM_FITUR" and has_active and ("database" in signals):
        return ("BERISIKO_SALAH", signals,
                "Konteks masalah aktif database tapi dilabel pertanyaan umum.")
    # (2) kerusakan database tapi dilabel jaringan
    if ilabel == "INSTALASI_SETUP_NETWORK" and re.search(
        r"corrupt|rusak|tidak\s+bisa\s+dibuka|firebird|engine|access\s+violation",
        text,
    ):
        return ("BERISIKO_SALAH", signals,
                "Indikasi kerusakan/error internal database tapi dilabel INSTALASI_SETUP_NETWORK.")
    # (3) pertanyaan panduan murni tapi dilabel jaringan
    if ilabel == "INSTALASI_SETUP_NETWORK" and is_question and not has_active:
        return ("BERISIKO_SALAH", signals,
                "Pola pertanyaan panduan ('bagaimana cara'/'apa itu') tanpa masalah aktif "
                "tapi dilabel INSTALASI_SETUP_NETWORK.")
    # (4) teks sangat pendek yang ber-network-signal dilabel fallback
    if ilabel == "LAINNYA_UNCATEGORIZED" and has_active and has_signal:
        return ("BERISIKO_SALAH", signals,
                "Ada indikasi masalah aktif dengan sinyal topik tapi masuk LAINNYA_UNCATEGORIZED.")

    # ---- aturan "ambigu"
    if ilabel == "INSTALASI_SETUP_NETWORK" and ("database" in signals) and not has_active:
        return ("AMBIGU", signals,
                "Memuat sinyal database & jaringan tanpa tanda masalah aktif; cek manual.")
    if ilabel == "DATABASE_SYSTEM_ERROR" and ("network" in signals) and not has_active:
        return ("AMBIGU", signals,
                "Memuat sinyal database & jaringan tanpa tanda masalah aktif; cek manual.")
    if ilabel == "PERTANYAAN_UMUM_FITUR" and is_question and has_signal:
        # pertanyaan namun menyentuh topik teknis tertentu -> perlu dicek kechat
        return ("AMBIGU", signals, "Pertanyaan namun menyentuh topik teknis tertentu.")
    if ilabel in ("PERTANYAAN_UMUM_FITUR", "LAINNYA_UNCATEGORIZED") and low_text:
        return ("AMBIGU", signals, "Teks terlalu pendek/umum untuk dipastikan.")

    # ---- sisanya konsisten
    return ("KONSISTEN", signals, "Selaras dengan sinyal teks.")


def run(input_path=None, limit=None):
    path = Path(input_path) if input_path else INPUT_FILE
    if not path.exists():
        print(f"[ERROR] File tidak ditemukan: {path}")
        print("Jalankan LLM labeling dulu: python main.py llm-label")
        return

    rows = load_csv(path)
    if limit:
        rows = rows[:limit]
    print("=" * 60)
    print("  AUDIT GROUND TRUTH HASIL LLM (non-destruktif)")
    print(f"  Input : {path.name}")
    print(f"  Output: {OUTPUT_FILE}")
    print("=" * 60)

    cat_counter = Counter()
    verdict_counter = Counter()
    detail = []

    for r in rows:
        ilabel = (r.get("kategori_llm") or r.get("kategori") or "").strip()
        text = r.get("client_text") or r.get("raw_text") or ""
        verdict, signals, note = classify(ilabel, text)
        cat_counter[ilabel] += 1
        verdict_counter[verdict] += 1
        detail.append(
            {
                "sub_conversation_id": r.get("sub_conversation_id", ""),
                "kategori_llm": ilabel,
                "verdict": verdict,
                "signals": ";".join(signals),
                "note": note,
                "confidence": r.get("confidence", ""),
                "reason": r.get("reason", r.get("evidence", "")),
                "main_issue": r.get("main_issue", ""),
                "client_text": text,
            }
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sub_conversation_id", "kategori_llm", "verdict", "signals",
                "note", "confidence", "reason", "main_issue", "client_text",
            ],
        )
        writer.writeheader()
        writer.writerows(detail)

    print("\n=== DISTRIBUSI LABEL ===")
    for cat, n in cat_counter.most_common():
        print(f"  - {cat:<30}: {n:>3} ({n/len(detail)*100:.1f}%)")

    print("\n=== HASIL AUDIT ===")
    for v in ("KONSISTEN", "AMBIGU", "BERISIKO_SALAH"):
        print(f"  - {v:<16}: {verdict_counter.get(v, 0)}")

    risky = [d for d in detail if d["verdict"] == "BERISIKO_SALAH"]
    print(f"\n>>> {len(risky)} label berisiko salah (tidak diubah, hanya ditandai).")
    print(f"    Daftar lengkap di: {OUTPUT_FILE}\n")

    print("CONTOH BERISIKO SALAH (max 8):")
    for d in risky[:8]:
        print(f"  - {d['sub_conversation_id']:<24} label={d['kategori_llm']:<26} {d['note']}")
        print(f"    teks: {d['client_text'][:100]}")
    print()
    print("=" * 60)
    print("  AUDIT SELESAI — ground truth TIDAK diubah")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit ground truth LLM")
    parser.add_argument("--input", default=None, help="Path ke csv label alternatif")
    parser.add_argument("--limit", type=int, default=None, help="Batas jumlah baris (debug)")
    args = parser.parse_args()
    run(input_path=args.input, limit=args.limit)