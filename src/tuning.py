"""
tuning.py - Hyperparameter Tuning & Ensemble Optimization (Fase 15.5)

Melakukan optimasi sistematis (GridSearchCV dengan Stratified K-Fold CV)
pada 3 algoritma kandidat juara:
1. LogisticRegression (Tuning C, solver, penalty)
2. LinearSVC (Tuning C, loss, penalty)
3. GradientBoosting (Tuning learning_rate, n_estimators, max_depth)
Serta membangun Voting Classifier (Ensemble) yang menggabungkan model-model terbaik.
Menyimpan model-model hasil tuning ke folder models/ dan melaporkan peningkatan akurasi.
"""

import csv
import pickle
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import GradientBoostingClassifier, VotingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
INPUT_SPLIT_FILE = PROCESSED_DIR / "train_test_data.npz"
TUNING_SUMMARY_FILE = PROCESSED_DIR / "tuning_results_summary.csv"

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
    return X_train, X_test, y_train, y_test

def tune_models(X_train, y_train):
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # 1. Grid Search Logistic Regression
    param_grid_lr = {
        "C": [0.3, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0],
        "solver": ["lbfgs", "saga"],
        "class_weight": ["balanced"],
        "max_iter": [1500],
        "random_state": [42]
    }
    grid_lr = GridSearchCV(
        LogisticRegression(),
        param_grid_lr,
        cv=cv,
        scoring="f1_weighted",
        n_jobs=-1
    )
    grid_lr.fit(X_train, y_train)

    # 2. Grid Search LinearSVC
    param_grid_svc = {
        "C": [0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0],
        "loss": ["squared_hinge"],
        "class_weight": ["balanced"],
        "max_iter": [2500],
        "random_state": [42]
    }
    grid_svc = GridSearchCV(
        LinearSVC(),
        param_grid_svc,
        cv=cv,
        scoring="f1_weighted",
        n_jobs=-1
    )
    grid_svc.fit(X_train, y_train)

    # 3. Grid Search Gradient Boosting
    param_grid_gb = {
        "n_estimators": [50, 75, 100, 120],
        "learning_rate": [0.03, 0.05, 0.08, 0.1],
        "max_depth": [2, 3],
        "random_state": [42]
    }
    grid_gb = GridSearchCV(
        GradientBoostingClassifier(),
        param_grid_gb,
        cv=cv,
        scoring="f1_weighted",
        n_jobs=-1
    )
    grid_gb.fit(X_train, y_train)

    best_lr = grid_lr.best_estimator_
    best_svc = grid_svc.best_estimator_
    best_gb = grid_gb.best_estimator_

    # 4. Membangun Voting Ensemble dari 3 model terbaik hasil tuning
    # Hard voting karena LinearSVC tidak menghasilkan probabilitas secara native
    ensemble_voting = VotingClassifier(
        estimators=[
            ("tuned_lr", best_lr),
            ("tuned_svc", best_svc),
            ("tuned_gb", best_gb),
        ],
        voting="hard"
    )
    ensemble_voting.fit(X_train, y_train)

    tuned_models = {
        "Tuned_LogisticRegression": (best_lr, grid_lr.best_params_, grid_lr.best_score_),
        "Tuned_LinearSVC": (best_svc, grid_svc.best_params_, grid_svc.best_score_),
        "Tuned_GradientBoosting": (best_gb, grid_gb.best_params_, grid_gb.best_score_),
        "Ensemble_VotingClassifier": (ensemble_voting, "Voting(Tuned_LR + Tuned_SVC + Tuned_GB)", None),
    }

    return tuned_models

def evaluate_on_test(tuned_models, X_test, y_test):
    results = {}
    for name, (clf, params, cv_score) in tuned_models.items():
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        p_w, r_w, f1_w, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted", zero_division=0)
        p_m, r_m, f1_m, _ = precision_recall_fscore_support(y_test, y_pred, average="macro", zero_division=0)
        clf_report = classification_report(y_test, y_pred, zero_division=0)

        results[name] = {
            "model": clf,
            "params": params,
            "cv_f1_score": cv_score,
            "test_accuracy": acc,
            "f1_weighted": f1_w,
            "f1_macro": f1_m,
            "classification_report": clf_report,
        }
    return results

def save_tuned_artifacts(results):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Simpan model-model hasil tuning
    for name, data in results.items():
        filename = MODELS_DIR / f"model_{name.lower()}.pkl"
        with open(filename, "wb") as f:
            pickle.dump(data["model"], f)

    # Simpan laporan ringkasan tuning ke CSV
    with open(TUNING_SUMMARY_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["model_name", "test_accuracy", "f1_weighted", "f1_macro", "best_parameters"])
        for name, data in results.items():
            writer.writerow([
                name,
                f"{data['test_accuracy']*100:.2f}%",
                f"{data['f1_weighted']*100:.2f}%",
                f"{data['f1_macro']*100:.2f}%",
                str(data["params"]),
            ])

def print_results(results):
    print("\n" + "=" * 75)
    print("  HASIL HYPERPARAMETER TUNING & ENSEMBLE PADA DATA UJI (34 SAMPEL)")
    print("=" * 75)
    print(f"{'Model Optimization':<30} | {'Test Acc':<10} | {'F1-Weighted':<12} | {'F1-Macro':<10}")
    print("-" * 75)

    sorted_res = sorted(results.items(), key=lambda x: x[1]["test_accuracy"], reverse=True)
    for name, d in sorted_res:
        acc_s = f"{d['test_accuracy']*100:.1f}%"
        f1_w_s = f"{d['f1_weighted']*100:.1f}%"
        f1_m_s = f"{d['f1_macro']*100:.1f}%"
        print(f"{name:<30} | {acc_s:<10} | {f1_w_s:<12} | {f1_m_s:<10}")
    print("-" * 75)

    best_name, best_d = sorted_res[0]
    print(f"\nModel Terbaik Setelah Tuning: {best_name}")
    print(f"Test Accuracy Baru : {best_d['test_accuracy']*100:.1f}%")
    print(f"F1-Weighted Baru   : {best_d['f1_weighted']*100:.1f}%")
    print(f"Hyperparameters    : {best_d['params']}\n")

    print(f"--- DETAIL CLASSIFICATION REPORT ({best_name}) ---")
    print(best_d["classification_report"])

def run():
    print("=" * 60)
    print("  FASE 15.5 — HYPERPARAMETER TUNING & ENSEMBLE OPTIMIZATION")
    print(f"  Input : {INPUT_SPLIT_FILE}")
    print(f"  Tujuan: Menemukan parameter terbaik & menaikkan akurasi")
    print("=" * 60)

    X_train, X_test, y_train, y_test = load_split_data(INPUT_SPLIT_FILE)
    print(f"\nMemulai GridSearchCV pada data latih (135 sampel)...")

    tuned_models = tune_models(X_train, y_train)
    results = evaluate_on_test(tuned_models, X_test, y_test)
    save_tuned_artifacts(results)
    print_results(results)

    print("=" * 60)
    print("  TUNING & ENSEMBLE SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()