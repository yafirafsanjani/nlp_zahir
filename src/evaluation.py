"""
evaluation.py - Evaluasi Model Machine Learning pada Data Uji (Fase 15)

Membaca train_test_data.npz (data uji 34 sampel / 20%),
memuat seluruh model baseline dan model hasil hyperparameter tuning / ensemble,
mengevaluasi performa model menggunakan metrik:
- Test Accuracy
- F1-Score (Weighted & Macro)
- Precision & Recall
- Classification Report per kategori kendala
- Confusion Matrix
Menyimpan hasil ke data/processed/evaluation_summary.csv & laporan teks detail.
"""

import csv
import pickle
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
INPUT_SPLIT_FILE = PROCESSED_DIR / "train_test_data.npz"
SUMMARY_CSV_FILE = PROCESSED_DIR / "evaluation_summary.csv"
REPORT_TXT_FILE = PROCESSED_DIR / "evaluation_classification_reports.txt"

def get_available_models():
    models_dict = {}
    for p in MODELS_DIR.glob("model_*.pkl"):
        clean_name = p.stem.replace("model_", "")
        models_dict[clean_name] = p
    return models_dict

def load_test_data(filepath):
    data = np.load(filepath, allow_pickle=True)
    X_test = csr_matrix(
        (data["X_test_data"], data["X_test_indices"], data["X_test_indptr"]),
        shape=tuple(data["X_test_shape"])
    )
    y_test = data["y_test"]
    sub_ids_test = data["sub_ids_test"]
    return X_test, y_test, sub_ids_test

def evaluate_all_models(X_test, y_test):
    results = {}
    classes = sorted(list(set(y_test)))
    model_files = get_available_models()

    for name, path in model_files.items():
        try:
            with open(path, "rb") as f:
                clf = pickle.load(f)

            y_pred = clf.predict(X_test)

            acc = accuracy_score(y_test, y_pred)
            p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(
                y_test, y_pred, average="weighted", zero_division=0
            )
            p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
                y_test, y_pred, average="macro", zero_division=0
            )

            clf_rep = classification_report(y_test, y_pred, zero_division=0)
            cm = confusion_matrix(y_test, y_pred, labels=classes)

            results[name] = {
                "accuracy": acc,
                "f1_weighted": f1_weighted,
                "precision_weighted": p_weighted,
                "recall_weighted": r_weighted,
                "f1_macro": f1_macro,
                "precision_macro": p_macro,
                "recall_macro": r_macro,
                "classification_report": clf_rep,
                "confusion_matrix": cm,
                "classes": classes,
            }
        except Exception as e:
            print(f"[WARN] Gagal mengevaluasi {name}: {e}")

    return results

def save_evaluation_results(results):
    sorted_models = sorted(results.items(), key=lambda x: x[1]["accuracy"], reverse=True)
    with open(SUMMARY_CSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "model_name",
            "test_accuracy",
            "f1_weighted",
            "precision_weighted",
            "recall_weighted",
            "f1_macro",
            "precision_macro",
            "recall_macro"
        ])
        for name, m in sorted_models:
            writer.writerow([
                name,
                f"{m['accuracy']*100:.2f}%",
                f"{m['f1_weighted']*100:.2f}%",
                f"{m['precision_weighted']*100:.2f}%",
                f"{m['recall_weighted']*100:.2f}%",
                f"{m['f1_macro']*100:.2f}%",
                f"{m['precision_macro']*100:.2f}%",
                f"{m['recall_macro']*100:.2f}%",
            ])

    with open(REPORT_TXT_FILE, "w", encoding="utf-8") as f:
        f.write("======================================================================\n")
        f.write("  LAPORAN EVALUASI DETAIL SELURUH MODEL PADA DATA UJI (34 SAMPEL)\n")
        f.write("======================================================================\n\n")

        for name, m in sorted_models:
            f.write(f"\n{'='*70}\n")
            f.write(f"MODEL: {name}\n")
            f.write(f"Test Accuracy: {m['accuracy']*100:.2f}% | F1-Weighted: {m['f1_weighted']*100:.2f}% | F1-Macro: {m['f1_macro']*100:.2f}%\n")
            f.write(f"{'-'*70}\n")
            f.write("CLASSIFICATION REPORT PER KATEGORI KENDALA:\n")
            f.write(m["classification_report"])
            f.write("\nCONFUSION MATRIX:\n")
            f.write(f"Label Urutan: {', '.join(m['classes'])}\n")
            f.write(str(m["confusion_matrix"]))
            f.write("\n\n")

def print_evaluation_table(results):
    print("\n=== VALIDASI FASE 15 (EVALUASI LENGKAP BASELINE & TUNED MODEL) ===")
    print("Performa Model pada 34 Sampel Data Uji (Test Set 20%):")
    print("-" * 75)
    print(f"{'Algoritma':<28} | {'Test Accuracy':<14} | {'F1-Weighted':<14} | {'F1-Macro':<10}")
    print("-" * 75)

    sorted_models = sorted(results.items(), key=lambda x: x[1]["accuracy"], reverse=True)
    for name, m in sorted_models:
        acc_str = f"{m['accuracy']*100:.1f}%"
        f1_w_str = f"{m['f1_weighted']*100:.1f}%"
        f1_m_str = f"{m['f1_macro']*100:.1f}%"
        print(f"{name:<28} | {acc_str:<14} | {f1_w_str:<14} | {f1_m_str:<10}")
    print("-" * 75)

    best_name, best_m = sorted_models[0]
    print(f"\nModel Terbaik pada Data Uji: {best_name}")
    print(f"Akurasi: {best_m['accuracy']*100:.1f}% | F1-Weighted: {best_m['f1_weighted']*100:.1f}%\n")

    print(f"--- DETAIL CLASSIFICATION REPORT MODEL TERBAIK ({best_name}) ---")
    print(best_m["classification_report"])

def run():
    if not INPUT_SPLIT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_SPLIT_FILE}")
        print("Jalankan fase 13 terlebih dahulu: python main.py split")
        return

    print("=" * 60)
    print("  FASE 15 — EVALUASI MODEL MACHINE LEARNING (LENGKAP)")
    print(f"  Input Data : {INPUT_SPLIT_FILE}")
    print(f"  Output CSV : {SUMMARY_CSV_FILE}")
    print(f"  Laporan    : {REPORT_TXT_FILE}")
    print("=" * 60)

    X_test, y_test, sub_ids_test = load_test_data(INPUT_SPLIT_FILE)
    print(f"\nMemuat {X_test.shape[0]} data uji independen.")

    results = evaluate_all_models(X_test, y_test)
    save_evaluation_results(results)
    print_evaluation_table(results)

    print("=" * 60)
    print("  FASE 15 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()