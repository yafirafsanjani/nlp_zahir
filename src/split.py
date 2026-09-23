"""
split.py - Group-Stratified Train-Test Split (Fase 13)

Membaca data/processed/chat_normalized.csv, membagi dataset menjadi Data Latih (Train 80%)
dan Data Uji (Test 20%) menggunakan StratifiedGroupKFold (berdasarkan conversation_id)
untuk menjamin TIDAK ADA GROUP LEAKAGE antara percakapan induk di data latih dan data uji.
"""

import csv
from pathlib import Path
from collections import Counter
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_CSV_FILE = PROCESSED_DIR / "chat_normalized.csv"
OUTPUT_SPLIT_FILE = PROCESSED_DIR / "train_test_data.npz"
SUMMARY_CSV_FILE = PROCESSED_DIR / "train_test_summary.csv"

def load_normalized_data(filepath):
    with open(filepath, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    
    texts = np.array([
        r.get("normalized_text", r.get("clean_text", "")).strip() 
        if r.get("normalized_text", r.get("clean_text", "")).strip() else "kosong" 
        for r in rows
    ])
    labels = np.array([r["kategori_kendala"] for r in rows])
    sub_ids = np.array([r.get("sub_conversation_id", f"sub_{i}") for i, r in enumerate(rows)])
    conv_ids = np.array([r.get("conversation_id", s.rsplit("_", 1)[0] if "_" in s else s) for s, r in zip(sub_ids, rows)])
    
    return texts, labels, sub_ids, conv_ids

def perform_group_stratified_split(texts, labels, sub_ids, conv_ids, n_splits=5):
    sgkf = StratifiedGroupKFold(n_splits=n_splits)
    train_idx, test_idx = next(sgkf.split(texts, labels, conv_ids))
    
    X_train, X_test = texts[train_idx], texts[test_idx]
    y_train, y_test = labels[train_idx], labels[test_idx]
    ids_train, ids_test = sub_ids[train_idx], sub_ids[test_idx]
    groups_train, groups_test = conv_ids[train_idx], conv_ids[test_idx]
    
    overlap = set(groups_train).intersection(set(groups_test))
    if len(overlap) > 0:
        raise ValueError(f"[LEAKAGE DETECTED] Parent conversation leakage detected: {overlap}")
        
    return X_train, X_test, y_train, y_test, ids_train, ids_test, groups_train, groups_test

def save_split_data(X_train, X_test, y_train, y_test, ids_train, ids_test, groups_train, groups_test):
    np.savez_compressed(
        OUTPUT_SPLIT_FILE,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        sub_ids_train=ids_train,
        sub_ids_test=ids_test,
        groups_train=groups_train,
        groups_test=groups_test,
    )

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

def validate(y_train, y_test, groups_train, groups_test):
    print("\n=== VALIDASI FASE 13 (GROUP-STRATIFIED TRAIN-TEST SPLIT) ===")
    n_train = len(y_train)
    n_test = len(y_test)
    total = n_train + n_test
    overlap = set(groups_train).intersection(set(groups_test))

    print(f"Total Sampel Dataset       : {total} Dokumen Sub-Percakapan")
    print(f"Data Latih (Train)         : {n_train} sampel ({n_train/total*100:.1f}%)")
    print(f"Data Uji (Test)            : {n_test} sampel ({n_test/total*100:.1f}%)")
    print(f"Parent Conversation Overlap: {len(overlap)} (LEAKAGE CHECK: PASSED)\n")

    train_counts = Counter(y_train)
    test_counts = Counter(y_test)
    all_classes = sorted(list(set(y_train) | set(y_test)))

    print("DISTRIBUSI KELAS PADA DATA LATIH & DATA UJI:")
    print("-" * 65)
    for cat in all_classes:
        tr = train_counts.get(cat, 0)
        te = test_counts.get(cat, 0)
        tot = tr + te
        print(f"{cat:<28} | {tot:>5} | {tr:>5} ({tr/tot*100:>4.1f}%) | {te:>4} ({te/tot*100:>4.1f}%)")
    print("-" * 65)
    print()

def run():
    if not INPUT_CSV_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_CSV_FILE}")
        return

    print("=" * 60)
    print("  FASE 13 ? GROUP-STRATIFIED TRAIN-TEST SPLIT (80% / 20%)")
    print(f"  Input : {INPUT_CSV_FILE}")
    print(f"  Output: {OUTPUT_SPLIT_FILE}")
    print("=" * 60)

    texts, labels, sub_ids, conv_ids = load_normalized_data(INPUT_CSV_FILE)
    print(f"\nMemuat {len(texts)} baris dokumen dari {INPUT_CSV_FILE.name}")

    X_train, X_test, y_train, y_test, ids_train, ids_test, groups_train, groups_test = perform_group_stratified_split(
        texts, labels, sub_ids, conv_ids
    )
    save_split_data(X_train, X_test, y_train, y_test, ids_train, ids_test, groups_train, groups_test)
    validate(y_train, y_test, groups_train, groups_test)

    print("=" * 60)
    print("  FASE 13 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    run()
