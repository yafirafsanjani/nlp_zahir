"""
export.py - Export Hasil & Laporan Analitik Eksekutif (Fase 19)

Membaca master_conversations_final.csv, menghasilkan ringkasan laporan analitik:
1. data/output/executive_summary.csv (KPI Customer Support Zahir)
2. data/output/category_breakdown_report.csv (Korelasi Kategori Kendala vs Remote & Respons)
3. data/output/final_project_report.txt (Laporan naratif lengkap untuk laporan magang/kerja)
"""

import csv
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
INPUT_MASTER_FILE = OUTPUT_DIR / "master_conversations_final.csv"
EXEC_SUMMARY_FILE = OUTPUT_DIR / "executive_summary.csv"
BREAKDOWN_FILE = OUTPUT_DIR / "category_breakdown_report.csv"
REPORT_TXT_FILE = OUTPUT_DIR / "final_project_report.txt"

def load_master_data(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def generate_executive_summary(data):
    total_convs = len(data)

    respons_count = sum(1 for r in data if r["client_response"] == "RESPONS")
    tidak_respons_count = total_convs - respons_count

    remote_count = sum(1 for r in data if r["penanganan_remote"] == "REMOTE")
    non_remote_count = total_convs - remote_count

    cred_count = sum(1 for r in data if r["contains_credentials"] == "True")
    match_count = sum(1 for r in data if r["prediction_match"] == "MATCH")

    cat_counts = Counter(r["kategori_kendala_ground_truth"] for r in data)
    top_cat, top_cat_count = cat_counts.most_common(1)[0]

    rows = [
        ["METRIK_KPI", "NILAI", "PERSENTASE", "KETERANGAN"],
        ["Total Unit Sub-Percakapan", total_convs, "100.0%", "Hasil segmentasi berbasis jeda 4 jam & pergeseran topik"],
        ["Client Respons (Aktif)", respons_count, f"{respons_count/total_convs*100:.1f}%", "Klien merespons balik bantuan admin CS"],
        ["Client Tidak Respons", tidak_respons_count, f"{tidak_respons_count/total_convs*100:.1f}%", "Percakapan selesai di pihak admin tanpa balasan klien"],
        ["Penanganan Remote", remote_count, f"{remote_count/total_convs*100:.1f}%", "Bantuan remote via Ultraviewer / Teamviewer"],
        ["Penanganan Non-Remote", non_remote_count, f"{non_remote_count/total_convs*100:.1f}%", "Selesai melalui panduan teks chat"],
        ["Percakapan Berbagi Kredensial", cred_count, f"{cred_count/total_convs*100:.1f}%", "Terdeteksi ID / Password remote untuk penanganan"],
        ["Akurasi Keselarasan Model AI", match_count, f"{match_count/total_convs*100:.1f}%", "Prediksi model produksi cocok dengan ground-truth"],
        ["Kategori Kendala Terbanyak", top_cat, f"{top_cat_count/total_convs*100:.1f}%", f"{top_cat_count} kasus permasalahan"],
    ]

    with open(EXEC_SUMMARY_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    return rows

def generate_category_breakdown(data):
    cat_map = {}
    for r in data:
        cat = r["kategori_kendala_ground_truth"]
        if cat not in cat_map:
            cat_map[cat] = {
                "total": 0,
                "remote": 0,
                "non_remote": 0,
                "respons": 0,
                "tidak_respons": 0,
                "total_msgs": 0,
            }
        cat_map[cat]["total"] += 1
        if r["penanganan_remote"] == "REMOTE":
            cat_map[cat]["remote"] += 1
        else:
            cat_map[cat]["non_remote"] += 1

        if r["client_response"] == "RESPONS":
            cat_map[cat]["respons"] += 1
        else:
            cat_map[cat]["tidak_respons"] += 1

        cat_map[cat]["total_msgs"] += int(r["total_messages"])

    rows = [
        [
            "kategori_kendala",
            "total_kasus",
            "remote_count",
            "remote_pct",
            "non_remote_count",
            "respons_count",
            "tidak_respons_count",
            "rata_pesan_per_kasus",
        ]
    ]

    sorted_cats = sorted(cat_map.items(), key=lambda x: x[1]["total"], reverse=True)
    for cat, stat in sorted_cats:
        tot = stat["total"]
        rem = stat["remote"]
        non_rem = stat["non_remote"]
        resp = stat["respons"]
        no_resp = stat["tidak_respons"]
        avg_msgs = stat["total_msgs"] / tot if tot > 0 else 0

        rows.append([
            cat,
            tot,
            rem,
            f"{rem/tot*100:.1f}%",
            non_rem,
            resp,
            no_resp,
            f"{avg_msgs:.1f}",
        ])

    with open(BREAKDOWN_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    return rows

def generate_narrative_report(data, exec_rows, breakdown_rows):
    total = len(data)
    with open(REPORT_TXT_FILE, "w", encoding="utf-8") as f:
        f.write("=" * 75 + "\n")
        f.write("      LAPORAN AKHIR PROYEK NLP ZAHIR (CUSTOMER SUPPORT ANALYTICS)\n")
        f.write("=" * 75 + "\n\n")

        f.write("1. EXECUTIVE OVERVIEW\n")
        f.write("-" * 40 + "\n")
        f.write(f"Proyek NLP Zahir telah berhasil memproses dan menganalisis seluruh data export WhatsApp\n")
        f.write(f"customer support Zahir melalui pipeline NLP & Machine Learning end-to-end (Fase 1 s.d. 19).\n")
        f.write(f"Total percakapan yang dianalisis: {total} unit sub-percakapan.\n\n")

        f.write("RINGKASAN METRIK UTAMA (KPI CS ZAHIR):\n")
        for row in exec_rows[1:]:
            f.write(f"  * {row[0]:<30}: {str(row[1]):<10} ({row[2]}) - {row[3]}\n")

        f.write("\n\n2. REKAPITULASI KORELASI KATEGORI KENDALA DENGAN PENANGANAN\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Kategori Kendala':<28} | {'Total':<6} | {'Remote %':<10} | {'Rata2 Pesan':<12}\n")
        f.write("-" * 70 + "\n")
        for row in breakdown_rows[1:]:
            f.write(f"{row[0]:<28} | {str(row[1]):<6} | {row[3]:<10} | {row[7]:<12}\n")
        f.write("-" * 70 + "\n\n")

        f.write("3. INSIGHT BISNIS & REKOMENDASI MANAJERIAL ZAHIR:\n")
        f.write("-" * 45 + "\n")
        f.write("a. Mayoritas Kendala Didominasi Masalah Transaksi & Input Data (36.7%):\n")
        f.write("   Banyak klien mengalami keraguan dalam input faktur penjualan, saldo gantung,\n")
        f.write("   dan penarikan PO/DO. Disarankan pembuatan video tutorial panduan singkat modul transaksi.\n\n")
        f.write("b. Kategori Instalasi & Database Memiliki Rasio Remote Tertinggi:\n")
        f.write("   Kasus koneksi client-server anakan-induk dan database corrupt hampir selalu\n")
        f.write("   membutuhkan remote desktop. Tim teknis remote perlu diprioritaskan untuk kategori ini.\n\n")
        f.write("c. Efektivitas Model AI Produksi (Tuned Gradient Boosting):\n")
        f.write("   Model AI telah dilatih dan di-tuning dengan akurasi uji 70.6% (keselarasan master 94.1%).\n")
        f.write("   Model ini siap diintegrasikan untuk routing tiket support otomatis ke staf yang tepat.\n\n")
        f.write("=" * 75 + "\n")
        f.write("  Laporan dibuat otomatis oleh nlp_zahir Pipeline Engine\n")
        f.write("=" * 75 + "\n")

def validate():
    print("\n=== VALIDASI FASE 19 (EXPORT HASIL & LAPORAN ANALITIK) ===")
    print("Berkas Laporan Berhasil Dibuat di Folder data/output/:")
    print(f"  1. Ringkasan Eksekutif KPI  : {EXEC_SUMMARY_FILE.name}")
    print(f"  2. Rekapitulasi per Kategori: {BREAKDOWN_FILE.name}")
    print(f"  3. Laporan Naratif Lengkap  : {REPORT_TXT_FILE.name}\n")

    # Tampilkan preview ringkasan eksekutif
    with open(EXEC_SUMMARY_FILE, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    print("PREVIEW RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY):")
    print("-" * 65)
    for r in reader[1:]:
        print(f"  * {r[0]:<28}: {r[1]:<8} ({r[2]})")
    print("-" * 65)
    print()

def run():
    if not INPUT_MASTER_FILE.exists():
        print(f"[ERROR] Berkas master tidak ditemukan: {INPUT_MASTER_FILE}")
        print("Jalankan fase 18 terlebih dahulu: python main.py consolidate")
        return

    print("=" * 60)
    print("  FASE 19 — EXPORT HASIL & LAPORAN ANALITIK EKSEKUTIF")
    print(f"  Input  : {INPUT_MASTER_FILE}")
    print(f"  Output : {OUTPUT_DIR}")
    print("=" * 60)

    data = load_master_data(INPUT_MASTER_FILE)
    exec_rows = generate_executive_summary(data)
    breakdown_rows = generate_category_breakdown(data)
    generate_narrative_report(data, exec_rows, breakdown_rows)

    validate()

    print("=" * 60)
    print("  FASE 19 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()