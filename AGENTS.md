# PROJECT NLP ZAHIR — STATUTE & PROGRESS DOCUMENTATION

## 1. GAMBARAN UMUM PROJECT
Project **nlp_zahir** bertujuan untuk menganalisis data percakapan WhatsApp export dan media terkait layanan customer support **Zahir**.

### Output Utama Project:
1. **client_response**: RESPONS / TIDAK_RESPONS
2. **kategori_kendala**: Kategori permasalahan percakapan (Single-Label per sub_conversation_id)
3. **penanganan_remote**: REMOTE / NON_REMOTE

---

## 2. STRUKTUR DIREKTORI DATA & CODE
`
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
│   │   ├── chat_with_remotes.csv
│   │   └── chat_with_categories.csv
│   └── output/
├── models/
├── src/
│   ├── __init__.py
│   ├── parser.py                (Fase 1 & 2: Parsing chat & mapping media)
│   ├── exploration.py           (Fase 3: Data understanding & validation)
│   ├── roles.py                 (Fase 4: Identifikasi ADMIN, CLIENT, SYSTEM)
│   ├── conversation.py          (Fase 5: Unit percakapan / threshold 4 jam)
│   ├── client_response.py       (Fase 6: Penentuan RESPONS / TIDAK_RESPONS)
│   ├── remote.py                (Fase 7: Penentuan REMOTE / NON_REMOTE)
│   ├── category_exploration.py  (Fase 8: Eksplorasi Kategori Kendala)
│   └── category_labeling.py     (Fase 9: Data Labeling & Sub-Conversation Splitting)
├── main.py                      (CLI Entry Point)
├── requirements.txt
├── AGENTS.md                    (Dokumentasi Status Sesi ini)
└── README.md
`

---

## 3. COMMAND REFERENCE (CARA MENJALANKAN PIPELINE)
Semua command dijalankan dari root direktori dalam Virtual Environment Python:

- **Fase 1-2 (Parsing & Media Mapping)**:
  python main.py
- **Fase 3 (Data Understanding & Validation)**:
  python main.py explore
- **Fase 4 (Identifikasi Role Admin & Client)**:
  python main.py roles
- **Fase 5 (Pembentukan Unit Percakapan - Threshold 4 Jam)**:
  python main.py conversations 4
- **Fase 6 (Analisis Respons Klien)**:
  python main.py responses
- **Fase 7 (Analisis Penanganan Remote)**:
  python main.py remote
- **Fase 8 (Eksplorasi Kategori Kendala)**:
  python main.py category
- **Fase 9 (Data Labeling & Sub-Conversation Splitting)**:
  python main.py label

---

## 4. STATUS PERKEMBANGAN PIPELINE (PROGRESS TRACKER)

- [x] **FASE 0 — Setup Project**: Struktur folder disiapkan, .gitignore dikonfigurasi.
- [x] **FASE 1 — Data Ingestion**: Membaca file .txt dari data/raw/chat/ (Total: 1,735 pesan).
- [x] **FASE 2 — Parsing WhatsApp**: Ekstraksi tanggal, waktu, pengirim, percakapan, & mapping 43 file gambar.
- [x] **FASE 3 — Data Understanding & Validation**: Eksplorasi statistik, panjang pesan, & identifikasi konten khusus.
- [x] **FASE 4 — Identifikasi Client & Admin**: Assign role (ADMIN: 873 pesan, CLIENT: 859 pesan, SYSTEM: 3 pesan).
- [x] **FASE 5 — Pembentukan Unit Percakapan**: Threshold 4 jam -> 121 unit percakapan (conversation_id).
- [x] **FASE 6 — Analisis Respons Klien**: 106 percakapan RESPONS (87.6%), 15 percakapan TIDAK_RESPONS (12.4%).
- [x] **FASE 7 — Analisis Penanganan Remote**: 32 percakapan REMOTE (26.4%), 89 percakapan NON_REMOTE (73.6%), 52 pesan contains_credentials=True.
- [x] **FASE 8 — Eksplorasi Kategori Kendala**: Analisis frekuensi N-gram pesan klien & kandidat pemetaan kategori kendala.
- [x] **FASE 9 — Data Labeling**: Menggunakan **OPSI A (Sub-Conversation Topic Splitting)** -> 121 parent conversations dipecah presisi menjadi 169 sub-unit percakapan (sub_conversation_id) berlabel tunggal presisi. Output: chat_with_categories.csv.
- [ ] **FASE 10 — Text Preprocessing**: **<-- FASE SAAT INI / SELANJUTNYA (AKAN DILANJUTKAN)**
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
1. **Konsep Sub-Conversation Splitting (OPSI A)**: Diterapkan di Fase 9 untuk menangani percakapan panjang yang mengandung lebih dari 1 masalah. Dari 121 conversation_id, sebanyak 29 percakapan panjang dipecah berdasarkan pergeseran topik keluhan menjadi total 169 sub_conversation_id (_a, _b, _c, _d). Hal ini memastikan setiap masalah keluhan tercatat 100% presisi tanpa ada yang tenggelam.
2. **Logika Bisnis vs ML**: Fase 4 s.d. 9 murni menggunakan Business Logic / Rule-Based berbasis data nyata. Model ML baru akan dilatih pada Fase 14 untuk klasifikasi otomatis.
3. **Privasi & Kredensial**: Tidak ada ID/Password remote asli yang diekstrak/disimpan di CSV. Hanya menggunakan boolean flag contains_credentials.
4. **Data Raw**: Folder data/raw/ dan data/processed/ diabaikan oleh Git (sesuai .gitignore).