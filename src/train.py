"""
train.py - Training Model Machine Learning (Fase 14) - Expanded Suite (7 Algoritma)

Membaca train_test_data.npz (data latih 80%),
melatih 7 algoritma klasifikasi teks Machine Learning:
1. Logistic Regression (Multinomial) + class_weight='balanced'
2. Linear Support Vector Machine (LinearSVC) + class_weight='balanced'
3. SGDClassifier (Hinge / Linear SVM via SGD) + class_weight='balanced'
4. Complement Naive Bayes (ComplementNB) - Khusus Imbalanced Text
5. Multinomial Naive Bayes (MultinomialNB)
6. Random Forest Classifier + class_weight='balanced'
7. Gradient Boosting Classifier
Melakukan 5-Fold Stratified Cross Validation untuk validasi kestabilan,
dan menyimpan seluruh model terlatih ke folder models/.
"""

import csv
import pickle
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
INPUT_SPLIT_FILE = PROCESSED_DIR / "train_test_data.npz"
RESULTS_CSV_FILE = MODELS_DIR / "training_results.csv"

def load_split_data(filepath):
    data = np.load(filepath, allow_pickle=True)
    X_train = csr_matrix(
        (data["X_train_data"], data["X_train_indices"], data["X_train_indptr"]),
        shape=tuple(data["X_train_shape"])
    )
    X_test = csr_matrix(
        (data["X_test_data"], data["X_test_indices"], data["X_test_indptr"]),
        shape=tuple(data["X_test_shape"])
    )
    y_train = data["y_train"]
    y_test = data["y_test"]
    sub_ids_train = data["sub_ids_train"]
    sub_ids_test = data["sub_ids_test"]
    feature_names = data["feature_names"]

    return X_train, X_test, y_train, y_test, sub_ids_train, sub_ids_test, feature_names

def train_and_cross_validate(X_train, y_train):
    models = {
        "LogisticRegression": LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=42
        ),
        "LinearSVC": LinearSVC(
            C=1.0,
            class_weight="balanced",
            random_state=42,
            max_iter=2000
        ),
        "SGDClassifier": SGDClassifier(
            loss="modified_huber",
            class_weight="balanced",
            max_iter=2000,
            random_state=42
        ),
        "ComplementNB": ComplementNB(
            alpha=0.5
        ),
        "MultinomialNB": MultinomialNB(
            alpha=0.5
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=100,
            class_weight="balanced",
            random_state=42
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=80,
            learning_rate=0.1,
            max_depth=3,
            random_state=42
        ),
    }

    results = {}
    trained_models = {}

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for name, clf in models.items():
        # 5-Fold Cross Validation F1-Weighted & Accuracy
        cv_acc_scores = cross_val_score(clf, X_train, y_train, cv=cv, scoring="accuracy")
        cv_f1_scores = cross_val_score(clf, X_train, y_train, cv=cv, scoring="f1_weighted")

        # Fit model pada seluruh data latih (135 sampel)
        clf.fit(X_train, y_train)
        train_acc = clf.score(X_train, y_train)

        results[name] = {
            "cv_accuracy_mean": cv_acc_scores.mean(),
            "cv_accuracy_std": cv_acc_scores.std(),
            "cv_f1_mean": cv_f1_scores.mean(),
            "cv_f1_std": cv_f1_scores.std(),
            "train_accuracy": train_acc,
        }
        trained_models[name] = clf

    return trained_models, results

def save_models_and_results(trained_models, results):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Simpan setiap model terlatih
    for name, clf in trained_models.items():
        model_filename = MODELS_DIR / f"model_{name.lower()}.pkl"
        with open(model_filename, "wb") as f:
            pickle.dump(clf, f)

    # 2. Simpan perbandingan performa ke CSV
    with open(RESULTS_CSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "model_name",
            "cv_accuracy_mean",
            "cv_accuracy_std",
            "cv_f1_weighted_mean",
            "cv_f1_weighted_std",
            "train_accuracy"
        ])
        for name, m in results.items():
            writer.writerow([
                name,
                f"{m['cv_accuracy_mean']:.4f}",
                f"{m['cv_accuracy_std']:.4f}",
                f"{m['cv_f1_mean']:.4f}",
                f"{m['cv_f1_std']:.4f}",
                f"{m['train_accuracy']:.4f}",
            ])

def validate(results, trained_models):
    print("\n=== VALIDASI FASE 14 (TRAINING MODEL & CROSS-VALIDATION - 7 ALGORITMA) ===")
    print("Perbandingan Hasil 5-Fold Stratified Cross-Validation pada Data Latih:")
    print("-" * 75)
    print(f"{'Algoritma':<20} | {'CV Accuracy':<16} | {'CV F1-Weighted':<16} | {'Train Acc':<10}")
    print("-" * 75)

    sorted_results = sorted(results.items(), key=lambda x: x[1]["cv_f1_mean"], reverse=True)
    for name, r in sorted_results:
        acc_str = f"{r['cv_accuracy_mean']*100:.1f}% ± {r['cv_accuracy_std']*100:.1f}%"
        f1_str = f"{r['cv_f1_mean']*100:.1f}% ± {r['cv_f1_std']*100:.1f}%"
        train_str = f"{r['train_accuracy']*100:.1f}%"
        print(f"{name:<20} | {acc_str:<16} | {f1_str:<16} | {train_str:<10}")
    print("-" * 75)

    best_model_name = sorted_results[0][0]
    print(f"\nModel Terbaik Berdasarkan Cross-Validation: {best_model_name} (F1: {sorted_results[0][1]['cv_f1_mean']*100:.1f}%)")
    print(f"Seluruh 7 model telah disimpan ke direktori: {MODELS_DIR}\n")

def run():
    if not INPUT_SPLIT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_SPLIT_FILE}")
        print("Jalankan fase 13 terlebih dahulu: python main.py split")
        return

    print("=" * 60)
    print("  FASE 14 — TRAINING MODEL CLASSIFICATION (7 ALGORITMA)")
    print(f"  Input Data : {INPUT_SPLIT_FILE}")
    print(f"  Simpan di  : {MODELS_DIR}")
    print("=" * 60)

    X_train, X_test, y_train, y_test, ids_train, ids_test, feature_names = load_split_data(INPUT_SPLIT_FILE)
    print(f"\nMemuat {X_train.shape[0]} data latih ({X_train.shape[1]} fitur)")

    trained_models, results = train_and_cross_validate(X_train, y_train)
    save_models_and_results(trained_models, results)

    validate(results, trained_models)

    print("=" * 60)
    print("  FASE 14 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()