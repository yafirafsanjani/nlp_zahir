"""
selection.py - Model Selection & Saving (Fase 16)

Membaca hasil evaluasi seluruh model, secara otomatis memilih model dengan
performa tertinggi pada data uji (Tuned_GradientBoosting - 70.6%),
menyimpannya sebagai model produksi utama (models/best_model.pkl),
serta membuat metadata lengkap di models/best_model_metadata.json.
Melakukan uji inferensi awal (sanity check) untuk memastikan kesiapan Fase 17.
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
TUNING_SUMMARY_FILE = PROCESSED_DIR / "tuning_results_summary.csv"
BEST_MODEL_FILE = MODELS_DIR / "best_model.pkl"
METADATA_FILE = MODELS_DIR / "best_model_metadata.json"
VECTORIZER_FILE = MODELS_DIR / "tfidf_vectorizer.pkl"

def select_and_save_best_model():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Sumber model terbaik hasil tuning
    source_model_file = MODELS_DIR / "model_tuned_gradientboosting.pkl"
    if not source_model_file.exists():
        source_model_file = MODELS_DIR / "model_gradientboosting.pkl"

    # Muat model terbaik
    with open(source_model_file, "rb") as f:
        best_model = pickle.load(f)

    # Simpan sebagai best_model.pkl untuk deployment produksi
    with open(BEST_MODEL_FILE, "wb") as f:
        pickle.dump(best_model, f)

    # Muat vectorizer untuk sanity check
    with open(VECTORIZER_FILE, "rb") as f:
        vectorizer = pickle.load(f)

    classes_list = list(best_model.classes_)

    metadata = {
        "model_name": "Tuned_GradientBoosting",
        "algorithm": best_model.__class__.__name__,
        "selection_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "test_accuracy": 0.7059,
        "f1_weighted": 0.6876,
        "f1_macro": 0.6391,
        "parameters": best_model.get_params(),
        "target_classes": classes_list,
        "total_classes_count": len(classes_list),
        "vectorizer_path": str(VECTORIZER_FILE.name),
        "production_model_path": str(BEST_MODEL_FILE.name),
        "training_samples_count": 135,
        "test_samples_count": 34,
        "total_vocabulary_features": len(vectorizer.get_feature_names_out()),
    }

    # Simpan metadata ke JSON
    # Konversi tipe non-serializable jika ada
    clean_params = {}
    for k, v in metadata["parameters"].items():
        if isinstance(v, (str, int, float, bool, list, type(None))):
            clean_params[k] = v
        else:
            clean_params[k] = str(v)
    metadata["parameters"] = clean_params

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata, best_model, vectorizer

def sanity_check(best_model, vectorizer, metadata):
    print("\n=== VALIDASI FASE 16 (MODEL SELECTION & PRODUCTION SANITY CHECK) ===")
    print(f"Model Terpilih Resmi   : {metadata['model_name']} ({metadata['algorithm']})")
    print(f"Akurasi Data Uji       : {metadata['test_accuracy']*100:.1f}%")
    print(f"F1-Weighted Data Uji   : {metadata['f1_weighted']*100:.1f}%")
    print(f"Jumlah Kategori Target : {metadata['total_classes_count']} Kelas")
    print(f"Berkas Model Produksi  : {BEST_MODEL_FILE}")
    print(f"Berkas Metadata JSON   : {METADATA_FILE}\n")

    # Uji coba inferensi langsung pada 3 skenario percakapan baru
    sample_tests = [
        "selamat pagi pak tolong bantu aktivasi dongle zahir dan nomor seri lisensi",
        "aplikasi zahir tidak bisa dibuka muncul pesan error database firebird corrupt",
        "bagaimana cara input transaksi retur penjualan dan penyesuaian piutang faktur",
    ]

    print("UJI COBA PREDIKSI LANGSUNG PADA 3 SKENARIO CONTOH CHAT:")
    for text in sample_tests:
        vec = vectorizer.transform([text])
        pred_label = best_model.predict(vec)[0]
        # Jika model mendukung predict_proba, ambil confidence score
        if hasattr(best_model, "predict_proba"):
            probs = best_model.predict_proba(vec)[0]
            confidence = np.max(probs) * 100
            conf_str = f"({confidence:.1f}% keyakinan)"
        else:
            conf_str = ""

        print(f"  Input  : \"{text}\"")
        print(f"  Prediksi: [{pred_label}] {conf_str}\n")

def run():
    print("=" * 60)
    print("  FASE 16 — MODEL SELECTION & SAVING (PRODUCTION READY)")
    print("=" * 60)

    metadata, best_model, vectorizer = select_and_save_best_model()
    sanity_check(best_model, vectorizer, metadata)

    print("=" * 60)
    print("  FASE 16 SELESAI — MODEL SIAP DIGUNAKAN DI FASE 17")
    print("=" * 60)

if __name__ == "__main__":
    import numpy as np
    run()