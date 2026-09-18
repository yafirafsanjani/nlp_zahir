"""
llm_labeling.py - Modul LLM Labeling (Fase Ekspansi LLM 2/5)

Membaca chat_with_categories.csv, menggabungkan pesan CLIENT (sebagai keluhan)
dan seluruh pesan (sebagai konteks) per sub_conversation_id, menetapkan
kategori_kendala dengan bantuan model AI (OpenAI / Gemini / Mock dry-run)
berdasarkan definisi taksonomi di config/taxonomy.json, lalu menyimpan hasil ke
data/processed/llm_labels.csv.

Kontrak JSON LLM: {"label", "main_issue", "reason", "confidence",
"perlu_kategori_baru", "usulan_kategori"}.

Cara pakai:
    python src/llm_labeling.py                # real (butuh LLM_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY)
    python src/llm_labeling.py --dry-run      # simulasi tanpa API (pakai regex)
    python src/llm_labeling.py --provider gemini --dry-run

Prinsip: LLM hanya dipakai untuk membentuk ground truth, TIDAK pernah di jalur
prediksi harian (Fase 17 tetap murni model ML).
"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from collections import Counter

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.taxonomy import (
    load_taxonomy,
    build_category_patterns,
    detect_category,
    get_fallback_category,
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INPUT_FILE = PROCESSED_DIR / "chat_with_categories.csv"
OUTPUT_FILE = PROCESSED_DIR / "llm_labels.csv"

CONFIDENCE_LOW = 0.6          # confidence di bawah ini -> kandidat reconciliation
MAX_TEXT_CHARS = 2000         # teks keluhan dipotong agar muat konteks model

# Definisi sistem untuk seluruh provider
SYSTEM_INSTRUCTIONS = (
    "Kamu adalah analis labeling data untuk layanan customer support software "
    "akuntansi Zahir.\n\n"
    "TUGAS: tentukan SATU kategori kendala dari percakapan klien, berdasar pada "
    "INTI MASALAH UTAMA yang sedang dihadapi customer.\n\n"
    "PRINSIP KLASIFIKASI:\n"
    "1. Perhatikan SELURUH percakapan (keluhan klien + konteks tindakan admin). "
    "Label ditentukan dari masalah utama customer, bukan dari banyaknya kata kunci "
    "dan bukan dari solusi terakhir yang diberikan admin.\n"
    "2. Beda antara PERTANYAAN UMUM dan MASALAH/TROUBLESHOOTING:\n"
    "   - PERTANYAAN_UMUM_FITUR HANYA jika customer menanyakan cara/fungsi/menu/"
    "panduan dan TIDAK ada masalah yang sedang ditangani (tidak gagal, tidak error, "
    "tidak 'tidak bisa').\n"
    "   - Jika ada masalah aktif (tidak bisa, error, gagal, loading, gantung, "
    "tidak terhubung), pilih kategori sesuai INTI masalahnya:\n"
    "     * masalah koneksi/instalasi/jaringan (IP, LAN, firewall, client-server, "
    "server/client) -> INSTALASI_SETUP_NETWORK\n"
    "     * kerusakan/error database itu sendiri (corrupt, engine error, tidak bisa "
    "dibuka karena rusak) -> DATABASE_SYSTEM_ERROR\n"
    "     * keluhan lain -> kategori yang sesuai atau LAINNYA_UNCATEGORIZED.\n"
    "3. Kehadiran kata IP/server/firewall/database SAJA tidak menentukan kategori — "
    "yang menentukan adalah APAKAH ada masalah yang sedang ditangani dan apa intinya.\n"
    "4. Percakapan multi-masalah: pilih SATU kendala yang PALING UTAMA (yang "
    "mendominasi dan menjadi tujuan bantuan admin).\n"
    "5. Jangan mengarang kategori di luar daftar. Bila benar-benar tidak ada yang "
    "cocok, gunakan LAINNYA_UNCATEGORIZED dan set perlu_kategori_baru=true beserta "
    "usulan_kategori.\n\n"
    "FORMAT JAWABAN: jawab HANYA dengan SATU objek JSON valid, tanpa teks lain, "
    "tanpa komentar, dengan format persis berikut:\n"
    '{"label": "<nama_kategori>", "main_issue": "<inti masalah customer dalam 1 kalimat>", '
    '"reason": "<alasan singkat mengapa label ini dipilih, jelaskan masalah utamanya, '
    'JANGAN hanya mengulang keyword>", '
    '"confidence": <0-1 float>, '
    '"perlu_kategori_baru": <true/false>, '
    '"usulan_kategori": <null atau string nama kategori baru>}\n'
    "Aturan field:\n"
    "- label = salah satu dari daftar kategori yang diberikan.\n"
    "- main_issue = ringkasan MASALAH UTAMA customer (mis. 'client tidak bisa "
    "terhubung ke server meskipun IP sudah diganti').\n"
    "- reason = penjelasan logis kenapa label dipilih (bandingkan dengan definisi "
    "kategori), bukan kutipan ulang kata kunci.\n"
    "- confidence = seberapa yakin kamu (0 s.d. 1).\n"
    "- perlu_kategori_baru diisi true bila topik kendala jelas BUKAN termasuk semua "
    "kategori yang ada.\n"
)

# Contoh few-shot per kategori (termasuk contoh pembeda tanya vs troubleshooting)
FEW_SHOT_EXAMPLES = [
    (
        "keluhan: pak database error firebird corrupt pas buka aplikasi, tiba tiba "
        "aplikasi keluar sendiri",
        {
            "label": "DATABASE_SYSTEM_ERROR",
            "main_issue": "database corrupt sehingga aplikasi tidak bisa dibuka.",
            "reason": "Kerusakan database itu sendiri (corrupt, engine Firebird) menyebabkan aplikasi keluar sendiri — masuk kategori error database.",
            "confidence": 0.95,
            "perlu_kategori_baru": False,
            "usulan_kategori": None,
        },
    ),
    (
        "keluhan: dongle saya tidak terbaca pak, lisensi jadi unregistered, minta "
        "kode aktivasi ulang",
        {
            "label": "LISENSI_DONGLE_REGISTRASI",
            "main_issue": "dongle tidak terbaca sehingga aplikasi unregistered.",
            "reason": "Inti masalah adalah perangkat lisensi/dongle dan registrasi aktivasi ulang.",
            "confidence": 0.95,
            "perlu_kategori_baru": False,
            "usulan_kategori": None,
        },
    ),
    (
        "keluhan: ip sudah saya ganti tapi tetap tidak bisa, waktu ganti ip di-ok "
        "kemudian loading lama, setelah firewall dinonaktifkan baru bisa",
        {
            "label": "INSTALASI_SETUP_NETWORK",
            "main_issue": "komputer client tidak bisa terhubung ke server meskipun IP sudah diganti.",
            "reason": "Inti masalah adalah koneksi jaringan client-server yang sedang ditangani (ganti IP, loading, firewall menghalangi), bukan pertanyaan penggunaan.",
            "confidence": 0.95,
            "perlu_kategori_baru": False,
            "usulan_kategori": None,
        },
    ),
    (
        "keluhan: pak, apa itu ip address? apakah berpengaruh ke koneksi zahir "
        "client server?",
        {
            "label": "PERTANYAAN_UMUM_FITUR",
            "main_issue": "customer ingin memahami konsep IP address.",
            "reason": "Tidak ada masalah yang ditangani, hanya pertanyaan penjelasan konsep — meskipun memuat kata 'ip address'.",
            "confidence": 0.85,
            "perlu_kategori_baru": False,
            "usulan_kategori": None,
        },
    ),
    (
        "keluhan: pak saya mau tanya, gimana cara setting ip komputer biar bisa "
        "konek (belum dicoba, hanya ingin panduan)",
        {
            "label": "PERTANYAAN_UMUM_FITUR",
            "main_issue": "customer ingin panduan setting IP, belum ada masalah gagal.",
            "reason": "Permintaan panduan tanpa kendala yang sedang dialami — tetap pertanyaan umum soal cara penggunaan.",
            "confidence": 0.8,
            "perlu_kategori_baru": False,
            "usulan_kategori": None,
        },
    ),
    (
        "keluhan: laporan laba rugi tidak seimbang pak, waktu cetak pdf malah "
        "menggantung",
        {
            "label": "LAPORAN_REPORTING",
            "main_issue": "laporan laba rugi tidak seimbang dan menggantung saat dicetak.",
            "reason": "Masalah berpusat pada output laporan (cetak pdf), bukan database atau jaringan.",
            "confidence": 0.9,
            "perlu_kategori_baru": False,
            "usulan_kategori": None,
        },
    ),
    (
        "keluhan: input faktur penjualan tapi stok tidak terpotong otomatis, "
        "saldo jadi selisih",
        {
            "label": "TRANSAKSI_INPUT_DATA",
            "main_issue": "stok tidak terpotong otomatis saat input faktur penjualan.",
            "reason": "Masalah terjadi pada penginputan transaksi dan saldo, bukan pada infrastruktur.",
            "confidence": 0.95,
            "perlu_kategori_baru": False,
            "usulan_kategori": None,
        },
    ),
    (
        "keluhan: client tidak bisa konek ke server padahal database server "
        "normal, udah ganti ip tetep ga bisa, admin cek firewall baru ketemu",
        {
            "label": "INSTALASI_SETUP_NETWORK",
            "main_issue": "client tidak bisa konek ke server karena firewall, database normal.",
            "reason": "Koneksi jaringan yang bermasalah (bukan database), terbukti firewall penyebabnya — masuk masalah network.",
            "confidence": 0.95,
            "perlu_kategori_baru": False,
            "usulan_kategori": None,
        },
    ),
    (
        "keluhan: selamat pagi pak, makasih banyak bantuannya hari ini, salam "
        "sukses untuk zahir",
        {
            "label": "LAINNYA_UNCATEGORIZED",
            "main_issue": "tidak ada keluhan teknis, hanya ucapan terima kasih.",
            "reason": "Percakapan tidak berisi masalah teknis apa pun.",
            "confidence": 0.8,
            "perlu_kategori_baru": False,
            "usulan_kategori": None,
        },
    ),
]


def load_csv(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _format_taxonomy(taxonomy):
    """Mengubah taksonomi JSON menjadi bagian daftar kategori dalam prompt."""
    lines = []
    for cat in taxonomy.get("categories", []):
        lines.append(f"- {cat['name']}: {cat['definition']}")
    fallback = taxonomy.get("fallback_category", get_fallback_category())
    lines.append(
        f"- {fallback}: digunakan bila keluhan tidak termasuk semua kategori di atas "
        "atau percakapan tidak berisi keluhan teknis sama sekali."
    )
    return "\n".join(lines)


def _format_few_shot():
    parts = []
    for text, label in FEW_SHOT_EXAMPLES:
        parts.append(text)
        parts.append(json.dumps(label, ensure_ascii=False))
    return "\n".join(parts)


def build_labeling_prompt(taxonomy, text, convo=None):
    """Merangkai prompt lengkap: taksonomi + few-shot + percakapan yang dilabeli."""
    prompt = (
        "Daftar kategori yang sah:\n"
        + _format_taxonomy(taxonomy)
        + "\n\nContoh beberapa pasang keluhan-jawaban:\n"
        + _format_few_shot()
        + "\n\nSekarang labeli percakapan berikut (jangan buat analisis, langsung "
        "JAWAB objek JSON sesuai format):\n"
    )
    prompt += "\nKeluhan klien (utama):\n" + (
        text[:MAX_TEXT_CHARS] if text else "(tidak ada teks keluhan)"
    )
    if convo and convo.strip():
        prompt += "\n\nKonteks percakapan (untuk memahami kronologi & tindakan admin; "
        prompt += "label tetap ditentukan dari MASALAH UTAMA klien):\n" + convo.strip()[:MAX_TEXT_CHARS]
    return prompt


# ---------------------------------------------------------------------------
# Provider LLM
# ---------------------------------------------------------------------------
class OpenAIProvider:
    def __init__(self, api_key, model):
        self._api_key = api_key
        self.model = model

    def complete(self, prompt):
        try:
            import openai
        except ImportError:
            sys.exit("[ERROR] Paket 'openai' belum terpasang. Jalankan: pip install openai")
        client = openai.OpenAI(api_key=self._api_key)
        resp = client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""


class GeminiProvider:
    def __init__(self, api_key, model):
        self._api_key = api_key
        self.model = model

    def complete(self, prompt):
        try:
            import google.generativeai as genai
        except ImportError:
            sys.exit(
                "[ERROR] Paket 'google-generativeai' belum terpasang. "
                "Jalankan: pip install google-generativeai"
            )
        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(self.model)
        resp = model.generate_content(
            SYSTEM_INSTRUCTIONS + "\n\n" + prompt,
            generation_config=genai.types.GenerationConfig(temperature=0),
        )
        return resp.text or ""


class MockProvider:
    """Simulasi LLM tanpa API: pakai deteksi regex sebagai pengganti jawaban."""

    def __init__(self):
        self.patterns = build_category_patterns()
        self.fallback = get_fallback_category()

    def complete(self, prompt):
        match = re.search(
            r"Keluhan\s+klien[^\n]*:\s*(.*?)(\n\s*\nKonteks|\Z)",
            prompt,
            re.DOTALL,
        )
        text = match.group(1).strip() if match else ""
        kategori = detect_category(text, self.patterns)
        return json.dumps(
            {
                "label": kategori,
                "main_issue": text[:120] if text else "tidak ada keluhan teknis",
                "reason": "deteksi pola kata (dry-run simulasi regex)",
                "confidence": 0.9,
                "perlu_kategori_baru": False,
                "usulan_kategori": None,
            },
            ensure_ascii=False,
        )


def make_provider(provider=None, dry_run=False):
    if dry_run:
        return MockProvider()

    provider = (provider or os.getenv("LLM_PROVIDER", "openai")).strip().lower()
    if provider in ("openai", "gpt"):
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            sys.exit("[ERROR] setenv OPENAI_API_KEY atau gunakan --dry-run untuk simulasi.")
        return OpenAIProvider(api_key, os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    if provider in ("gemini", "google", "gemini-google"):
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            sys.exit("[ERROR] setenv GEMINI_API_KEY atau gunakan --dry-run untuk simulasi.")
        return GeminiProvider(api_key, os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    sys.exit(
        f"[ERROR] Provider LLM tidak dikenal: {provider}. "
        "Pilih 'openai' atau 'gemini' (atau gunakan --dry-run)."
    )


# ---------------------------------------------------------------------------
# Parsing & validasi respons LLM
# ---------------------------------------------------------------------------
def extract_json(text):
    """Mengambil objek JSON pertama dari teks jawaban model secara toleran."""
    if not text:
        return None
    text = text.strip()
    # buang bungkus markdown code fence (kalau ada)
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    candidate = text[start:end + 1]

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # percobaan toleran: hapus trailing comma
    cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def normalize_label_response(obj, allowed_categories):
    """
    Memastikan respons sesuai kontrak struktur {label, main_issue, reason,
    confidence, perlu_kategori_baru, usulan_kategori}. 'kategori' lama tetap
    diterima agar kompatibel ke bawah. Kategori di luar daftar sah dipaksa ke
    fallback dan ditandai perlu_kategori_baru=True (untuk ditangani Fase 3).
    """
    fallback = get_fallback_category()
    if not isinstance(obj, dict):
        return {
            "kategori": fallback,
            "confidence": 0.0,
            "evidence": None,
            "reason": None,
            "main_issue": None,
            "perlu_kategori_baru": False,
            "usulan_kategori": None,
        }

    kategori = str(obj.get("label") or obj.get("kategori") or "").strip()
    perlu_baru = bool(obj.get("perlu_kategori_baru", False))

    if kategori in allowed_categories:
        if perlu_baru:
            usulan = str(obj.get("usulan_kategori") or "").strip() or kategori
        else:
            usulan = str(obj.get("usulan_kategori") or "").strip() or None
            if usulan:
                perlu_baru = True
    else:
        # kategori asing -> jadikan usulan, label dipaksa ke fallback
        usulan = kategori or str(obj.get("usulan_kategori") or "").strip() or None
        kategori = fallback
        perlu_baru = True

    try:
        confidence = float(obj.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    reason = str(obj.get("reason") or "").strip() or None
    main_issue = str(obj.get("main_issue") or "").strip() or None
    evidence = (
        str(obj.get("evidence") or "").strip()
        or main_issue
        or (reason[:120] if reason else None)
    )

    return {
        "kategori": kategori,
        "confidence": confidence,
        "evidence": evidence,
        "reason": reason,
        "main_issue": main_issue,
        "perlu_kategori_baru": perlu_baru,
        "usulan_kategori": usulan,
    }


# ---------------------------------------------------------------------------
# Agregasi & alur utama
# ---------------------------------------------------------------------------
def aggregate_by_subconversation(rows):
    """Menggabungkan teks CLIENT dan konteks percakapan per sub_conversation_id."""
    grouped = {}
    for r in rows:
        sid = r["sub_conversation_id"]
        if sid not in grouped:
            grouped[sid] = {
                "client_texts": [],
                "convo_lines": [],
                "regex_category": r.get("kategori_kendala", ""),
                "msg_count": 0,
            }
        grouped[sid]["msg_count"] += 1
        role = r.get("role", "")
        text = (r.get("percakapan") or "").strip()
        if not text:
            continue
        if role == "CLIENT":
            grouped[sid]["client_texts"].append(text)
        grouped[sid]["convo_lines"].append(f"({role}) {text}")

    docs = []
    for sid, info in grouped.items():
        docs.append(
            {
                "sub_conversation_id": sid,
                "client_text": " ".join(info["client_texts"]).strip(),
                "convo_text": "\n".join(info["convo_lines"]).strip(),
                "regex_category": info["regex_category"],
                "msg_count": info["msg_count"],
            }
        )
    return docs


def run(provider=None, dry_run=False):
    if not INPUT_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {INPUT_FILE}")
        print("Jalankan fase 9 (labeling) terlebih dahulu: python main.py label")
        return

    taxonomy = load_taxonomy()
    allowed = set(cat["name"] for cat in taxonomy.get("categories", []))
    allowed.add(taxonomy.get("fallback_category", get_fallback_category()))
    fallback = get_fallback_category()

    llm = make_provider(provider, dry_run)

    print("=" * 60)
    print("  FASE EKSPANSI LLM 2/5 — LLM LABELING")
    mode = "DRY-RUN (simulasi regex, tanpa API)" if dry_run else \
        f"REAL ({getattr(llm, 'model', provider or os.getenv('LLM_PROVIDER', 'openai'))})"
    print(f"  Mode    : {mode}")
    print(f"  Input   : {INPUT_FILE}")
    print(f"  Output  : {OUTPUT_FILE}")
    print("=" * 60)

    data = load_csv(INPUT_FILE)
    docs = aggregate_by_subconversation(data)
    print(f"\nTotal sub-conversation yang akan dilabeli: {len(docs)}")

    results = []
    n_fail = 0
    for i, doc in enumerate(docs, 1):
        prompt = build_labeling_prompt(taxonomy, doc["client_text"], doc["convo_text"])
        try:
            raw = llm.complete(prompt)
            label = normalize_label_response(extract_json(raw), allowed)
        except Exception as exc:  # satu gagal tidak mematikan seluruh proses
            n_fail += 1
            label = {
                "kategori": fallback,
                "confidence": 0.0,
                "evidence": None,
                "reason": None,
                "main_issue": None,
                "perlu_kategori_baru": False,
                "usulan_kategori": None,
            }
            print(f"  [WARN] sub {doc['sub_conversation_id']} gagal: {exc}")

        agree = label["kategori"] == doc["regex_category"]
        flag_recon = (
            label["perlu_kategori_baru"]
            or label["confidence"] < CONFIDENCE_LOW
            or label["kategori"] == fallback
        )

        results.append(
            {
                "sub_conversation_id": doc["sub_conversation_id"],
                "msg_count": doc["msg_count"],
                "client_text": doc["client_text"],
                "kategori_llm": label["kategori"],
                "confidence": f"{label['confidence']:.2f}",
                "reason": label["reason"] or "",
                "main_issue": label["main_issue"] or "",
                "evidence": label["evidence"] or "",
                "perlu_kategori_baru": "TRUE" if label["perlu_kategori_baru"] else "FALSE",
                "usulan_kategori": label["usulan_kategori"] or "",
                "kategori_regex": doc["regex_category"],
                "agree": "TRUE" if agree else "FALSE",
                "flag_recon": "TRUE" if flag_recon else "FALSE",
            }
        )
        if i % 10 == 0 or i == len(docs):
            print(f"  ... {i}/{len(docs)} sub-conversation selesai")

    # ---- simpan CSV
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sub_conversation_id", "msg_count", "client_text", "kategori_llm",
        "confidence", "reason", "main_issue", "evidence",
        "perlu_kategori_baru", "usulan_kategori",
        "kategori_regex", "agree", "flag_recon",
    ]
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # ---- ringkasan
    print(f"\n=== RINGKASAN LLM LABELING ===")
    print(f"Total dilabeli    : {len(results)} sub-conversation")
    print(f"Gagal dipanggil AI : {n_fail}")

    cat_counter = Counter(r["kategori_llm"] for r in results)
    print("\nSEBARAN KATEGORI LLM:")
    for cat, count in cat_counter.most_common():
        print(f"  - {cat:<30}: {count} ({count / len(results) * 100:.1f}%)")

    agree_n = sum(1 for r in results if r["agree"] == "TRUE")
    print(f"\nKESESUAIAN DENGAN REGEX (agree): {agree_n}/{len(results)} "
          f"({agree_n / len(results) * 100:.1f}%)")

    recon = [r for r in results if r["flag_recon"] == "TRUE"]
    print(f"KANDIDAT RECONCILIATION (Fase 3): {len(recon)} sub-conversation "
          "(confidence rendah / perlu kategori baru / fallback)")

    print(f"\nHasil disimpan ke: {OUTPUT_FILE}")
    print("=" * 60)
    print("  FASE LLM-L SELESAI — LANJUT KE FASE 3 (RECONCILIATION)")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Labeling kategori kendala Zahir")
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER", "openai"),
                        help="openai | gemini (atau via env LLM_PROVIDER)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulasi tanpa API (pakai deteksi regex)")
    args = parser.parse_args()
    run(provider=args.provider, dry_run=args.dry_run)