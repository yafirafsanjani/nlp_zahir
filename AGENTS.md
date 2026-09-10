# PROJECT NLP ZAHIR — STATUTE & PROGRESS DOCUMENTATION

## 1. GAMBARAN UMUM PROJECT
Project **nlp_zahir** bertujuan untuk menganalisis data percakapan WhatsApp export dan media terkait layanan customer support **Zahir**.

### Output Utama Project:
1. **client_response**: `RESPONS` / `TIDAK_RESPONS`
2. **kategori_kendala**: Kategori permasalahan percakapan
3. **penanganan_remote**: `REMOTE` / `NON_REMOTE`

---

## 2. STRUKTUR DIREKTORI DATA & CODE
```
nlp_zahir/
├── data/
│   ├── raw/
│   │   ├── chat/
│   │   │   ├── chat_1.txt
│   │   │   └── chat_2.txt
│   │   └── media/
│   │       ├── chat_1/ (11 file .jpg)
│   │       └── chat_2/ (32 file .jpg)
│   ├── processed/
│   │   ├── chat_parsed.csv
│   │   ├── chat_with_roles.csv
│   │   ├── chat_with_conversations.csv
│   │   ├── chat_with_responses.csv
│   │   └── chat_with_remotes.csv
│   └── output/
├── models/
├── src/
│   ├── __init__.py
│   ├── parser.py          (Fase 1 & 2: Parsing chat & mapping media)
│   ├── exploration.py     (Fase 3: Data understanding & validation)
│   ├── roles.py           (Fase 4: Identifikasi ADMIN, CLIENT, SYSTEM)
│   ├── conversation.py    (Fase 5: Unit percakapan / threshold 4 jam)
│   ├── client_response.py (Fase 6: Penentuan RESPONS / TIDAK_RESPONS)
│   └── remote.py          (Fase 7: Penentuan REMOTE / NON_REMOTE)
├── main.py                (CLI Entry Point)
├── requirements.txt
├── AGENTS.md              (Dokumentasi Status Sesi ini)
└── README.md
```

---

## 3. COMMAND REFERENCE (CARA MENJALANKAN PIPELINE)
Semua command dijalankan dari root direktori dalam Virtual Environment Python:

- **Fase 1-2 (Parsing & Media Mapping)**:
  `python main.py`
- **Fase 3 (Data Understanding & Validation)**:
  `python main.py explore`
- **Fase 4 (Identifikasi Role Admin & Client)**:
  `python main.py roles`
- **Fase 5 (Pembentukan Unit Percakapan - Threshold 4 Jam)**:
  `python main.py conversations 4`
- **Fase 6 (Analisis Respons Klien)**:
  `python main.py responses`
- **Fase 7 (Analisis Penanganan Remote)**:
  `python main.py remote`

---

## 4. STATUS PERKEMBANGAN PIPELINE (PROGRESS TRACKER)

- [x] **FASE 0 — Setup Project**: Struktur folder disiapkan, `.gitignore` dikonfigurasi.
- [x] **FASE 1 — Data Ingestion**: Membaca file `.txt` dari `data/raw/chat/` (Total: 1,735 pesan).
- [x] **FASE 2 — Parsing WhatsApp**: Ekstraksi tanggal, waktu, pengirim, percakapan, & mapping 43 file gambar.
- [x] **FASE 3 — Data Understanding & Validation**: Eksplorasi statistik, panjang pesan, & identifikasi konten khusus.
- [x] **FASE 4 — Identifikasi Client & Admin**: Assign role (`ADMIN`: 873 pesan, `CLIENT`: 859 pesan, `SYSTEM`: 3 pesan).
- [x] **FASE 5 — Pembentukan Unit Percakapan**: Threshold 4 jam -> 121 unit percakapan (`conversation_id`).
- [x] **FASE 6 — Analisis Respons Klien**: 106 percakapan `RESPONS` (87.6%), 15 percakapan `TIDAK_RESPONS` (12.4%).
- [x] **FASE 7 — Analisis Penanganan Remote**: 32 percakapan `REMOTE` (26.4%), 89 percakapan `NON_REMOTE` (73.6%), 52 pesan `contains_credentials=True`.
- [ ] **FASE 8 — Eksplorasi Kategori Kendala**: **<-- FASE SAAT INI / SELANJUTNYA**
- [ ] **FASE 9 — Data Labeling**
- [ ] **FASE 10 — Text Preprocessing**
- [ ] **FASE 11 — Normalisasi Bahasa Chat**
- [ ] **FASE 12 — Feature Extraction (TF-IDF)**
- [ ] **FASE 13 — Train-Test Split**
- [ ] **FASE 14 — Training Model**
- [ ] **FASE 15 — Evaluasi Model**
- [ ] **FASE 16 — Model Selection & Saving**
- [ ] **FASE 17 — Prediksi Data Baru**
- [ ] **FASE 18 — Penggabungan Hasil**
- [ ] **FASE 19 — Export Hasil**
- [ ] **FASE 20 — Main Pipeline / Automation**

---

## 5. CATATAN PENTING & PRINSIP KEAMANAN
1. **Logika Bisnis vs ML**: Fase 4 s.d. 7 murni menggunakan Business Logic / Rule-Based berbasis data nyata. Model ML baru akan dilatih pada Fase 14 untuk klasifikasi otomatis.
2. **Privasi & Kredensial**: Tidak ada ID/Password remote asli yang diekstrak/disimpan di CSV. Hanya menggunakan boolean flag `contains_credentials`.
3. **Data Raw**: Folder `data/raw/` dan `data/processed/` diabaikan oleh Git (sesuai `.gitignore`).
