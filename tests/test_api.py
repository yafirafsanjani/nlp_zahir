import io
import json
import zipfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_CHAT_TEXT = '''15/08/23 10.15 - Zahir Surabaya: Selamat pagi bapak/ibu
15/08/23 10.16 - PT ABC: Pagi admin, mau tanya cara registrasi lisensi dongle Zahir
15/08/23 10.17 - Zahir Surabaya: Baik pak, mohon infokan nomor seri dongle
'''


class TestFastAPIBackend(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        import os, shutil, json
        base_dir = Path(__file__).resolve().parent.parent
        chat_dir = base_dir / "data" / "raw" / "chat"
        media_dir = base_dir / "data" / "raw" / "media"
        for i in range(10, 50):
            txt = chat_dir / f"chat_{i}.txt"
            if txt.exists():
                txt.unlink()
            mfolder = media_dir / f"chat_{i}"
            if mfolder.exists():
                shutil.rmtree(mfolder)
        mapping_file = chat_dir / "chat_mapping.json"
        if mapping_file.exists():
            try:
                with open(mapping_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["thats"] = [c for c in data.get("chats", []) if not any(c.get("file_name") == f"chat_{i}.txt" for j in range(10, 50))]
                with open(mapping_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass


    def _create_zip_bytes(self, files_dict):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for name, content in files_dict.items():
                if isinstance(content, bytes):
                    zf.writestr(name, content)
                else:
                    zf.writestr(name, content.encode("utf-8"))
        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    def test_1_health_endpoint(self):
        """1. GET /api/health -> 200 OK"""
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "nlp-zahir-api")
        self.assertEqual(data["version"], "1.0.0")

    def test_2_upload_valid_zip(self):
        """2. POST /api/upload dengan ZIP valid -> 200 OK & session_id"""
        zip_bytes = self._create_zip_bytes({"WhatsApp Chat dengan PT ABC.txt": SAMPLE_CHAT_TEXT})
        files = {"file": ("WhatsApp_Export.zip", zip_bytes, "application/zip")}
        
        response = client.post("/api/upload", files=files)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("session_id", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["total_chats"], 1)

    def test_3_upload_missing_file(self):
        """3. POST /api/upload tanpa file -> 422 Unprocessable Entity / 400 Bad Request"""
        response = client.post("/api/upload")
        self.assertIn(response.status_code, [400, 422])

    def test_4_upload_non_zip_file(self):
        """4. POST /api/upload dengan file bukan ZIP -> 400 Bad Request"""
        files = {"file": ("test.txt", b"plain text content", "text/plain")}
        response = client.post("/api/upload", files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Ekstensi file harus .zip", response.json()["detail"])

    def test_5_upload_corrupt_zip(self):
        """5. POST /api/upload dengan corrupt ZIP -> 400 Bad Request"""
        files = {"file": ("corrupt.zip", b"INVALID ZIP HEADER BYTES", "application/zip")}
        response = client.post("/api/upload", files=files)
        self.assertEqual(response.status_code, 400)

    def test_6_analyze_valid_session(self):
        """6. POST /api/analyze dengan session valid -> 200 OK & completed"""
        # Upload dulu ZIP valid untuk membuat sesi aktif
        zip_bytes = self._create_zip_bytes({"WhatsApp Chat dengan PT ABC.txt": SAMPLE_CHAT_TEXT})
        upload_res = client.post("/api/upload", files={"file": ("export.zip", zip_bytes, "application/zip")})
        session_id = upload_res.json()["session_id"]

        # Panggil endpoint analyze
        response = client.post("/api/analyze", json={"session_id": session_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["session_id"], session_id)
        self.assertEqual(data["status"], "completed")

    def test_7_analyze_invalid_session(self):
        """7. POST /api/analyze dengan session invalid -> 404 Not Found"""
        invalid_session = "session_non_existent_999999"
        response = client.post("/api/analyze", json={"session_id": invalid_session})
        self.assertEqual(response.status_code, 404)

    def test_8_error_handling_no_traceback(self):
        """8. API error handling tidak mengembalikan traceback internal"""
        response = client.post("/api/analyze", json={"session_id": "invalid_session_test"})
        self.assertEqual(response.status_code, 404)
        body = response.text
        self.assertNotIn("Traceback", body)
        self.assertNotIn("File \"", body)


if __name__ == "__main__":
    unittest.main()
