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
- models/best_model.pkl: Model AI terbaik siap produksi (*Tuned Gradient Boosting*, akurasi uji 70.6%).