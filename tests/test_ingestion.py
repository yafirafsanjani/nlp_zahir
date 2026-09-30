import os
import json
import zipfile
import unittest
import tempfile
from pathlib import Path

from src.ingestion import (
    ingest_whatsapp_zip,
    validate_zip_file,
    ZipValidationError,
)
from src.ingestion.chat_detector import detect_chat_files, is_whatsapp_chat_content
from src.ingestion.mapping import extract_customer_name, create_chat_mapping
from src.ingestion.media_organizer import organize_media_files
from src.parser import parse_whatsapp_chats

SAMPLE_CHAT_1 = '''15/08/23 10.15 - Zahir Surabaya: Selamat pagi bapak/ibu
15/08/23 10.16 - PT ABC: Pagi admin, mau tanya cara registrasi lisensi dongle Zahir
15/08/23 10.17 - Zahir Surabaya: Baik pak, mohon infokan nomor seri dongle
15/08/23 10.18 - PT ABC: IMG-20230815-WA0001.jpg (file terlampir)
'''

SAMPLE_CHAT_2 = '''15/08/23 11.00 - Zahir Surabaya: Halo dengan CV Eterna Eka?
15/08/23 11.02 - CV Eterna Eka: Iya mas, database firebird corrupt tidak bisa dibuka error
15/08/23 11.05 - Zahir Surabaya: Baik pak kami remote via ultraviewer ID 123456 Pass 123
'''

SAMPLE_NON_CHAT = '''Ini adalah teks biasa tanpa format timestamp WhatsApp.
Tidak ada tanggal dan jam di awal baris.
'''


class TestWhatsAppIngestion(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_zip(self, files_dict, zip_filename="test.zip"):
        zip_path = self.tmp_path / zip_filename
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for name, content in files_dict.items():
                if isinstance(content, bytes):
                    zf.writestr(name, content)
                else:
                    zf.writestr(name, content.encode('utf-8'))
        return zip_path

    def test_1_valid_zip_single_chat(self):
        """1. Valid ZIP dengan satu chat."""
        zip_path = self._create_zip({"WhatsApp Chat dengan PT ABC.txt": SAMPLE_CHAT_1})
        target_dir = self.tmp_path / "raw_target"
        
        result = ingest_whatsapp_zip(zip_path, target_dir=target_dir)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_chats"], 1)
        self.assertTrue((target_dir / "chat" / "chat_1.txt").exists())

    def test_2_valid_zip_multiple_chats(self):
        """2. Valid ZIP dengan beberapa chat."""
        zip_path = self._create_zip({
            "Chat PT ABC.txt": SAMPLE_CHAT_1,
            "Chat CV Eterna.txt": SAMPLE_CHAT_2
        })
        target_dir = self.tmp_path / "raw_target"

        result = ingest_whatsapp_zip(zip_path, target_dir=target_dir)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_chats"], 2)
        self.assertTrue((target_dir / "chat" / "chat_1.txt").exists())
        self.assertTrue((target_dir / "chat" / "chat_2.txt").exists())

    def test_3_zip_with_chat_and_media(self):
        """3. ZIP dengan chat + media."""
        zip_path = self._create_zip({
            "WhatsApp Chat dengan PT ABC.txt": SAMPLE_CHAT_1,
            "IMG-20230815-WA0001.jpg": b"fake_image_bytes"
        })
        target_dir = self.tmp_path / "raw_target"

        result = ingest_whatsapp_zip(zip_path, target_dir=target_dir)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_media"], 1)
        self.assertTrue((target_dir / "media" / "chat_1" / "IMG-20230815-WA0001.jpg").exists())

    def test_4_empty_zip(self):
        """4. Empty ZIP."""
        zip_path = self.tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            pass

        with self.assertRaises(ZipValidationError):
            validate_zip_file(zip_path)

    def test_5_corrupt_zip(self):
        """5. Corrupt ZIP."""
        corrupt_path = self.tmp_path / "corrupt.zip"
        corrupt_path.write_bytes(b"THIS IS NOT A VALID ZIP FILE HEADER")

        with self.assertRaises(ZipValidationError):
            validate_zip_file(corrupt_path)

    def test_6_invalid_zip_path(self):
        """6. Invalid ZIP path."""
        non_existent = self.tmp_path / "does_not_exist.zip"

        with self.assertRaises(ZipValidationError):
            validate_zip_file(non_existent)

    def test_7_path_traversal_zip(self):
        """7. Path traversal ZIP."""
        zip_path = self.tmp_path / "traversal.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("../../evil.txt", "evil content")

        with self.assertRaises(ZipValidationError):
            validate_zip_file(zip_path)

    def test_8_empty_txt(self):
        """8. Empty TXT."""
        zip_path = self._create_zip({
            "empty_chat.txt": "   \n  \n  ",
            "valid_chat.txt": SAMPLE_CHAT_1
        })
        target_dir = self.tmp_path / "raw_target"

        result = ingest_whatsapp_zip(zip_path, target_dir=target_dir)

        self.assertEqual(result["total_chats"], 1)
        self.assertEqual(result["chat_files"], ["chat_1.txt"])

    def test_9_duplicate_source_filenames(self):
        """9. Duplicate source filenames."""
        zip_path = self._create_zip({
            "folder1/WhatsApp Chat.txt": SAMPLE_CHAT_1,
            "folder2/WhatsApp Chat.txt": SAMPLE_CHAT_2
        })
        target_dir = self.tmp_path / "raw_target"

        result = ingest_whatsapp_zip(zip_path, target_dir=target_dir)

        self.assertEqual(result["total_chats"], 2)
        mapping_file = Path(result["mapping_file"])
        with open(mapping_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        self.assertIn("chat_1.txt", mapping)
        self.assertIn("chat_2.txt", mapping)
        self.assertNotEqual(mapping["chat_1.txt"]["source_filename"], mapping["chat_2.txt"]["source_filename"])

    def test_10_unresolved_media(self):
        """10. Unresolved media."""
        zip_path = self._create_zip({
            "folder1/Chat PT ABC.txt": SAMPLE_CHAT_1,
            "folder2/Chat CV Eterna.txt": SAMPLE_CHAT_2,
            "random_orphan_image.png": b"fake_bytes"
        })
        target_dir = self.tmp_path / "raw_target"

        result = ingest_whatsapp_zip(zip_path, target_dir=target_dir)

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["unresolved_files"]), 1)
        self.assertEqual(result["unresolved_files"][0]["filename"], "random_orphan_image.png")
        self.assertTrue((target_dir / "media" / "unresolved" / "random_orphan_image.png").exists())

    def test_11_mapping_customer_source(self):
        """11. Mapping customer/source."""
        zip_path = self._create_zip({
            "WhatsApp Chat dengan PT ABC.txt": SAMPLE_CHAT_1,
            "WhatsApp Chat.txt": SAMPLE_CHAT_2
        })
        target_dir = self.tmp_path / "raw_target"

        result = ingest_whatsapp_zip(zip_path, target_dir=target_dir)

        mapping_file = Path(result["mapping_file"])
        with open(mapping_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        self.assertEqual(mapping["chat_1.txt"]["customer_name"], "PT ABC")
        self.assertIsNone(mapping["chat_2.txt"]["customer_name"])

    def test_12_session_isolation_and_existing_nlp_compatibility(self):
        """12. Session isolation and backward compatibility with existing NLP pipeline."""
        target_dir1 = self.tmp_path / "session_1" / "raw"
        target_dir2 = self.tmp_path / "session_2" / "raw"

        zip1 = self._create_zip({"Chat PT ABC.txt": SAMPLE_CHAT_1}, zip_filename="session1.zip")
        zip2 = self._create_zip({"Chat CV Eterna.txt": SAMPLE_CHAT_2}, zip_filename="session2.zip")

        res1 = ingest_whatsapp_zip(zip1, target_dir=target_dir1, session_id="sess_1")
        res2 = ingest_whatsapp_zip(zip2, target_dir=target_dir2, session_id="sess_2")

        self.assertEqual(res1["session_id"], "sess_1")
        self.assertEqual(res2["session_id"], "sess_2")
        self.assertTrue((target_dir1 / "chat" / "chat_1.txt").exists())
        self.assertTrue((target_dir2 / "chat" / "chat_1.txt").exists())

        messages = parse_whatsapp_chats(
            raw_dir=target_dir1 / "chat",
            media_dir=target_dir1 / "media",
            output_file=target_dir1 / "chat_parsed.csv"
        )
        self.assertGreater(len(messages), 0)
        self.assertTrue((target_dir1 / "chat_parsed.csv").exists())


if __name__ == "__main__":
    unittest.main()
