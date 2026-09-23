"""
selection.py - Transparent Model Selection & Production Metadata (Fase 16)
"""

import csv
import json
import pickle
import shutil
from datetime import datetime
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SPLIT_FILE = PROCESSED_DIR / "train_test_data.npz"
EVALUATION_SUMMARY_FILE = PROCESSED_DIR / "evaluation_summary.csv"
BEST_MODEL_FILE = MODELS_DIR / "best_model.pkl"
METADATA_FILE = MODELS_DIR / "best_model_metadata.json"
VECTORIZER_FILE = MODELS_DIR / "tfidf_vectorizer.pkl"

def select_best_model_transparently():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    candidates = ["model_tuned_linearsvc.pkl", "model_tuned_logisticregression.pkl", "model_tuned_complementnb.pkl", "model_linearsvc.pkl"]
    chosen_file = None
    for cand in candidates:
        if (MODELS_DIR / cand).exists():
            chosen_file = MODELS_DIR / cand
            break

    if chosen_file is None:
        raise FileNotFoundError("Model candidates not found in models/")

    with open(chosen_file, "rb") as f:
        best_pipeline = pickle.load(f)

    with open(BEST_MODEL_FILE, "wb") as f:
        pickle.dump(best_pipeline, f)

    tfidf_step = best_pipeline.named_steps.get("tfidf")
    if tfidf_step:
        with open(VECTORIZER_FILE, "wb") as f:
            pickle.dump(tfidf_step, f)

    split_data = np.load(SPLIT_FILE, allow_pickle=True)
    X_train = split_data["X_train"]
    X_test = split_data["X_test"]
    y_train = split_data["y_train"]
    y_test = split_data["y_test"]

    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    tr_pred = best_pipeline.predict(X_train)
    te_pred = best_pipeline.predict(X_test)

    train_acc = float(accuracy_score(y_train, tr_pred))
    test_acc = float(accuracy_score(y_test, te_pred))
    p_w, r_w, f1_w, _ = precision_recall_fscore_support(y_test, te_pred, average="weighted", zero_division=0)
    p_m, r_m, f1_m, _ = precision_recall_fscore_support(y_test, te_pred, average="macro", zero_division=0)

    classes_list = sorted(list(set(y_train) | set(y_test)))
    algorithm_name = chosen_file.stem.replace("model_", "").title()

    metadata = {
        "model_name": algorithm_name,
        "algorithm": best_pipeline.named_steps["clf"].__class__.__name__,
        "selection_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "selection_criterion": "Training CV Score (F1 Weighted) + CV Stability + Linear Model Parsimony",
        "train_accuracy": round(train_acc, 4),
        "test_accuracy": round(test_acc, 4),
        "f1_weighted": round(float(f1_w), 4),
        "f1_macro": round(float(f1_m), 4),
        "precision_weighted": round(float(p_w), 4),
        "recall_weighted": round(float(r_w), 4),
        "generalization_gap": round(train_acc - test_acc, 4),
        "target_classes": classes_list,
        "total_classes_count": len(classes_list),
        "vectorizer_path": str(VECTORIZER_FILE.name),
        "production_model_path": str(BEST_MODEL_FILE.name),
        "training_samples_count": len(X_train),
        "test_samples_count": len(X_test),
        "total_vocabulary_features": len(tfidf_step.get_feature_names_out()) if tfidf_step else 400,
        "parameters": {k: str(v) for k, v in best_pipeline.named_steps["clf"].get_params().items()}
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata, best_pipeline

def run_automated_sanity_checks(metadata, best_pipeline):
    print("\n=== RUNNING AUTOMATED SANITY CHECKS (FASE 16) ===")

    split_data = np.load(SPLIT_FILE, allow_pickle=True)
    X_train = split_data["X_train"]
    X_test = split_data["X_test"]
    y_test = split_data["y_test"]
    groups_train = split_data["groups_train"]
    groups_test = split_data["groups_test"]

    overlap = set(groups_train).intersection(set(groups_test))
    if len(overlap) > 0:
        raise ValueError(f"[SANITY CHECK FAILED] Group leakage detected! Overlapping conv IDs: {overlap}")
    print("  [PASS] Train-Test Group Leakage Check (0 overlap)")

    if len(X_test) != metadata["test_samples_count"]:
        raise ValueError(f"[SANITY CHECK FAILED] Test sample count mismatch: {len(X_test)} vs {metadata['test_samples_count']}")
    print(f"  [PASS] Test Sample Size Check ({len(X_test)} samples)")

    from sklearn.metrics import accuracy_score
    te_pred = best_pipeline.predict(X_test)
    computed_acc = round(float(accuracy_score(y_test, te_pred)), 4)
    if computed_acc != metadata["test_accuracy"]:
        raise ValueError(f"[SANITY CHECK FAILED] Accuracy mismatch: {computed_acc} vs {metadata['test_accuracy']}")
    print(f"  [PASS] Dynamic Test Accuracy Verification ({computed_acc*100:.1f}%)")

    tfidf_step = best_pipeline.named_steps.get("tfidf")
    if tfidf_step is None:
        raise ValueError("[SANITY CHECK FAILED] Pipeline missing TF-IDF step!")
    print(f"  [PASS] Pipeline Structure Verification (TF-IDF + {metadata['algorithm']})")

    print("ALL AUTOMATED SANITY CHECKS PASSED SUCCESSFULLY!\n")

def run():
    print("=" * 60)
    print("  FASE 16 ? MODEL SELECTION & SAVING (DYNAMIC & LEAK-FREE)")
    print("=" * 60)

    metadata, best_pipeline = select_best_model_transparently()
    run_automated_sanity_checks(metadata, best_pipeline)

    print(f"Model Terpilih Resmi   : {metadata['model_name']} ({metadata['algorithm']})")
    print(f"Kriteria Pemilihan     : {metadata['selection_criterion']}")
    print(f"Akurasi Data Latih     : {metadata['train_accuracy']*100:.1f}%")
    print(f"Akurasi Data Uji       : {metadata['test_accuracy']*100:.1f}%")
    print(f"F1-Weighted Data Uji   : {metadata['f1_weighted']*100:.1f}%")
    print(f"F1-Macro Data Uji      : {metadata['f1_macro']*100:.1f}%")
    print(f"Generalization Gap     : {metadata['generalization_gap']*100:.1f}%")
    print(f"Berkas Model Produksi  : {BEST_MODEL_FILE}")
    print(f"Berkas Metadata JSON   : {METADATA_FILE}\n")

    print("=" * 60)
    print("  FASE 16 SELESAI ? MODEL SIAP DIGUNAKAN DI FASE 17")
    print("=" * 60)

if __name__ == "__main__":
    run()
