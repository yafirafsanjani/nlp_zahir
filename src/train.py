"""
train.py - Model Training & 5-Fold Cross-Validation (Fase 14)

Melatih 7 model klasifikasi teks berbasis Sklearn Pipeline (TF-IDF + Classifier):
- LogisticRegression
- LinearSVC
- ComplementNB
- MultinomialNB
- SGDClassifier
- RandomForest
- GradientBoosting

Menggunakan 5-Fold Stratified Cross-Validation HANYA PADA DATA LATIH (X_train)
untuk mengukur stabilitas dan performa validasi tanpa menyentuh data uji (X_test).
"""

import csv
import pickle
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import ComplementNB, MultinomialNB
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
INPUT_SPLIT_FILE = PROCESSED_DIR / "train_test_data.npz"
TRAINING_RESULTS_FILE = MODELS_DIR / "training_results.csv"

CUSTOM_STOPWORDS = [
    "yang", "di", "ke", "dari", "ini", "itu", "dan", "atau", "untuk", "dengan", "pada", "adalah", "ada",
    "pak", "bu", "kak", "ibu", "bapak", "mas", "mbak", "saya", "kami", "kita", "anda",
    "selamat", "pagi", "siang", "sore", "malam", "halo", "hallo", "haloo", "hi", "hey",
    "terima", "kasih", "terimakasih", "makasih", "siap", "baik", "oke", "ok", "iya", "ya",
    "mohon", "tolong", "bantu", "dibantu", "sama", "aja", "saja", "lagi", "pun", "deh",
    "sih", "nih", "tuh", "dong", "kan", "lah", "kok", "oh", "nah", "wah", "yuk",
    "apa", "kenapa", "bagaimana", "dimana", "kapan", "siapa", "mengapa", "seperti"
]

def load_train_data(filepath):
    data = np.load(filepath, allow_pickle=True)
    return data["X_train"], data["y_train"]

def get_baseline_pipelines():
    return {
        "LogisticRegression": Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=400, stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42))
        ]),
        "LinearSVC": Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=400, stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
            ("clf", LinearSVC(class_weight="balanced", max_iter=2000, random_state=42))
        ]),
        "ComplementNB": Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=400, stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
            ("clf", ComplementNB())
        ]),
        "MultinomialNB": Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=400, stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
            ("clf", MultinomialNB())
        ]),
        "SGDClassifier": Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=400, stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
            ("clf", SGDClassifier(class_weight="balanced", random_state=42))
        ]),
        "RandomForest": Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=400, stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
            ("clf", RandomForestClassifier(class_weight="balanced", random_state=42))
        ]),
        "GradientBoosting": Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=400, stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
            ("clf", GradientBoostingClassifier(random_state=42))
        ]),
    }

def train_and_cross_validate(X_train, y_train, n_splits=5):
    pipelines = get_baseline_pipelines()
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    results = {}

    for name, pipe in pipelines.items():
        cv_accs, cv_f1_macs, cv_f1_wtds = [], [], []

        for train_idx, val_idx in skf.split(X_train, y_train):
            X_tr, y_tr = X_train[train_idx], y_train[train_idx]
            X_val, y_val = X_train[val_idx], y_train[val_idx]

            pipe.fit(X_tr, y_tr)
            val_pred = pipe.predict(X_val)

            cv_accs.append(accuracy_score(y_val, val_pred))
            _, _, f1_m, _ = precision_recall_fscore_support(y_val, val_pred, average="macro", zero_division=0)
            _, _, f1_w, _ = precision_recall_fscore_support(y_val, val_pred, average="weighted", zero_division=0)
            cv_f1_macs.append(f1_m)
            cv_f1_wtds.append(f1_w)

        pipe.fit(X_train, y_train)
        tr_pred = pipe.predict(X_train)
        train_acc = accuracy_score(y_train, tr_pred)

        results[name] = {
            "pipeline": pipe,
            "train_accuracy": train_acc,
            "cv_acc_mean": np.mean(cv_accs),
            "cv_acc_std": np.std(cv_accs),
            "cv_f1_macro_mean": np.mean(cv_f1_macs),
            "cv_f1_macro_std": np.std(cv_f1_macs),
            "cv_f1_weighted_mean": np.mean(cv_f1_wtds),
            "cv_f1_weighted_std": np.std(cv_f1_wtds),
        }

    return results

def save_trained_models(results):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for name, data in results.items():
        model_file = MODELS_DIR / f"model_{name.lower()}.pkl"
        with open(model_file, "wb") as f:
            pickle.dump(data["pipeline"], f)

    with open(TRAINING_RESULTS_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "model_name",
            "train_accuracy",
            "cv_acc_mean",
            "cv_acc_std",
            "cv_f1_macro_mean",
            "cv_f1_macro_std",
            "cv_f1_weighted_mean",
            "cv_f1_weighted_std"
        ])
        for name, data in results.items():
            writer.writerow([
                name,
                f"{data['train_accuracy']*100:.2f}%",
                f"{data['cv_acc_mean']*100:.2f}%",
                f"{data['cv_acc_std']*100:.2f}%",
                f"{data['cv_f1_macro_mean']*100:.2f}%",
                f"{data['cv_f1_macro_std']*100:.2f}%",
                f"{data['cv_f1_weighted_mean']*100:.2f}%",
                f"{data['cv_f1_weighted_std']*100:.2f}%"
            ])

def validate_training(results):
    print("\n=== VALIDASI FASE 14 (MODEL TRAINING & 5-FOLD CROSS-VALIDATION) ===")
    print("Performa 7 Model Baseline pada Data Latih (X_train):")
    print("-" * 95)
    print(f"{'Model':<20} | {'Train Acc':<10} | {'CV Acc (mean ? std)':<22} | {'CV F1 Weighted':<18} | {'CV F1 Macro':<15}")
    print("-" * 95)

    for name, data in results.items():
        tr_acc = f"{data['train_accuracy']*100:.1f}%"
        cv_acc = f"{data['cv_acc_mean']*100:.1f}% ? {data['cv_acc_std']*100:.1f}%"
        cv_f1w = f"{data['cv_f1_weighted_mean']*100:.1f}% ? {data['cv_f1_weighted_std']*100:.1f}%"
        cv_f1m = f"{data['cv_f1_macro_mean']*100:.1f}% ? {data['cv_f1_macro_std']*100:.1f}%"
        print(f"{name:<20} | {tr_acc:<10} | {cv_acc:<22} | {cv_f1w:<18} | {cv_f1m:<15}")
    print("-" * 95)
    print()

def run():
    if not INPUT_SPLIT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_SPLIT_FILE}")
        return

    print("=" * 60)
    print("  FASE 14 ? MODEL TRAINING & 5-FOLD CV (LEAK-FREE PIPELINES)")
    print("=" * 60)

    X_train, y_train = load_train_data(INPUT_SPLIT_FILE)
    print(f"\nMemuat {len(X_train)} dokumen data latih.")

    results = train_and_cross_validate(X_train, y_train, n_splits=5)
    save_trained_models(results)
    validate_training(results)

    print("=" * 60)
    print("  FASE 14 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()
