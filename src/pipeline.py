"""
pipeline.py - Full Automation Pipeline (Fase 20)

Mengotomatisasi seluruh alur kerja proyek NLP Zahir secara sekuensial end-to-end.
Dapat dipanggil dari CLI maupun sebagai Python function (process_conversations).
"""

import time
from pathlib import Path

from src.parser import parse_whatsapp_chats
from src.roles import identify_roles
from src.conversation import group_conversations
from src.client_response import analyze_client_responses
from src.remote import classify_remote
from src.category_labeling import label_sub_conversations
from src.preprocessing import preprocess_text_data
from src.normalization import normalize_text_data
from src.features import run as run_features
from src.split import run as run_split
from src.train import run as run_train
from src.tuning import run as run_tuning
from src.evaluation import run as run_evaluation
from src.selection import run as run_selection
from src.consolidation import consolidate_master_data
from src.export import export_all_reports

BASE_DIR = Path(__file__).resolve().parent.parent

def process_conversations(raw_dir=None, media_dir=None, threshold_hours=4.0, full_tuning=True):
    """API Function Python utama untuk memproses percakapan WhatsApp dari data mentah hingga laporan akhir."""
    return run_full_pipeline(raw_dir=raw_dir, media_dir=media_dir, threshold_hours=threshold_hours, full_tuning=full_tuning)

def run_full_pipeline(raw_dir=None, media_dir=None, threshold_hours=4.0, full_tuning=True):
    start_total = time.time()

    print("\n" + "=" * 75)
    print("      MEMULAI OTOMASI PIPELINE LENGKAP PROYEK NLP ZAHIR (FASE 1 - 20)")
    print("=" * 75 + "\n")

    parse_kwargs = {}
    if raw_dir:
        parse_kwargs["raw_dir"] = raw_dir
    if media_dir:
        parse_kwargs["media_dir"] = media_dir

    steps = [
        ("Fase 1 & 2: WhatsApp Parsing & Media Mapping", lambda: parse_whatsapp_chats(**parse_kwargs)),
        ("Fase 4    : Role Identification (ADMIN / CLIENT / SYSTEM)", lambda: identify_roles()),
        ("Fase 5    : Unit Percakapan (Threshold Jeda 4 Jam)", lambda: group_conversations(threshold_hours=threshold_hours)),
        ("Fase 6    : Analisis Respons Klien (RESPONS / TIDAK_RESPONS)", lambda: analyze_client_responses()),
        ("Fase 7    : Analisis Penanganan Remote & Kredensial", lambda: classify_remote()),
        ("Fase 9    : Sub-Conversation Splitting & Data Labeling", lambda: label_sub_conversations()),
        ("Fase 10   : Text Preprocessing & Document Aggregation", lambda: preprocess_text_data()),
        ("Fase 11   : Cascaded Normalization (indo-normalizer + Zahir)", lambda: normalize_text_data()),
        ("Fase 12   : Feature Extraction TF-IDF (Unigram & Bigram)", lambda: run_features()),
        ("Fase 13   : Stratified Train-Test Split (80% / 20%)", lambda: run_split()),
        ("Fase 14   : Training Model Classification (7 Algoritma)", lambda: run_train()),
    ]

    if full_tuning:
        steps.append(("Fase 15.1 : Hyperparameter Tuning & Voting Ensemble", lambda: run_tuning()))

    steps.extend([
        ("Fase 15.2 : Evaluasi Model pada Data Uji Independen", lambda: run_evaluation()),
        ("Fase 16   : Model Selection & Saving Production Model", lambda: run_selection()),
        ("Fase 18   : Konsolidasi Master Dataset Final", lambda: consolidate_master_data()),
        ("Fase 19   : Export Laporan Analitik Eksekutif & KPI", lambda: export_all_reports()),
    ])

    total_steps = len(steps)

    for idx, (desc, func) in enumerate(steps, 1):
        step_start = time.time()
        print(f"\n[{idx}/{total_steps}] MENJALANKAN: {desc}...")
        print("-" * 75)

        func()

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
