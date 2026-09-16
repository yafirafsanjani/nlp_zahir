"""
pipeline.py - Full Automation Pipeline (Fase 20)

Mengotomatisasi seluruh alur kerja proyek NLP Zahir secara sekuensial end-to-end:
1. Ingestion & WhatsApp Parsing (Fase 1 & 2)
2. Role Identification ADMIN, CLIENT, SYSTEM (Fase 4)
3. Pembentukan Unit Percakapan Jeda 4 Jam (Fase 5)
4. Analisis Respons Klien (Fase 6)
5. Analisis Penanganan Remote & Kredensial (Fase 7)
6. Sub-Conversation Topic Splitting & Ground Truth Labeling (Fase 9)
7. Text Preprocessing & Aggregation (Fase 10)
8. Cascaded Normalization (indo-normalizer + Kamus Zahir) (Fase 11)
9. Ekstraksi Fitur TF-IDF Unigram & Bigram (Fase 12)
10. Stratified Train-Test Split 80/20 (Fase 13)
11. Training Model 7 Algoritma & Cross-Validation (Fase 14)
12. Hyperparameter Tuning & Voting Ensemble Optimization (Fase 15)
13. Evaluasi Independen pada Data Uji (Fase 15)
14. Model Selection & Saving Model Produksi (Fase 16)
15. Konsolidasi Master Dataset Final (Fase 18)
16. Export Laporan Analitik Eksekutif & KPI (Fase 19)
"""

import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def run_full_pipeline(threshold_hours=4.0, full_tuning=True):
    start_total = time.time()

    print("\n" + "=" * 75)
    print("      MEMULAI OTOMASI PIPELINE LENGKAP PROYEK NLP ZAHIR (FASE 1 - 20)")
    print("=" * 75 + "\n")

    steps = [
        ("Fase 1 & 2: WhatsApp Parsing & Media Mapping", "src.parser"),
        ("Fase 4    : Role Identification (ADMIN / CLIENT / SYSTEM)", "src.roles"),
        ("Fase 5    : Unit Percakapan (Threshold Jeda 4 Jam)", "src.conversation"),
        ("Fase 6    : Analisis Respons Klien (RESPONS / TIDAK_RESPONS)", "src.client_response"),
        ("Fase 7    : Analisis Penanganan Remote & Kredensial", "src.remote"),
        ("Fase 9    : Sub-Conversation Splitting & Data Labeling", "src.category_labeling"),
        ("Fase 10   : Text Preprocessing & Document Aggregation", "src.preprocessing"),
        ("Fase 11   : Cascaded Normalization (indo-normalizer + Zahir)", "src.normalization"),
        ("Fase 12   : Feature Extraction TF-IDF (Unigram & Bigram)", "src.features"),
        ("Fase 13   : Stratified Train-Test Split (80% / 20%)", "src.split"),
        ("Fase 14   : Training Model Classification (7 Algoritma)", "src.train"),
    ]

    if full_tuning:
        steps.append(("Fase 15.1 : Hyperparameter Tuning & Voting Ensemble", "src.tuning"))

    steps.extend([
        ("Fase 15.2 : Evaluasi Model pada Data Uji Independen", "src.evaluation"),
        ("Fase 16   : Model Selection & Saving Production Model", "src.selection"),
        ("Fase 18   : Konsolidasi Master Dataset Final", "src.consolidation"),
        ("Fase 19   : Export Laporan Analitik Eksekutif & KPI", "src.export"),
    ])

    total_steps = len(steps)

    for idx, (desc, module_name) in enumerate(steps, 1):
        step_start = time.time()
        print(f"\n[{idx}/{total_steps}] MENJALANKAN: {desc}...")
        print("-" * 75)

        mod = __import__(module_name, fromlist=["run"])
        if module_name == "src.conversation":
            mod.run(threshold_hours=threshold_hours)
        else:
            mod.run()

        step_elapsed = time.time() - step_start
        print(f"-> Selesai dalam {step_elapsed:.2f} detik.")

    total_elapsed = time.time() - start_total
    print("\n" + "=" * 75)
    print("      SELURUH PIPELINE OTOMASI NLP ZAHIR SELESAI DENGAN SUKSES!")
    print(f"      Total Waktu Eksekusi: {total_elapsed:.2f} detik")
    print("=" * 75)
    print("\nFile Hasil Akhir Siap Pakai:")
    print("  1. Master Dataset Final    : data/output/master_conversations_final.csv")
    print("  2. Ringkasan Eksekutif KPI : data/output/executive_summary.csv")
    print("  3. Rekap Kategori Kendala  : data/output/category_breakdown_report.csv")
    print("  4. Laporan Naratif Proyek  : data/output/final_project_report.txt")
    print("  5. Model AI Produksi Utama : models/best_model.pkl\n")

def run(arg=None):
    threshold = 4.0
    full_tuning = True

    if arg:
        try:
            threshold = float(arg)
        except ValueError:
            pass

    run_full_pipeline(threshold_hours=threshold, full_tuning=full_tuning)

if __name__ == "__main__":
    run()