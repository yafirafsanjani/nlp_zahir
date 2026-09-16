"""
features.py - Feature Extraction TF-IDF (Fase 12)

Membaca chat_normalized.csv, melakukan pembobotan kata menggunakan TF-IDF
dengan konfigurasi Unigram & Bigram (1, 2) serta filtering stopwords percakapan umum.
Menyimpan model vectorizer ke models/tfidf_vectorizer.pkl dan
matriks fitur ke data/processed/tfidf_features.npz & tfidf_summary.csv.
"""

import csv
import pickle
from pathlib import Path
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
INPUT_FILE = PROCESSED_DIR / "chat_normalized.csv"
VECTORIZER_FILE = MODELS_DIR / "tfidf_vectorizer.pkl"
FEATURES_NPZ_FILE = PROCESSED_DIR / "tfidf_features.npz"
SUMMARY_CSV_FILE = PROCESSED_DIR / "tfidf_features_summary.csv"

# Stopwords umum percakapan & salam (agar bobot fokus pada istilah masalah teknis)
CUSTOM_STOPWORDS = [
    "yang", "di", "ke", "dari", "ini", "itu", "dan", "atau", "untuk", "dengan", "pada", "adalah", "ada",
    "pak", "bu", "kak", "ibu", "bapak", "mas", "mbak", "saya", "kami", "kita", "anda",
    "selamat", "pagi", "siang", "sore", "malam", "halo", "hallo", "haloo", "hi", "hey",
    "terima", "kasih", "terimakasih", "makasih", "siap", "baik", "oke", "ok", "iya", "ya",
    "mohon", "tolong", "bantu", "dibantu", "sama", "aja", "saja", "lagi", "pun", "deh",
    "sih", "nih", "tuh", "dong", "kan", "lah", "kok", "oh", "nah", "wah", "yuk",
    "apa", "kenapa", "bagaimana", "dimana", "kapan", "siapa", "mengapa", "seperti"
]

def load_data(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    return reader

def extract_tfidf_features(data):
    texts = [row["normalized_text"] if row["normalized_text"].strip() else "kosong" for row in data]
    labels = [row["kategori_kendala"] for row in data]
    sub_ids = [row["sub_conversation_id"] for row in data]

    # Inisialisasi TfidfVectorizer dengan Unigram + Bigram
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        max_features=400,
        stop_words=CUSTOM_STOPWORDS,
        sublinear_tf=True
    )

    tfidf_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()

    return vectorizer, tfidf_matrix, feature_names, texts, labels, sub_ids

def save_artifacts(vectorizer, tfidf_matrix, labels, sub_ids, feature_names):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Simpan model vectorizer
    with open(VECTORIZER_FILE, "wb") as f:
        pickle.dump(vectorizer, f)

    # 2. Simpan sparse matrix & metadata numpy
    np.savez_compressed(
        FEATURES_NPZ_FILE,
        data=tfidf_matrix.data,
        indices=tfidf_matrix.indices,
        indptr=tfidf_matrix.indptr,
        shape=tfidf_matrix.shape,
        labels=np.array(labels),
        sub_ids=np.array(sub_ids),
        feature_names=np.array(feature_names),
    )

    # 3. Simpan ringkasan fitur kata teratas ke CSV untuk transparansi
    dense_matrix = tfidf_matrix.toarray()
    mean_scores = dense_matrix.mean(axis=0)
    sorted_indices = np.argsort(mean_scores)[::-1]

    with open(SUMMARY_CSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["feature_name", "mean_tfidf_score", "document_frequency"])
        for idx in sorted_indices:
            feat = feature_names[idx]
            score = mean_scores[idx]
            doc_freq = np.count_nonzero(dense_matrix[:, idx])
            writer.writerow([feat, f"{score:.5f}", doc_freq])

def validate(vectorizer, tfidf_matrix, feature_names, labels, sub_ids):
    print("\n=== VALIDASI FASE 12 (FEATURE EXTRACTION TF-IDF) ===")
    n_docs, n_features = tfidf_matrix.shape
    print(f"Dimensi Matriks TF-IDF : {n_docs} Dokumen x {n_features} Fitur Kata/Frase")
    print(f"Rentang N-gram         : Unigram (1) & Bigram (2)")
    print(f"Model Disimpan ke      : {VECTORIZER_FILE.name}")
    print(f"Matriks Disimpan ke    : {FEATURES_NPZ_FILE.name}\n")

    dense_matrix = tfidf_matrix.toarray()
    mean_scores = dense_matrix.mean(axis=0)

    print("TOP 15 FITUR KATA/FRASE DENGAN BOBOT TF-IDF TERTINGGI (GLOBAL):")
    top_indices = np.argsort(mean_scores)[::-1][:15]
    for rank, idx in enumerate(top_indices, 1):
        feat = feature_names[idx]
        score = mean_scores[idx]
        df_count = np.count_nonzero(dense_matrix[:, idx])
        print(f"  {rank:>2}. {feat:<22} (Bobot Rata-rata: {score:.4f} | Muncul di {df_count} dokumen)")

    print("\nKATA KUNCI DOMINAN PER KATEGORI KENDALA (TOP 3 PER KELAS):")
    unique_labels = sorted(list(set(labels)))
    labels_array = np.array(labels)

    for cat in unique_labels:
        cat_indices = np.where(labels_array == cat)[0]
        if len(cat_indices) > 0:
            cat_mean = dense_matrix[cat_indices].mean(axis=0)
            cat_top_idx = np.argsort(cat_mean)[::-1][:3]
            top_words = [f"{feature_names[i]} ({cat_mean[i]:.3f})" for i in cat_top_idx if cat_mean[i] > 0]
            top_str = ", ".join(top_words) if top_words else "Tidak ada fitur dominan"
            print(f"  - [{cat:<28}] ({len(cat_indices):>2} dok): {top_str}")
    print()

def run():
    if not INPUT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_FILE}")
        print("Jalankan fase 11 terlebih dahulu: python main.py normalize")
        return

    print("=" * 60)
    print("  FASE 12 — FEATURE EXTRACTION (TF-IDF UNIGRAM & BIGRAM)")
    print(f"  Input : {INPUT_FILE}")
    print(f"  Output: {FEATURES_NPZ_FILE}")
    print(f"  Model : {VECTORIZER_FILE}")
    print("=" * 60)

    data = load_data(INPUT_FILE)
    print(f"\nMemuat {len(data)} baris dokumen dari {INPUT_FILE.name}")

    vectorizer, tfidf_matrix, feature_names, texts, labels, sub_ids = extract_tfidf_features(data)
    save_artifacts(vectorizer, tfidf_matrix, labels, sub_ids, feature_names)

    validate(vectorizer, tfidf_matrix, feature_names, labels, sub_ids)

    print("=" * 60)
    print("  FASE 12 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()