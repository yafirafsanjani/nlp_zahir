"""
tuning.py - Hyperparameter Tuning & Pipeline Optimization (Fase 15.1)
"""

import csv
import pickle
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedKFold, GridSearchCV
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
TUNING_RESULTS_FILE = PROCESSED_DIR / "tuning_results_summary.csv"

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

def tune_models(X_train, y_train, n_splits=5):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    grids = {
        "Tuned_LogisticRegression": (
            Pipeline([
                ("tfidf", TfidfVectorizer(stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
                ("clf", LogisticRegression(random_state=42, max_iter=1000))
            ]),
            {
                "tfidf__ngram_range": [(1, 1), (1, 2)],
                "tfidf__min_df": [1, 2],
                "tfidf__max_features": [300, 400, 500],
                "clf__C": [0.1, 0.5, 1.0, 2.0],
                "clf__class_weight": ["balanced", None],
                "clf__solver": ["lbfgs"]
            }
        ),
        "Tuned_LinearSVC": (
            Pipeline([
                ("tfidf", TfidfVectorizer(stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
                ("clf", LinearSVC(random_state=42, max_iter=2000))
            ]),
            {
                "tfidf__ngram_range": [(1, 1), (1, 2)],
                "tfidf__min_df": [1, 2],
                "tfidf__max_features": [300, 400, 500],
                "clf__C": [0.05, 0.1, 0.3, 0.5, 1.0],
                "clf__class_weight": ["balanced", None]
            }
        ),
        "Tuned_ComplementNB": (
            Pipeline([
                ("tfidf", TfidfVectorizer(stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
                ("clf", ComplementNB())
            ]),
            {
                "tfidf__ngram_range": [(1, 1), (1, 2)],
                "tfidf__min_df": [1, 2],
                "tfidf__max_features": [300, 400, 500],
                "clf__alpha": [0.1, 0.5, 1.0, 2.0],
                "clf__norm": [True, False]
            }
        ),
        "Tuned_RandomForest": (
            Pipeline([
                ("tfidf", TfidfVectorizer(stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
                ("clf", RandomForestClassifier(random_state=42))
            ]),
            {
                "tfidf__ngram_range": [(1, 1), (1, 2)],
                "tfidf__max_features": [400],
                "clf__n_estimators": [50, 100],
                "clf__max_depth": [5, 10, None],
                "clf__class_weight": ["balanced", None]
            }
        ),
        "Tuned_GradientBoosting": (
            Pipeline([
                ("tfidf", TfidfVectorizer(stop_words=CUSTOM_STOPWORDS, sublinear_tf=True)),
                ("clf", GradientBoostingClassifier(random_state=42))
            ]),
            {
                "tfidf__ngram_range": [(1, 1), (1, 2)],
                "tfidf__max_features": [400],
                "clf__n_estimators": [50, 100],
                "clf__max_depth": [3, 5],
                "clf__learning_rate": [0.05, 0.1]
            }
        )
    }

    results = {}
    for name, (pipe, param_grid) in grids.items():
        grid = GridSearchCV(pipe, param_grid, cv=skf, scoring="f1_weighted", n_jobs=-1)
        grid.fit(X_train, y_train)

        best_pipe = grid.best_estimator_
        cv_f1_weighted = grid.best_score_

        cv_accs, cv_f1_macs = [], []
        for train_idx, val_idx in skf.split(X_train, y_train):
            X_tr, y_tr = X_train[train_idx], y_train[train_idx]
            X_val, y_val = X_train[val_idx], y_train[val_idx]
            best_pipe.fit(X_tr, y_tr)
            val_pred = best_pipe.predict(X_val)
            cv_accs.append(accuracy_score(y_val, val_pred))
            _, _, f1_m, _ = precision_recall_fscore_support(y_val, val_pred, average="macro", zero_division=0)
            cv_f1_macs.append(f1_m)

        best_pipe.fit(X_train, y_train)
        tr_pred = best_pipe.predict(X_train)
        train_acc = accuracy_score(y_train, tr_pred)

        results[name] = {
            "pipeline": best_pipe,
            "best_params": grid.best_params_,
            "train_accuracy": train_acc,
            "cv_f1_weighted_mean": cv_f1_weighted,
            "cv_acc_mean": np.mean(cv_accs),
            "cv_acc_std": np.std(cv_accs),
            "cv_f1_macro_mean": np.mean(cv_f1_macs),
            "cv_f1_macro_std": np.std(cv_f1_macs),
        }

    return results

def save_tuned_models(results):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for name, data in results.items():
        model_file = MODELS_DIR / f"model_{name.lower()}.pkl"
        with open(model_file, "wb") as f:
            pickle.dump(data["pipeline"], f)

    with open(TUNING_RESULTS_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["model_name", "train_accuracy", "cv_acc_mean", "cv_f1_weighted_mean", "cv_f1_macro_mean", "best_params"])
        for name, data in results.items():
            writer.writerow([
                name,
                f"{data['train_accuracy']*100:.2f}%",
                f"{data['cv_acc_mean']*100:.2f}%",
                f"{data['cv_f1_weighted_mean']*100:.2f}%",
                f"{data['cv_f1_macro_mean']*100:.2f}%",
                str(data["best_params"])
            ])

def run():
    if not INPUT_SPLIT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_SPLIT_FILE}")
        return

    print("=" * 60)
    print("  FASE 15.1 ? HYPERPARAMETER TUNING (TRAINING CV ONLY)")
    print("=" * 60)

    X_train, y_train = load_train_data(INPUT_SPLIT_FILE)
    results = tune_models(X_train, y_train, n_splits=5)
    save_tuned_models(results)

    print("\nHASIL HYPERPARAMETER TUNING PADA DATA LATIH:")
    for name, data in results.items():
        print(f"[{name}] Train Acc: {data['train_accuracy']*100:.1f}% | CV F1 Wtd: {data['cv_f1_weighted_mean']*100:.1f}% | CV Acc: {data['cv_acc_mean']*100:.1f}% ? {data['cv_acc_std']*100:.1f}%")
        print(f"  Best Params: {data['best_params']}\n")

    print("=" * 60)
    print("  FASE 15.1 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()
