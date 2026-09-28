import os
import csv
import unittest
from pathlib import Path

from src import (
    parse_whatsapp_chats,
    identify_roles,
    group_conversations,
    analyze_client_responses,
    classify_remote,
    label_sub_conversations,
    preprocess_text_data,
    clean_text_advanced,
    normalize_text_data,
    normalize_text_cascaded,
    predict_single_text,
    consolidate_master_data,
    export_all_reports,
    process_conversations,
    run_full_pipeline,
)

BASE_DIR = Path(__file__).resolve().parent.parent

class TestNLPPipelineAPI(unittest.TestCase):

    def test_imports(self):
        """Pastikan seluruh fungsi API utama dapat di-import dengan baik dari package src."""
        self.assertTrue(callable(parse_whatsapp_chats))
        self.assertTrue(callable(identify_roles))
        self.assertTrue(callable(group_conversations))
        self.assertTrue(callable(analyze_client_responses))
        self.assertTrue(callable(classify_remote))
        self.assertTrue(callable(label_sub_conversations))
        self.assertTrue(callable(preprocess_text_data))
        self.assertTrue(callable(normalize_text_data))
        self.assertTrue(callable(predict_single_text))
        self.assertTrue(callable(consolidate_master_data))
        self.assertTrue(callable(export_all_reports))
        self.assertTrue(callable(process_conversations))
        self.assertTrue(callable(run_full_pipeline))

    def test_text_preprocessing_and_normalization(self):
        """Uji fungsi pembersihan teks dan cascaded normalization."""
        raw_text = "Pagi pak, database firebird corrupt tidak bisa dibuka error!!"
        clean_text = clean_text_advanced(raw_text)
        self.assertNotIn("!", clean_text)

        norm_text, count = normalize_text_cascaded(clean_text)
        self.assertIn("firebird", norm_text)

    def test_remote_classification_logic(self):
        """Uji logika klasifikasi remote dan deteksi kredensial."""
        from src.remote import analyze_conversation_remote

        msgs_remote = [
            {"role": "CLIENT", "percakapan": "Pak tolong bantu via ultraviewer id 123456789 pass 1234"},
            {"role": "ADMIN", "percakapan": "Baik pak kami remote sekarang"},
        ]
        status, cred = analyze_conversation_remote(msgs_remote)
        self.assertEqual(status, "REMOTE")
        self.assertTrue(cred)

        msgs_non_remote = [
            {"role": "CLIENT", "percakapan": "Bagaimana cara cetak laporan laba rugi?"},
            {"role": "ADMIN", "percakapan": "Masuk ke menu laporan lalu pilih laba rugi"},
        ]
        status2, cred2 = analyze_conversation_remote(msgs_non_remote)
        self.assertEqual(status2, "NON_REMOTE")
        self.assertFalse(cred2)

    def test_single_prediction_engine(self):
        """Uji inferensi model machine learning untuk single text prediction."""
        sample_text = "bisa bantu registrasi lisensi dongle zahir"
        res = predict_single_text(sample_text)
        self.assertIn("predicted_category", res)
        self.assertIn("confidence", res)
        self.assertIn("all_probabilities", res)
        self.assertIn("normalized_text", res)
        self.assertIsInstance(res["confidence"], float)

    def test_master_dataset_structure_compatibility(self):
        """Validasi ketersediaan dan skema kolom master dataset untuk kebutuhan dashboard."""
        master_file = BASE_DIR / "data" / "output" / "master_conversations_final.csv"
        self.assertTrue(master_file.exists(), "Master output file harus tersedia")

        with open(master_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)

        required_columns = [
            "sub_conversation_id",
            "conversation_id",
            "source_file",
            "start_time",
            "end_time",
            "total_messages",
            "client_messages_count",
            "admin_messages_count",
            "has_media",
            "contains_credentials",
            "client_response",
            "penanganan_remote",
            "kategori_kendala_ground_truth",
            "kategori_kendala_ml_predicted",
            "prediction_confidence",
            "prediction_match",
            "full_conversation",
        ]

        for col in required_columns:
            self.assertIn(col, fieldnames, f"Kolom {col} wajib ada di master dataset untuk dashboard")

        self.assertGreater(len(rows), 0, "Master dataset tidak boleh kosong")

if __name__ == "__main__":
    unittest.main()
