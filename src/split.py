"""
split.py - Train-Test Split (Fase 13)

Membaca tfidf_features.npz, membagi dataset menjadi Data Latih (Train 80%)
dan Data Uji (Test 20%) menggunakan Stratified Splitting (stratify=y)
untuk menjaga proporsi tiap kategori kendala secara proporsional.
Menyimpan hasil ke data/processed/train_test_data.npz & train_test_summary.csv.
"""

import csv
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_NPZ_FILE = PROCESSED_DIR / "tfidf_features.npz"
OUTPUT_SPLIT_FILE = PROCESSED_DIR / "train_test_data.npz"
SUMMARY_CSV_FILE = PROCESSED_DIR / "train_test_summary.csv"

def load_tfidf_data(filepath):
    data = np.load(filepath, allow_pickle=True)
    shape = tuple(data["shape"])
    matrix = csr_matrix((data["data"], data["indices"], data["indptr"]), shape=shape)
    labels = data["labels"]
    sub_ids = data["sub_ids"]
    feature_names = data["feature_names"]
    return matrix, labels, sub_ids, feature_names

def perform_stratified_split(X, y, sub_ids, test_size=0.20, random_state=42):
    # Stratified Split menjaga distribusi kelas minoritas & mayoritas seimbang
    X_train, X_test, y_train, y_test, ids_train, ids_test = train_test_split(
        X,
        y,
        sub_ids,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )
    return X_train, X_test, y_train, y_test, ids_train, ids_test

def save_split_data(X_train, X_test, y_train, y_test, ids_train, ids_test, feature_names):
    # Simpan sparse matrix dan metadata train-test
    np.savez_compressed(
        OUTPUT_SPLIT_FILE,
        X_train_data=X_train.data,
        X_train_indices=X_train.indices,
        X_train_indptr=X_train.indptr,
        X_train_shape=X_train.shape,
        X_test_data=X_test.data,
        X_test_indices=X_test.indices,
        X_test_indptr=X_test.indptr,
        X_test_shape=X_test.shape,
        y_train=np.array(y_train),
        y_test=np.array(y_test),
        sub_ids_train=np.array(ids_train),
        sub_ids_test=np.array(ids_test),
        feature_names=np.array(feature_names),
    )

    # Simpan ringkasan perbandingan kelas ke CSV
    train_counts = Counter(y_train)
    test_counts = Counter(y_test)
    all_classes = sorted(list(set(y_train) | set(y_test)))

    with open(SUMMARY_CSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["kategori_kendala", "total_data", "train_count", "train_pct", "test_count", "test_pct"])
        for cat in all_classes:
            tr = train_counts.get(cat, 0)
            te = test_counts.get(cat, 0)
            tot = tr + te
            tr_pct = f"{tr/tot*100:.1f}%" if tot > 0 else "0%"
            te_pct = f"{te/tot*100:.1f}%" if tot > 0 else "0%"
            writer.writerow([cat, tot, tr, tr_pct, te, te_pct])

def validate(y_train, y_test, ids_train, ids_test):
    print("\n=== VALIDASI FASE 13 (STRATIFIED TRAIN-TEST SPLIT) ===")
    n_train = len(y_train)
    n_test = len(y_test)
    total = n_train + n_test

    print(f"Total Sampel Dataset : {total} Dokumen Sub-Percakapan")
    print(f"Data Latih (Train)   : {n_train} sampel ({n_train/total*100:.1f}%)")
    print(f"Data Uji (Test)      : {n_test} sampel ({n_test/total*100:.1f}%)\n")

    train_counts = Counter(y_train)
    test_counts = Counter(y_test)
    all_classes = sorted(list(set(y_train) | set(y_test)))

    print("DISTRIBUSI KELAS PADA DATA LATIH & DATA UJI (PROPORSI SEIMBANG):")
    print(f"{'Kategori Kendala':<28} | {'Total':<5} | {'Train (80%)':<12} | {'Test (20%)':<10}")
    print("-" * 65)
    for cat in all_classes:
        tr = train_counts.get(cat, 0)
        te = test_counts.get(cat, 0)
        tot = tr + te
        print(f"{cat:<28} | {tot:>5} | {tr:>5} ({tr/tot*100:>4.1f}%) | {te:>4} ({te/tot*100:>4.1f}%)")
    print("-" * 65)
    print()

def run():
    if not INPUT_NPZ_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_NPZ_FILE}")
        print("Jalankan fase 12 terlebih dahulu: python main.py features")
        return

    print("=" * 60)
    print("  FASE 13 — STRATIFIED TRAIN-TEST SPLIT (80% / 20%)")
    print(f"  Input : {INPUT_NPZ_FILE}")
    print(f"  Output: {OUTPUT_SPLIT_FILE}")
    print("=" * 60)

    X, y, sub_ids, feature_names = load_tfidf_data(INPUT_NPZ_FILE)
    print(f"\nMemuat {X.shape[0]} baris vektor dari {INPUT_NPZ_FILE.name}")

    X_train, X_test, y_train, y_test, ids_train, ids_test = perform_stratified_split(X, y, sub_ids, test_size=0.20, random_state=42)
    save_split_data(X_train, X_test, y_train, y_test, ids_train, ids_test, feature_names)

    validate(y_train, y_test, ids_train, ids_test)

    print("=" * 60)
    print("  FASE 13 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()