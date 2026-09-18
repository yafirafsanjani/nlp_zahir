"""
active_learning.py - Modul Active Learning Loop (Fase Ekspansi LLM 4/5)

Memakai model produksi (best_model.pkl) untuk menebak seluruh data training,
memilih dokumen yang paling "ragu" (margin probabilitas terkecil), lalu
mengirimnya ulang ke LLM untuk relabel. Hasil relabel yang konsisten antar
sinyal (label lama, label LLM Fase 2, label LLM baru) menjadi ground truth final,
sedangkan konflik ditandai REVIEW untuk cek manusia.

Keluaran:
  - data/processed/active_learning_results.csv  (detail tiap dokumen yang di-relabel)
  - data/processed/ground_truth_final.csv       (dataset penuh + label final utk retrain)

Cara pakai:
    python src/active_learning.py --dry-run
    python src/active_learning.py --provider gemini --top-n 30
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from collections import Counter

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.taxonomy import load_taxonomy, get_fallback_category
from src.llm_labeling import (
    build_labeling_prompt,
    extract_json,
    normalize_label_response,
    make_provider as make_labeling_provider,
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
DATA_FILE = PROCESSED_DIR / "chat_normalized.csv"
LLM_LABELS_FILE = PROCESSED_DIR / "llm_labels.csv"
MODEL_FILE = MODELS_DIR / "best_model.pkl"
VECTORIZER_FILE = MODELS_DIR / "tfidf_vectorizer.pkl"
RESULTS_FILE = PROCESSED_DIR / "active_learning_results.csv"
FINAL_GROUND_TRUTH_FILE = PROCESSED_DIR / "ground_truth_final.csv"

TOP_N_DEFAULT = 30            # jumlah dokumen paling ragu yang dikirim ulang ke LLM


def load_csv(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_pickle(filepath):
    import pickle
    with open(filepath, "rb") as f:
        return pickle.load(f)


def compute_scores(model, X):
    """Menghitung top-1 kelas, probabilitas, dan margin untuk tiap dokumen."""
    proba = model.predict_proba(X)
    classes = list(model.classes_)
    scores = []
    for i in range(proba.shape[0]):
        p = proba[i]
        order = np.argsort(p)[::-1]
        top1_idx, top2_idx = order[0], order[1]
        scores.append(
            {
                "top1_class": classes[top1_idx],
                "top1_prob": float(p[top1_idx]),
                "top2_class": classes[top2_idx],
                "top2_prob": float(p[top2_idx]),
                "margin": float(p[top1_idx] - p[top2_idx]),
            }
        )
    return scores


def select_uncertain(scores, docs, top_n):
    """
    Memilih dokumen paling ragu (margin terkecil). Dokumen tanpa teks (raw_text
    kosong) tidak bisa di-relabel LLM, jadi dikecualikan dari pool.
    """
    pool = [i for i, d in enumerate(docs) if d["raw_text"].strip()]
    ranked = sorted(pool, key=lambda i: scores[i]["margin"])
    return ranked[: min(top_n, len(ranked))]


def decide_status(old_label, llm_new, llm_prev):
    """Keputusan label final: KEEP / UPDATE / REVIEW."""
    if llm_new == old_label:
        return "KEEP", old_label
    if llm_prev and llm_new == llm_prev:
        return "UPDATE", llm_new
    return "REVIEW", old_label


def run(dry_run=False, provider=None, top_n=TOP_N_DEFAULT):
    missing = [p for p in (DATA_FILE, MODEL_FILE, VECTORIZER_FILE) if not p.exists()]
    if missing:
        print("[ERROR] File berikut tidak ditemukan:")
        for p in missing:
            print(f"        - {p}")
        print("Jalankan pipeline inti dulu (run-all), lalu fase 2 (llm_labeling).")
        return

    taxonomy = load_taxonomy()
    allowed = set(c["name"] for c in taxonomy.get("categories", []))
    allowed.add(taxonomy.get("fallback_category", get_fallback_category()))

    print("=" * 60)
    print("  FASE EKSPANSI LLM 4/5 — ACTIVE LEARNING LOOP")
    mode = "DRY-RUN (relabel simulasi regex, tanpa API)" if dry_run else "REAL"
    print(f"  Mode    : {mode}")
    print(f"  Top-N   : {top_n} dokumen paling ragu")
    print(f"  Model   : {MODEL_FILE.name}")
    print(f"  Input   : {DATA_FILE.name}")
    print("=" * 60)

    docs = load_csv(DATA_FILE)
    print(f"\nMemuat {len(docs)} dokumen dari {DATA_FILE.name}")

    vectorizer = load_pickle(VECTORIZER_FILE)
    model = load_pickle(MODEL_FILE)

    texts = [r["normalized_text"].strip() if r["normalized_text"].strip() else "kosong"
             for r in docs]
    X = vectorizer.transform(texts)
    scores = compute_scores(model, X)

    selected_idx = select_uncertain(scores, docs, top_n)
    print(f"Model siap. Dokumen paling ragu yang dipilih: {len(selected_idx)}")

    # label LLM Fase 2 (bila ada) utk sinyal konsistensi kedua
    llm_prev_map = {}
    if LLM_LABELS_FILE.exists():
        for r in load_csv(LLM_LABELS_FILE):
            llm_prev_map[r["sub_conversation_id"]] = r["kategori_llm"]
        print(f"Sinyal LLM Fase 2 (llm_labels.csv) tersedia utk {len(llm_prev_map)} dokumen")
    else:
        print("Sinyal LLM Fase 2 tidak ditemukan -> hanya 2 sinyal (label lama + LLM baru)")

    llm = make_labeling_provider(provider, dry_run)

    results = []
    relabeled = 0
    for pos, i in enumerate(selected_idx, 1):
        doc = docs[i]
        sid = doc["sub_conversation_id"]
        old_label = doc["kategori_kendala"]
        prompt = build_labeling_prompt(taxonomy, doc["raw_text"])
        try:
            raw = llm.complete(prompt)
            label = normalize_label_response(extract_json(raw), allowed)
        except Exception as exc:
            label = {
                "kategori": old_label, "confidence": 0.0, "evidence": None,
                "perlu_kategori_baru": False, "usulan_kategori": None,
            }
            print(f"  [WARN] {sid} gagal: {exc}")
        llm_new = label["kategori"]
        llm_prev = llm_prev_map.get(sid)
        status, final_label = decide_status(old_label, llm_new, llm_prev)
        if status != "KEEP":
            relabeled += 1

        results.append(
            {
                "sub_conversation_id": sid,
                "kategori_kendala": old_label,
                "kategori_kendala_final": final_label,
                "status": status,
                "top1_class": scores[i]["top1_class"],
                "top1_prob": f"{scores[i]['top1_prob']:.3f}",
                "top2_class": scores[i]["top2_class"],
                "top2_prob": f"{scores[i]['top2_prob']:.3f}",
                "margin": f"{scores[i]['margin']:.3f}",
                "label_llm_baru": llm_new,
                "label_llm_sebelum": llm_prev or "",
                "confidence_llm": f"{label['confidence']:.2f}",
                "evidence": label.get("evidence") or "",
                "raw_text": doc["raw_text"],
            }
        )
        if pos % 10 == 0 or pos == len(selected_idx):
            print(f"  ... {pos}/{len(selected_idx)} dokumen direlabel")

    # gabungkan seluruh dokumen ke ground truth final (dokumen tidak dipilih: KEEP)
    final_rows = []
    llm_new_by_sid = {r["sub_conversation_id"]: r["label_llm_baru"] for r in results}
    for i, doc in enumerate(docs):
        sid = doc["sub_conversation_id"]
        if sid in llm_new_by_sid:
            r = next(x for x in results if x["sub_conversation_id"] == sid)
            final_rows.append(
                {
                    "sub_conversation_id": sid,
                    "kategori_kendala": doc["kategori_kendala"],
                    "kategori_kendala_final": r["kategori_kendala_final"],
                    "status": r["status"],
                }
            )
        else:
            final_rows.append(
                {
                    "sub_conversation_id": sid,
                    "kategori_kendala": doc["kategori_kendala"],
                    "kategori_kendala_final": doc["kategori_kendala"],
                    "status": "KEEP",
                }
            )

    # ---- simpan
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sub_conversation_id", "kategori_kendala", "kategori_kendala_final", "status",
        "top1_class", "top1_prob", "top2_class", "top2_prob", "margin",
        "label_llm_baru", "label_llm_sebelum", "confidence_llm", "evidence", "raw_text",
    ]
    with open(RESULTS_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    with open(FINAL_GROUND_TRUTH_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["sub_conversation_id", "kategori_kendala",
                           "kategori_kendala_final", "status"]
        )
        writer.writeheader()
        writer.writerows(final_rows)

    # ---- ringkasan
    print(f"\n=== RINGKASAN ACTIVE LEARNING ===")
    print(f"Dokumen direlabel : {len(results)} ({top_n} target)")
    print(f"Label berubah     : {relabeled} (KEEP = tidak berubah)")

    st_counter = Counter(r["status"] for r in results)
    print("\nSTATUS PER DOKUMEN YANG DIRELABLE:")
    for st in ("KEEP", "UPDATE", "REVIEW"):
        print(f"  - {st:<8}: {st_counter.get(st, 0)}")

    k = sum(1 for r in results if r["status"] == "UPDATE")
    rv = sum(1 for r in results if r["status"] == "REVIEW")
    print(f"\n-> {k} label diperbarui (LLM konsisten), {rv} perlu cek manual (REVIEW).")

    upd = [r for r in final_rows if r["status"] == "UPDATE"]
    if upd:
        print("\nCONTOH PERUBAHAN LABEL (UPDATE):")
        for r in upd[:5]:
            print(f"  - {r['sub_conversation_id']}: "
                  f"{r['kategori_kendala']} -> {r['kategori_kendala_final']}")

    cold = sum(1 for r in final_rows if r["status"] == "REVIEW")
    print(f"\nGround truth final: {FINAL_GROUND_TRUTH_FILE}")
    print(f"  - total dokumen: {len(final_rows)}, UPDATE: {k}, REVIEW-PENDING: {cold}")
    print("=" * 60)
    print("  FASE ACTIVE SELESAI")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Active learning loop relabel")
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER", "openai"),
                        help="openai | gemini (atau via env LLM_PROVIDER)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulasi tanpa API (relabel pakai deteksi regex)")
    parser.add_argument("--top-n", type=int, default=TOP_N_DEFAULT,
                        help="Jumlah dokumen paling ragu yang dikirim ke LLM")
    args = parser.parse_args()
    run(dry_run=args.dry_run, provider=args.provider, top_n=args.top_n)