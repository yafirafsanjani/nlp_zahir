"""
evaluation.py - Independent Test Set Evaluation (Fase 15.2)
"""

import csv
import pickle
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
INPUT_SPLIT_FILE = PROCESSED_DIR / "train_test_data.npz"
SUMMARY_CSV_FILE = PROCESSED_DIR / "evaluation_summary.csv"
REPORT_TXT_FILE = PROCESSED_DIR / "evaluation_classification_reports.txt"

def load_test_data(filepath):
    data = np.load(filepath, allow_pickle=True)
    return data["X_train"], data["y_train"], data["X_test"], data["y_test"], data["sub_ids_test"]

def evaluate_all_models(X_train, y_train, X_test, y_test):
    classes = sorted(list(set(y_train) | set(y_test)))
    results = {}

    model_files = list(MODELS_DIR.glob("model_*.pkl"))
    for file_path in model_files:
        name = file_path.stem.replace("model_", "")
        if name in ("best_model", "ensemble_votingclassifier"):
            continue

        try:
            with open(file_path, "rb") as f:
                pipe = pickle.load(f)

            tr_pred = pipe.predict(X_train)
            train_acc = accuracy_score(y_train, tr_pred)

            y_pred = pipe.predict(X_test)
            acc = accuracy_score(y_test, y_pred)

            p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(
                y_test, y_pred, average="weighted", zero_division=0
            )
            p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
                y_test, y_pred, average="macro", zero_division=0
            )

            clf_rep = classification_report(y_test, y_pred, zero_division=0)
            cm = confusion_matrix(y_test, y_pred, labels=classes)
            gap = train_acc - acc

            results[name] = {
                "train_accuracy": train_acc,
                "accuracy": acc,
                "f1_weighted": f1_weighted,
                "precision_weighted": p_weighted,
                "recall_weighted": r_weighted,
                "f1_macro": f1_macro,
                "precision_macro": p_macro,
                "recall_macro": r_macro,
                "generalization_gap": gap,
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
            "train_accuracy",
            "test_accuracy",
            "f1_weighted",
            "precision_weighted",
            "recall_weighted",
            "f1_macro",
            "precision_macro",
            "recall_macro",
            "generalization_gap"
        ])
        for name, m in sorted_models:
            writer.writerow([
                name,
                f"{m['train_accuracy']*100:.2f}%",
                f"{m['accuracy']*100:.2f}%",
                f"{m['f1_weighted']*100:.2f}%",
                f"{m['precision_weighted']*100:.2f}%",
                f"{m['recall_weighted']*100:.2f}%",
                f"{m['f1_macro']*100:.2f}%",
                f"{m['precision_macro']*100:.2f}%",
                f"{m['recall_macro']*100:.2f}%",
                f"{m['generalization_gap']*100:.2f}%"
            ])

    with open(REPORT_TXT_FILE, "w", encoding="utf-8") as f:
        f.write("======================================================================\n")
        f.write("  LAPORAN EVALUASI DETAIL SELURUH MODEL PADA DATA UJI INDEPENDEN\n")
        f.write("======================================================================\n\n")

        for name, m in sorted_models:
            f.write(f"\n{'='*70}\n")
            f.write(f"MODEL: {name}\n")
            f.write(f"Train Acc: {m['train_accuracy']*100:.2f}% | Test Acc: {m['accuracy']*100:.2f}% | F1-Weighted: {m['f1_weighted']*100:.2f}% | F1-Macro: {m['f1_macro']*100:.2f}% | Gap: {m['generalization_gap']*100:.2f}%\n")
            f.write(f"{'-'*70}\n")
            f.write("CLASSIFICATION REPORT PER KATEGORI KENDALA:\n")
            f.write(m["classification_report"])
            f.write("\nCONFUSION MATRIX:\n")
            f.write(f"Label Urutan: {', '.join(m['classes'])}\n")
            f.write(str(m["confusion_matrix"]))
            f.write("\n\n")

def print_evaluation_table(results):
    print("\n=== VALIDASI FASE 15 (EVALUASI INDEPENDEN TEST SET) ===")
    print("-" * 95)
    print(f"{'Algoritma':<28} | {'Train Acc':<10} | {'Test Accuracy':<14} | {'F1-Weighted':<14} | {'F1-Macro':<10} | {'Gap':<6}")
    print("-" * 95)

    sorted_models = sorted(results.items(), key=lambda x: x[1]["accuracy"], reverse=True)
    for name, m in sorted_models:
        tr_acc_str = f"{m['train_accuracy']*100:.1f}%"
        acc_str = f"{m['accuracy']*100:.1f}%"
        f1_w_str = f"{m['f1_weighted']*100:.1f}%"
        f1_m_str = f"{m['f1_macro']*100:.1f}%"
        gap_str = f"{m['generalization_gap']*100:.1f}%"
        print(f"{name:<28} | {tr_acc_str:<10} | {acc_str:<14} | {f1_w_str:<14} | {f1_m_str:<10} | {gap_str:<6}")
    print("-" * 95)

def run():
    if not INPUT_SPLIT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_SPLIT_FILE}")
        return

    print("=" * 60)
    print("  FASE 15.2 ? EVALUASI MODEL INDEPENDEN DATA UJI")
    print("=" * 60)

    X_train, y_train, X_test, y_test, sub_ids_test = load_test_data(INPUT_SPLIT_FILE)
    print(f"\nMemuat {len(X_test)} data uji independen.")

    results = evaluate_all_models(X_train, y_train, X_test, y_test)
    save_evaluation_results(results)
    print_evaluation_table(results)

    print("=" * 60)
    print("  FASE 15.2 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()
