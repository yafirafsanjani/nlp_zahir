"""
predict.py - Inference Engine untuk Prediksi Data Baru (Fase 17)

Menyediakan pipeline inferensi end-to-end:
Raw Text -> Preprocessing -> Normalization -> TF-IDF Vectorizer -> Best Model.
Mendukung:
1. Prediksi kalimat teks langsung via CLI / argumen.
2. Mode interaktif ketik chat di terminal.
3. Prediksi batch file chat WhatsApp baru (.txt / .csv).
Menghasilkan label kategori kendala beserta tingkat keyakinan (confidence score).
"""

import sys
import csv
import pickle
import numpy as np
from pathlib import Path

# Import pipeline preprocessing & normalisasi yang sudah teruji
from src.preprocessing import clean_text_advanced
from src.normalization import normalize_text_cascaded

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "data" / "output"
BEST_MODEL_FILE = MODELS_DIR / "best_model.pkl"
VECTORIZER_FILE = MODELS_DIR / "tfidf_vectorizer.pkl"

_cached_model = None
_cached_vectorizer = None

def load_inference_artifacts():
    global _cached_model, _cached_vectorizer
    if _cached_model is None or _cached_vectorizer is None:
        if not BEST_MODEL_FILE.exists() or not VECTORIZER_FILE.exists():
            raise FileNotFoundError(
                "Model atau vectorizer belum tersedia. Jalankan 'python main.py select' terlebih dahulu."
            )
        with open(BEST_MODEL_FILE, "rb") as f:
            _cached_model = pickle.load(f)
        with open(VECTORIZER_FILE, "rb") as f:
            _cached_vectorizer = pickle.load(f)
    return _cached_model, _cached_vectorizer

def predict_single_text(raw_text):
    """
    Menjalankan inferensi end-to-end pada satu teks pesan chat:
    1. Preprocessing (Pembersihan teks mentah)
    2. Normalization (Cascaded Slang Normalization)
    3. TF-IDF Vectorization
    4. Model Classification & Confidence Score
    """
    model, vectorizer = load_inference_artifacts()

    clean_text = clean_text_advanced(raw_text)
    norm_text, _ = normalize_text_cascaded(clean_text)

    if not norm_text.strip():
        return {
            "predicted_category": "LAINNYA_UNCATEGORIZED",
            "confidence": 100.0,
            "all_probabilities": {},
            "normalized_text": "",
        }

    X_vec = vectorizer.transform([norm_text])
    pred_label = model.predict(X_vec)[0]

    probs_dict = {}
    confidence = 0.0
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X_vec)[0]
        confidence = float(np.max(probs) * 100)
        for cls_name, prob in zip(model.classes_, probs):
            probs_dict[cls_name] = round(float(prob * 100), 2)
    else:
        confidence = 100.0

    return {
        "predicted_category": pred_label,
        "confidence": confidence,
        "all_probabilities": probs_dict,
        "normalized_text": norm_text,
    }

def predict_batch_file(filepath):
    """
    Membaca berkas teks chat atau CSV, memprediksi kategori kendala,
    dan menyimpan hasilnya ke data/output/predictions_*.csv.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"[ERROR] Berkas tidak ditemukan: {path}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUTPUT_DIR / f"predictions_{path.stem}.csv"

    print(f"\nMemproses file batch: {path}")

    results = []
    # Jika file CSV
    if path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                raw_text = row.get("normalized_text") or row.get("clean_text") or row.get("percakapan") or ""
                res = predict_single_text(raw_text)
                row_copy = dict(row)
                row_copy["predicted_kategori"] = res["predicted_category"]
                row_copy["confidence_pct"] = f"{res['confidence']:.1f}%"
                results.append(row_copy)
    else:
        # Jika file teks mentah
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        for i, line in enumerate(lines, 1):
            res = predict_single_text(line)
            results.append({
                "line_id": i,
                "text": line[:150],
                "predicted_kategori": res["predicted_category"],
                "confidence_pct": f"{res['confidence']:.1f}%",
            })

    if results:
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)

    print(f"Prediksi selesai! Total {len(results)} baris diproses.")
    print(f"Hasil batch tersimpan di: {out_csv}\n")
    return out_csv

def interactive_mode():
    print("\n" + "=" * 65)
    print("  MODE PREDIKSI INTERAKTIF (Ketik 'exit' atau 'keluar' untuk selesai)")
    print("=" * 65)
    while True:
        try:
            user_input = input("\nMasukkan teks chat keluhan Zahir: ").strip()
            if user_input.lower() in ("exit", "keluar", "q"):
                print("Keluar dari mode interaktif. Sampai jumpa!")
                break
            if not user_input:
                continue

            res = predict_single_text(user_input)
            print("-" * 50)
            print(f"Teks Baku : \"{res['normalized_text']}\"")
            print(f"Prediksi  : [{res['predicted_category']}]")
            print(f"Keyakinan : {res['confidence']:.1f}%")
            if res["all_probabilities"]:
                print("Distribusi Probabilitas:")
                sorted_probs = sorted(res["all_probabilities"].items(), key=lambda x: x[1], reverse=True)
                for cat, prob in sorted_probs[:3]:
                    print(f"  - {cat:<28}: {prob}%")
            print("-" * 50)
        except (KeyboardInterrupt, EOFError):
            print("\nKeluar.")
            break

def run(arg=None):
    print("=" * 60)
    print("  FASE 17 — PREDIKSI DATA BARU (INFERENCE ENGINE)")
    print("=" * 60)

    load_inference_artifacts()

    if arg:
        p = Path(arg)
        if p.exists() and p.is_file():
            predict_batch_file(p)
        else:
            # Argumen berupa teks kalimat langsung
            print(f"\nMemprediksi teks masukan:")
            print(f"Input: \"{arg}\"")
            res = predict_single_text(arg)
            print("-" * 60)
            print(f"Teks Ternormalisasi : \"{res['normalized_text']}\"")
            print(f"Prediksi Kategori   : [{res['predicted_category']}]")
            print(f"Keyakinan AI        : {res['confidence']:.1f}%\n")
            if res["all_probabilities"]:
                print("Top Probabilitas:")
                sorted_probs = sorted(res["all_probabilities"].items(), key=lambda x: x[1], reverse=True)
                for cat, prob in sorted_probs[:3]:
                    print(f"  - {cat:<28}: {prob}%")
            print("-" * 60)
    else:
        # Jalankan beberapa contoh pengujian otomatis jika tidak ada argumen
        test_samples = [
            "selamat pagi admin mau tanya registrasi lisensi dongle nomor seri berapa ya",
            "pak ini database firebird corrupt tidak bisa dibuka error",
            "bagaimana cara buat nota faktur penjualan dan pelunasan piutang",
            "bisa minta tolong cetak laporan laba rugi bulanan ke format pdf excel",
            "mau tanya cara menghubungkan aplikasi komputer anak an ke komputer induk",
        ]
        print("\nMenjalankan Pengujian 5 Skenario Chat Nyata:")
        for idx, text in enumerate(test_samples, 1):
            res = predict_single_text(text)
            print(f"\n{idx}. Chat: \"{text}\"")
            print(f"   -> Hasil: [{res['predicted_category']}] ({res['confidence']:.1f}% keyakinan)")
        print("\nTips Penggunaan:")
        print("1. Prediksi teks langsung: python main.py predict \"kalimat chat kamu\"")
        print("2. Prediksi berkas file : python main.py predict path/ke/file_chat.txt")

    print("\n" + "=" * 60)
    print("  FASE 17 SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    cli_arg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    run(cli_arg)