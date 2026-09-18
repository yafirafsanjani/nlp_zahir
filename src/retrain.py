"""
retrain.py - Jalur Retrain Model dengan Label Non-Regex (Fase Ekspansi LLM 5/5)

Data baru yang belum punya ground truth melewati jalur LLM lalu training:
    python main.py train-model                 # LLM labeling -> reconciliation -> active learning -> train
    python main.py train-model --skip-llm      # pakai label CSV yang sudah ada & langsung train

Sumber label dipilih lewat argumen --labels:
    auto         (default) ground_truth_final.csv > llm_labels.csv > label existing
    ground_truth           pakai data/processed/ground_truth_final.csv (Fase ACTIVE)
    llm                    pakai data/processed/llm_labels.csv (Fase LLM-L)
    existing               pakai label regex/chow full yang sudah ada di chat_with_categories.csv

Setiap kali dijalankan, dataset label dipulihkan dulu dari backup regex murni
(chat_with_categories.backup.csv) supaya proses retrain idempotent.
"""

import csv
import os
import shutil
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CHAT_CATEGORIES_FILE = PROCESSED_DIR / "chat_with_categories.csv"
BACKUP_FILE = PROCESSED_DIR / "chat_with_categories.backup.csv"
LLM_LABELS_FILE = PROCESSED_DIR / "llm_labels.csv"
GROUND_TRUTH_FILE = PROCESSED_DIR / "ground_truth_final.csv"

PROVIDER_KEY_ENV = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}


def _print_banner(msg):
    print("\n" + "=" * 60)
    print("  " + msg)
    print("=" * 60)


def _load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _require_file(path, hint):
    if not path.exists():
        print(f"[ERROR] File tidak ditemukan: {path}")
        print(f"        {hint}")
        return False
    return True


def _resolve_label_rows_chaining(source, provider):
    """Menjalankan LLM labeling -> reconciliation -> active learning bila dipilih."""
    if not provider:
        provider = os.getenv("LLM_PROVIDER", "openai")
    key_env = PROVIDER_KEY_ENV.get(provider)
    if not key_env or not os.getenv(key_env):
        print(f"[ERROR] Provider '{provider}' butuh env {key_env}. " 
              "Set API key dulu atau jalankan dengan --skip-llm / --labels existing.")
        return None

    print(f"\n[1/3] LLM Labeling (real, provider={provider})...")
    from src.llm_labeling import run as run_llm
    run_llm(provider=provider, dry_run=False)

    print(f"\n[2/3] Reconciliation & Auto-Add Kategori (real)...")
    from src.reconciliation import run as run_recon
    run_recon(provider=provider, dry_run=False)

    print(f"\n[3/3] Active Learning Loop (real)...")
    from src.active_learning import run as run_active
    run_active(dry_run=False, provider=provider)

    return None  # label final diambil dari ground_truth_final.csv


def _build_label_map(source):
    """Mengembalikan dict {sub_conversation_id: label} sesuai sumber label."""
    if source == "existing":
        return None, "existing (regex/current), tanpa perubahan"

    if source == "llm":
        if not _require_file(LLM_LABELS_FILE, "Jalankan python main.py llm-label dulu."):
            return None, source
        rows = _load_csv(LLM_LABELS_FILE)
        mapping = {r["sub_conversation_id"]: r["kategori_llm"] for r in rows}
        return mapping, "LLM labeling (llm_labels.csv)"

    # source == ground_truth (default final)
    if not _require_file(GROUND_TRUTH_FILE,
                         "Jalankan Fase ACTIVE dulu (python src/active_learning.py)."):
        return None, source
    rows = _load_csv(GROUND_TRUTH_FILE)
    mapping = {r["sub_conversation_id"]: r["kategori_kendala_final"] for r in rows}
    return mapping, "active learning ground truth (ground_truth_final.csv)"


def _apply_labels(mapping):
    """Pulihkan dari backup regex murni, lalu terapkan label baru."""
    if not _require_file(CHAT_CATEGORIES_FILE, "Jalankan pipeline inti (run-all) dulu."):
        return False

    if not BACKUP_FILE.exists():
        shutil.copy2(CHAT_CATEGORIES_FILE, BACKUP_FILE)
        print(f"Backup label regex murni dibuat: {BACKUP_FILE.name}")
    else:
        shutil.copy2(BACKUP_FILE, CHAT_CATEGORIES_FILE)

    rows = _load_csv(CHAT_CATEGORIES_FILE)
    mapped = sum(1 for r in rows if r["sub_conversation_id"] in mapping)
    if mapped == 0:
        print(f"[ERROR] Tidak ada sub_conversation_id yang cocok dengan sumber label.")
        print("        Dataset label dikembalikan ke kondisi awal (regex).")
        return False

    for r in rows:
        if r["sub_conversation_id"] in mapping:
            r["kategori_kendala"] = mapping[r["sub_conversation_id"]]

    with open(CHAT_CATEGORIES_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Label baru diterapkan ke {mapped} baris pada {CHAT_CATEGORIES_FILE.name}")
    return True


def _run_chain():
    steps = [
        ("Fase 10  : Preprocessing & Agregasi", "src.preprocessing"),
        ("Fase 11  : Cascaded Normalization", "src.normalization"),
        ("Fase 12  : Feature Extraction TF-IDF", "src.features"),
        ("Fase 13  : Stratified Train-Test Split", "src.split"),
        ("Fase 14  : Training 7 Model", "src.train"),
        ("Fase 15.1: Hyperparameter Tuning & Ensemble", "src.tuning"),
        ("Fase 15.2: Evaluasi Independen", "src.evaluation"),
        ("Fase 16  : Model Selection & Saving", "src.selection"),
    ]
    for desc, module_name in steps:
        s = time.time()
        print(f"\n[CHAIN] {desc} ...")
        mod = __import__(module_name, fromlist=["run"])
        mod.run()
        print(f"-> {desc} selesai dalam {time.time() - s:.2f} detik.")


def run(label_source="auto", skip_llm=False, provider=None):
    print("=" * 60)
    print("  RETRAIN MODEL — jalur ground truth non-regex")
    print("=" * 60)

    source = label_source

    if not skip_llm and source == "auto":
        print("- Tanpa --skip-llm: LLM labeling -> reconciliation -> active learning -> train.")
        _resolve_label_rows_chaining("auto", provider)
        if not GROUND_TRUTH_FILE.exists():
            print("[ERROR] ground_truth_final.csv tidak terbentuk. Cek API key / jalankan --dry-run.")
            return
        source = "ground_truth"

    print(f"\nSumber label: {source}")
    if source == "auto":
        if GROUND_TRUTH_FILE.exists():
            source = "ground_truth"
        elif LLM_LABELS_FILE.exists():
            source = "llm"
        else:
            source = "existing"

    mapping, desc = _build_label_map(source)
    _print_banner(f"SUMBER LABEL: {desc}")

    if mapping is not None:
        ok = _apply_labels(mapping)
        if not ok:
            return

    _run_chain()

    print("\n" + "=" * 60)
    print("  RETRAIN SELESAI — model produksi diperbarui (models/best_model.pkl)")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Retrain model dengan label baru")
    parser.add_argument("--labels", default="auto",
                        choices=["auto", "ground_truth", "llm", "existing"])
    parser.add_argument("--skip-llm", action="store_true")
    parser.add_argument("--provider", default=None)
    args = parser.parse_args()
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    run(label_source=args.labels, skip_llm=args.skip_llm, provider=args.provider)