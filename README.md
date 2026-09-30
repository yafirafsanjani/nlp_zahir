# NLP Zahir — Customer Support Analytics & Automated Classification Pipeline

Proyek pengolahan bahasa alami (Natural Language Processing / NLP) dan Machine Learning end-to-end untuk menganalisis percakapan ekspor WhatsApp dan media layanan customer support software akuntansi **Zahir**.

---

## 🚀 3 Output Utama Proyek
1. **client_response**: RESPONS / TIDAK_RESPONS (Mendeteksi apakah klien merespons balik bantuan admin).
2. **penanganan_remote**: REMOTE / NON_REMOTE (Mendeteksi kebutuhan remote desktop via Ultraviewer/Teamviewer + flag kredensial aman).
3. **kategori_kendala**: Klasifikasi otomatis 7 kategori permasalahan teknis Zahir (*Single-Label* berbasis *Sub-Conversation Topic Splitting*).

---

## ⚡ Cara Menjalankan Pipeline Lengkap (One-Command Full Automation)
Cukup jalankan satu perintah berikut dari root folder (pastikan virtual environment aktif):

`ash
python main.py run-all
`
*Pipeline akan mengeksekusi otomatis seluruh alur kerja dari parsing file mentah WhatsApp, pembersihan teks, training 7 model machine learning, hyperparameter tuning, hingga menghasilkan laporan analitik akhir dalam waktu ~40 detik.*

---

## 🔍 Cara Melakukan Prediksi Data Baru (Inference Engine)
Kamu bisa menggunakan model AI produksi untuk memprediksi keluhan chat secara langsung:

`ash
# Prediksi kalimat langsung:
python main.py predict "selamat pagi pak mau tanya cara aktivasi lisensi dongle"

# Prediksi berkas file chat baru (.txt / .csv):
python main.py predict data/raw/chat/chat_1.txt
`

---

## 📊 Daftar Command Pipeline (Per Fase)
| Perintah | Deskripsi |
|---|---|
| python main.py | Fase 1 & 2: Parsing WhatsApp chat & media mapping |
| python main.py explore | Fase 3: Data understanding & statistik chat |
| python main.py roles | Fase 4: Identifikasi role ADMIN, CLIENT, SYSTEM |
| python main.py conversations 4 | Fase 5: Unit percakapan (Threshold jeda 4 jam) |
| python main.py responses | Fase 6: Penentuan status respons klien |
| python main.py remote | Fase 7: Analisis penanganan remote & kredensial |
| python main.py category | Fase 8: Eksplorasi frekuensi kata & N-gram kendala |
| python main.py label | Fase 9: Data labeling & sub-conversation topic splitting |
| python main.py preprocess | Fase 10: Text preprocessing & agregasi per dokumen |
| python main.py normalize | Fase 11: Cascaded normalization (indo-normalizer + domain Zahir) |
| python main.py features | Fase 12: Ekstraksi fitur numerik TF-IDF (Unigram & Bigram) |
| python main.py split | Fase 13: Stratified train-test split (80% Train / 20% Test) |
| python main.py train | Fase 14: Melatih 7 algoritma model machine learning |
| python main.py tune | Fase 15: Hyperparameter tuning (GridSearchCV) & Voting Ensemble |
| python main.py evaluate | Fase 15: Evaluasi komprehensif pada 34 data uji independen |
| python main.py select | Fase 16: Penetapan model produksi resmi (models/best_model.pkl) |
| python main.py predict | Fase 17: Inference engine prediksi data baru |
| python main.py consolidate| Fase 18: Penggabungan master dataset final |
| python main.py export | Fase 19: Export laporan KPI eksekutif & narasi bisnis |
| python main.py run-all | Fase 20: Otomasi seluruh pipeline end-to-end |

---

## 📁 Struktur Berkas Hasil Akhir (Deliverables)
- data/output/master_conversations_final.csv: Dataset master gabungan 169 sub-percakapan lengkap dengan label dan prediksi AI.
- data/output/executive_summary.csv: Ringkasan metrik KPI layanan CS Zahir (Respons rate 90.5%, Remote rate 31.4%, AI match 94.1%).
- data/output/category_breakdown_report.csv: Tabel analitik korelasi silang kategori kendala terhadap remote dan respons.
- data/output/final_project_report.txt: Laporan naratif analitik dan 3 rekomendasi bisnis strategis untuk tim manajemen Zahir.
- models/best_model.pkl: Model AI terbaik siap produksi (*Tuned LinearSVC*, akurasi uji independen leak-free 71.8%, F1-Weighted 69.9%).
- config/taxonomy.json: **Single Source of Truth** taksonomi kategori kendala (definisi + keyword + frasa). Dipakai bersama oleh regex pipeline dan LLM labeling — nambah/mengubah kategori cukup edit file ini tanpa menyentuh kode.

---

## 🧠 Roadmap Ekspansi LLM (Peningkatan Ground Truth & Akurasi Model)

Setelah pipeline inti rampung, dikembangkan skema **LLM-assisted labeling + active learning + dynamic taxonomy expansion** agar ground truth tidak lagi bergantung penuh pada regex.

| Fase | Status | Deskripsi |
|---|---|---|
| **TAXON** - Taksonomi Config | ✅ Selesai | `config/taxonomy.json` (v2) + `src/taxonomy.py`. Definisi kategori kini berbasis **logika pembeda**: pertanyaan umum vs troubleshooting network vs error database. Pattern regex generate otomatis. |
| **LLM-L** - Modul LLM Labeling | ✅ Selesai | `src/llm_labeling.py`: prompt definisi + few-shot, kontrak JSON `{label, main_issue, reason, confidence, perlu_kategori_baru, usulan_kategori}`, temperature=0, input = keluhan klien + konteks percakapan penuh, simpan `llm_labels.csv`. Mendukung OpenAI & Gemini + `--dry-run`. Dry-run agree vs regex: 88.4%. |
| **RECON** - Reconciliation & Auto-Add Kategori | ✅ Selesai | `src/reconciliation.py`: klaster kandidat `flag_recon` (TF-IDF + connected components), LLM mengusulkan kategori baru, auto-add ke `taxonomy.json` bila ≥ `--min-samples`; laporan `reconciliation_results.csv`. |
| **ACTIVE** - Active Learning Loop | ✅ Selesai | `src/active_learning.py`: model produksi memprediksi data training, `top-N` dokumen margin probabilitas terkecil (paling ragu) dikirim ulang ke LLM untuk relabel; label konsisten (KEEP/UPDATE) jadi ground truth final, konflik tanda REVIEW. Output `active_learning_results.csv` & `ground_truth_final.csv`. Dry-run: 30 relabel -> 9 UPDATE, 4 REVIEW. |
| **AUDIT** - Audit Ground Truth | ✅ Selesai | `src/audit_labels.py`: audit non-destruktif label hasil LLM → memilah `KONSISTEN / AMBIGU / BERISIKO_SALAH` (mis. teks ber-IP/firewall tapi dilabel pertanyaan umum) → `label_audit.csv`, tanpa mengubah ground truth. |
| **CLI** - Integrasi `main.py` | ✅ Selesai | `python main.py llm-label / reconcile / active-learning / train-model / audit-labels`, flag `--skip-llm`, `--labels ground_truth|llm|existing`, `--dry-run`, `--provider`, `--top-n`. Retrain idempotent via backup `chat_with_categories.backup.csv`. |

**Cara pakai integrasi CLI (Fase 5):**
```bash
# 1. Labeling LLM pada data baru (buat llm_labels.csv)
python main.py llm-label --provider openai            # real, butuh OPENAI_API_KEY
python main.py llm-label --dry-run                    # simulasi tanpa API

# 2. Reconciliation: usulkan & auto-add kategori baru
python main.py reconcile --dry-run --min-samples 3

# 3. Active learning: relabel dokumen paling ragu dari model
python main.py active-learning --dry-run --top-n 30

# 4. Audit ground truth (non-destruktif): KONSISTEN / AMBIGU / BERISIKO_SALAH
python main.py audit-labels
python main.py audit-labels --input path/ke/csv.csv    # audit file lain

# 5. Retrain model dengan ground truth hasil LLM
python main.py train-model                            # jalur penuh: LLM -> recon -> active -> train
python main.py train-model --skip-llm                 # langsung train dari CSV label (ground_truth > llm > existing)
python main.py train-model --skip-llm --labels llm    # paksa pakai label llm_labels.csv
```

**Cara pakai active learning (Fase 4):**
```bash
# Simulasi tanpa API (menguji alur)
python src/active_learning.py --dry-run

# Real - determinisasi label ragu (butuh OPENAI_API_KEY / GEMINI_API_KEY)
python src/active_learning.py --provider openai --top-n 30
```

**Cara pakai reconciliation (Fase 3):**
```bash
# Simulasi tanpa API (menguji alur)
python src/reconciliation.py --dry-run

# Real - OpenAI/Gemini (butuh OPENAI_API_KEY / GEMINI_API_KEY)
python src/reconciliation.py --provider openai --min-samples 5

# Threshold lebih rendah (lebih agresif menambah kategori)
python src/reconciliation.py --dry-run --min-samples 3
```

**Cara pakai LLM labeling (Fase 2):**
```bash
# Simulasi tanpa API (menguji alur)
python src/llm_labeling.py --dry-run

# Real - OpenAI (setenv OPENAI_API_KEY, opsi OPENAI_MODEL)
python src/llm_labeling.py --provider openai

# Real - Gemini (setenv GEMINI_API_KEY, opsi GEMINI_MODEL)
python src/llm_labeling.py --provider gemini
```

**Prinsip desain**: LLM hanya dipakai pada fase pembentukan ground truth — **tidak pernah** di jalur prediksi harian. Saat model dirasa cukup, langkah LLM bisa dilompati (`--skip-llm`) dan langsung training dari label yang sudah ada.
---

## 📦 WhatsApp ZIP Ingestion Modul (Tahap 2)

Modul ingestion backend (`src/ingestion/`) berfungsi untuk menerima, memvalidasi, mengekstrak, dan mengorganisasi file ekspor ZIP WhatsApp secara otomatis sebelum diproses oleh pipeline NLP.

### 1. Format ZIP yang Didukung
- File arsip format `.zip` berisi 1 atau beberapa file percakapan WhatsApp (`.txt`).
- Dapat menyertakan berbagai jenis media terlampir:
  - **Gambar**: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`
  - **Video**: `.mp4`, `.mov`, `.avi`
  - **Audio**: `.m4a`, `.mp3`, `.aac`, `.ogg`
  - **Dokumen**: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.csv`

### 2. Cara Menjalankan Ingestion (Python API)
```python
from src.ingestion import ingest_whatsapp_zip

# Ingestion file ZIP ke direktori data/raw (default)
result = ingest_whatsapp_zip("WhatsApp_Export.zip")

print("Status       :", result["status"])
print("Total Chat   :", result["total_chats"])
print("Total Media  :", result["total_media"])
print("Mapping File :", result["mapping_file"])
```

### 3. Output Directory & Struktur File
Hasil pengolahan akan diorganisasi secara otomatis ke struktur standar:
```
data/
└── raw/
    ├── chat/
    │   ├── chat_1.txt
    │   ├── chat_2.txt
    │   ├── chat_mapping.json
    │   └── ingestion_session.json
    └── media/
        ├── chat_1/
        │   ├── IMG-001.jpg
        │   └── ...
        ├── chat_2/
        │   └── ...
        └── unresolved/
            └── orphan_media.png
```

### 4. Mapping Customer & Metadata (`chat_mapping.json`)
Identitas asli file dan nama customer disimpan aman tanpa mengubah file fisik:
```json
{
    "chat_1.txt": {
        "source_filename": "WhatsApp Chat dengan PT ABC.txt",
        "customer_name": "PT ABC"
    },
    "chat_2.txt": {
        "source_filename": "WhatsApp Chat dengan CV Eterna.txt",
        "customer_name": "CV Eterna"
    }
}
```
*Catatan*: Jika nama customer tidak dapat ditentukan secara pasti dari nama file, `customer_name` bernilai `null` tanpa mengarang identitas.

### 5. Media Organization & Unresolved Handling
- File media akan dipetakan ke folder `data/raw/media/chat_N/` sesuai referensi nama file di pesan chat atau struktur folder ekspor.
- Media yang tidak dapat dipetakan secara pasti dimasukkan ke folder `data/raw/media/unresolved/` dan dicatat pada list `unresolved_files`.

### 6. Keamanan & Penanganan Error (`ZipValidationError`)
Pemeriksaan integritas dan keamanan dilakukan secara otomatis:
- Menolak file non-ZIP, corrupt, atau kosong.
- **Proteksi Path Traversal**: Menolak isi ZIP yang mengandung path berbahaya seperti `../../file.txt` atau absolute path.
- Menolak file melebihi batas ukuran (default limit: 100 MB compressed / 500 MB uncompressed).

### 7. Isolasi Sesi (`session_id`) & Kompatibilitas Pipeline Existing
- Mendukung pemrosesan terisolasi via parameter `target_dir` (misal `data/runs/<session_id>`).
- Output ingestion kompatibel 100% dengan `python main.py run-all` dan fungsi `parse_whatsapp_chats()`.

---

## 🌋 Cara Menjalankan FastAPI REST Backend (API Server)
Untuk menjalankan server REST API secara lokal:

```bash
uvicorn app.main:app --reload
```

Server API akan berjalan pada http://127.0.0.1:8000.
- **Dokumentasi Interactive Swagger UIa*: http://127.0.0.1:8000/docs
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

---

## Analytics API (Task 3B)

Analytics is read-only. Without `session_id`, every endpoint reads the existing default dataset at `data/output/master_conversations_final.csv`, so a dashboard can display data immediately. With `session_id`, it reads only that completed upload-analysis session. Swagger is available at `http://127.0.0.1:8000/docs`.

| Endpoint | Required query | Optional query | Description |
| --- | --- | --- | --- |
| `GET /api/overview` | none | `session_id`, `start_date`, `end_date` | KPIs, leading category, distribution, and period |
| `GET /api/issues` | none | `session_id`, `start_date`, `end_date` | Category-level issue and remote statistics |
| `GET /api/remote` | none | `session_id`, `start_date`, `end_date` | Remote totals by category and customer |
| `GET /api/customers` | none | `session_id`, `start_date`, `end_date` | Customer-level issue and remote statistics |
| `GET /api/time-series` | none | `session_id`, `period`, `start_date`, `end_date` | Daily, weekly, monthly, or yearly issue totals |

Example:

```text
GET /api/overview?session_id=session_20260930_ab12cd
GET /api/time-series?session_id=session_20260930_ab12cd&period=monthly
GET /api/overview
```

`remote_rate` is `remote_cases / (remote_cases + non_remote_cases) * 100`. Unknown remote values are reported separately and are never treated as non-remote. Remote input accepts the pipeline values `REMOTE` and `NON_REMOTE`, plus common boolean/numeric representations.

The analytical unit is one unique `sub_conversation_id`. Categories use `kategori_kendala_ml_predicted` only when it is present; missing or invalid predictions are returned as `UNKNOWN_UNCLASSIFIED`. Ground-truth labels are intentionally not substituted into dashboard inference.

Customer display names come from the session's `raw/chat/chat_mapping.json` only when `customer_name` is present. Otherwise the API returns a distinct `Unknown (<source_file>)` value to preserve source boundaries without inventing an identity. No conversation content or credential flag is returned.

Time series use `start_time`; invalid or missing timestamps are excluded only from time-series records. Date filters use ISO `YYYY-MM-DD`, are inclusive, and apply consistently to every endpoint. Weekly rows start on Monday and use that Monday date as the label. Each response includes `dataset`, for example `{"type": "default", "session_id": null}` or `{"type": "session", "session_id": "..."}`. The default CSV is used only when `session_id` is omitted. An invalid session or a session without output returns `404`; it never falls back to the default dataset.

An overview response has this shape:

```json
{
  "session_id": "session_20260930_ab12cd",
  "total_issues": 12,
  "remote_rate": 42.86,
  "top_issue": {"category": "TRANSAKSI_INPUT_DATA", "count": 5},
  "category_distribution": [],
  "analysis_period": {"start": "2026-09-01T09:00:00", "end": "2026-09-30T15:30:00"}
}
```

Run all backend and analytics tests with:

```bash
python -m unittest discover -s tests
```
