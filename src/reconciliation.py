"""
reconciliation.py - Modul Reconciliation & Auto-Add Kategori (Fase Ekspansi LLM 3/5)

Memproses kandidat bermasalah dari llm_labels.csv (flag_recon=TRUE):
  (1) mengelompokkan keluhan yang sejenis via TF-IDF + connected components,
  (2) meminta AI mengusulkan kategori baru (nama + definisi + keywords + phrases),
  (3) auto-menambahkan ke config/taxonomy.json hanya jika kelompok memenuhi
      threshold minimal anggota (default >= 5),
  (4) sisanya (kelompok kecil / usulan tidak valid / tanpa teks) tetap fallback.

Laporan keputusan disimpan ke data/processed/reconciliation_results.csv,
dan config/taxonomy.json (single source of truth) diperbarui versinya.

Cara pakai:
    python src/reconciliation.py --dry-run
    python src/reconciliation.py --provider gemini --min-samples 5
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

from src.taxonomy import load_taxonomy, get_fallback_category
from src.llm_labeling import extract_json, OpenAIProvider, GeminiProvider

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
LLM_LABELS_FILE = PROCESSED_DIR / "llm_labels.csv"
REPORT_FILE = PROCESSED_DIR / "reconciliation_results.csv"
TAXONOMY_PATH = BASE_DIR / "config" / "taxonomy.json"

MIN_SAMPLES_NEW_CATEGORY = 5   # auto-add hanya jika anggota kelompok >= ini
CLUSTER_THRESHOLD = 0.30       # kemiripan minimum antar dokumen agar sekelompok
NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")

# Artefak WhatsApp/chat yang harus dibuang sebelum klastering agar topik bersih
MEDIA_ARTIFACTS = re.compile(
    r"<media[^>]*>|img-\d+-wa\d+\.\w+|[\w\- ]+\.pdf|https?://\S+|www\S+",
    re.IGNORECASE,
)

STOPWORDS = {
    "yang", "di", "ke", "dari", "ini", "itu", "dan", "atau", "untuk", "dengan",
    "pada", "adalah", "ada", "bisa", "tidak", "gak", "nggak", "nga", "ngga",
    "ya", "sudah", "udah", "mau", "akan", "kalau", "kalo", "jika", "saya",
    "kami", "pak", "bu", "kak", "mas", "mbak", "tolong", "bantu", "mohon",
    "lagi", "biar", "agar", "nya", "sama", "aja", "saja", "terima", "kasih",
    "makasih", "apa", "kenapa", "punya", "cuma", "juga", "sih", "deh",
}

NON_TECHNICAL = {
    "selamat", "pagi", "siang", "sore", "malam", "halo", "hai", "salam",
    "makasih", "terima", "kasih", "tolong", "bantu", "mohon", "baik", "siap",
    "oke", "ok", "iya", "nanti", "kemarin", "besok", "minggu", "senin",
    "selasa", "rabu", "kamis", "jumat", "sabtu",
}


def load_csv(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def select_candidates(rows):
    return [r for r in rows if r.get("flag_recon") == "TRUE"]


def clean_for_cluster(text):
    """Bersihkan artefak media/URL agar klaster fokus pada topik keluhan."""
    t = MEDIA_ARTIFACTS.sub(" ", text)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def cluster_texts(texts, threshold=CLUSTER_THRESHOLD):
    """
    Mengelompokkan teks berdasarkan kemiripan kosinus TF-IDF.
    Dua dokumen dianggap satu kelompok bila kemiripannya >= threshold
    (metode connected components - deterministik, tanpa API).
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    n = len(texts)
    if n == 0:
        return []

    vectorizer = TfidfVectorizer(
        token_pattern=r"(?u)\b[a-z0-9_]+\b",
        ngram_range=(1, 2),
        min_df=1,
        max_features=2000,
    )
    X = vectorizer.fit_transform(texts)
    sim = cosine_similarity(X)

    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i + 1, n):
            if sim[i][j] >= threshold:
                union(i, j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)


# ---------------------------------------------------------------------------
# Provider usulan kategori
# ---------------------------------------------------------------------------
class MockProposalProvider:
    """Simulasi AI tanpa API: usulkan nama dari kata paling sering di kelompok."""

    def complete(self, prompt):
        m = re.search(r"DOKUMEN\s*:?\s*\n(.*)$", prompt, re.DOTALL)
        if not m:
            return json.dumps({"nama_kategori": None})
        block = m.group(1)
        items = re.findall(r"\d+\.\s*(.+)", block)
        tokens = []
        for text in items:
            for w in re.findall(r"(?u)\b[a-z0-9_]+\b", text.lower()):
                if len(w) > 2 and w not in STOPWORDS:
                    tokens.append(w)
        top = [w for w, _ in Counter(tokens).most_common(3)]
        if not top or any(w in NON_TECHNICAL for w in top):
            return json.dumps({"nama_kategori": None})
        name = "_".join(w.upper() for w in top)
        return json.dumps(
            {
                "nama_kategori": name,
                "definition": "Keluhan yang berkaitan dengan " + ", ".join(top) + ".",
                "keywords": top,
                "phrases": [],
            },
            ensure_ascii=False,
        )


def make_proposal_provider(dry_run=False, provider=None):
    if dry_run:
        return MockProposalProvider()

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


def build_proposal_prompt(existing_names, texts):
    lines = [f"{i + 1}. {t}" for i, t in enumerate(texts)]
    return (
        "Daftar kategori yang SUDAH ADA (jangan membuat ulang): "
        + (", ".join(existing_names) if existing_names else "-")
        + "\n\nBerikut kelompok keluhan klien yang dianggap sejenis. Analisis topiknya.\n"
        "Jika kelompok ini membentuk SATU topik teknis baru yang belum tercakup "
        "kategori yang ada, usulkan satu kategori baru.\n"
        "Jika sebenarnya hanya obrolan umum / bukan keluhan teknis / sudah tercakup "
        'kategori yang ada, balas objek: {"nama_kategori": null}.\n'
        "Jawab HANYA satu objek JSON valid tanpa teks lain:\n"
        '{"nama_kategori": "<UPPER_SNAKE>", "definition": "<kalimat definisi>", '
        '"keywords": ["kata", "kunci", "deteksi"], "phrases": ["frasa kunci"]}\n'
        "- nama_kategori: nama singkat UPPER_SNAKE (mis. PEMBACKUPAN_DATA).\n"
        "- definition: penjelasan satu kalimat kapan kategori dipakai.\n"
        "- keywords: 3-8 kata kunci bahasa Indonesia untuk deteksi regex (kata dasar).\n"
        "- phrases: frasa 2-3 kata bila ada, boleh list kosong [].\n\n"
        "DOKUMEN:\n" + "\n".join(lines)
    )


# ---------------------------------------------------------------------------
# Validasi usulan
# ---------------------------------------------------------------------------
def validate_proposal(obj, existing_names):
    """Memastikan usulan kategori valid; None bila menolak / rusak / bentrok."""
    if not isinstance(obj, dict):
        return None
    name = str(obj.get("nama_kategori") or "").strip().upper()
    if not name or name in existing_names or not NAME_RE.match(name):
        return None

    definition = str(obj.get("definition") or "").strip()
    if len(definition) < 10:
        return None

    keywords = []
    for kw in obj.get("keywords") or []:
        kw = re.sub(r"[^a-z0-9_ ]", "", str(kw).strip().lower()).strip()
        if kw and kw not in keywords:
            keywords.append(kw)
    if len(keywords) < 2:
        return None

    phrases = []
    for ph in obj.get("phrases") or []:
        ph = re.sub(r"[^a-z0-9_ ]", "", str(ph).strip().lower()).strip()
        if ph and ph not in phrases:
            phrases.append(ph)

    return {"name": name, "definition": definition, "keywords": keywords, "phrases": phrases}


def add_categories_to_taxonomy(proposals):
    """Menulis kategori baru ke taxonomy.json (auto-add). Kembalikan jumlah yang ditambah."""
    if not proposals:
        return 0
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        tx = json.load(f)
    existing = {c["name"] for c in tx.get("categories", [])}
    added = 0
    for p in proposals:
        if p["name"] in existing:
            continue
        tx.setdefault("categories", []).append(
            {
                "name": p["name"],
                "definition": p["definition"],
                "keywords": p["keywords"],
                "phrases": p.get("phrases", []),
            }
        )
        existing.add(p["name"])
        added += 1
    tx["version"] = int(tx.get("version", 1)) + 1
    with open(TAXONOMY_PATH, "w", encoding="utf-8") as f:
        json.dump(tx, f, ensure_ascii=False, indent=2)
    return added


# ---------------------------------------------------------------------------
# Alur utama
# ---------------------------------------------------------------------------
def run(min_samples=MIN_SAMPLES_NEW_CATEGORY, dry_run=False,
        provider=None, threshold=CLUSTER_THRESHOLD):
    if not LLM_LABELS_FILE.exists():
        print(f"[ERROR] File input tidak ditemukan: {LLM_LABELS_FILE}")
        print("Jalankan fase 2 (LLM Labeling) terlebih dahulu: python src/llm_labeling.py")
        return

    taxonomy = load_taxonomy()
    fallback = taxonomy.get("fallback_category", get_fallback_category())
    existing_names = [c["name"] for c in taxonomy.get("categories", [])] + [fallback]

    print("=" * 60)
    print("  FASE EKSPANSI LLM 3/5 — RECONCILIATION & AUTO-ADD KATEGORI")
    mode = "DRY-RUN (usulan simulasi, tanpa API)" if dry_run else "REAL"
    print(f"  Mode        : {mode}")
    print(f"  Threshold   : >= {min_samples} anggota per kelompok")
    print(f"  Kemiripan   : >= {threshold}")
    print(f"  Input       : {LLM_LABELS_FILE}")
    print("=" * 60)

    rows = load_csv(LLM_LABELS_FILE)
    candidates = select_candidates(rows)
    print(f"\nKandidat reconciliation (flag_recon=TRUE): {len(candidates)}")

    if not candidates:
        print("Tidak ada kandidat. Taksonomi tetap.\n")
        return

    cand_with_text = [c for c in candidates if c["client_text"].strip()]
    n_no_text = len(candidates) - len(cand_with_text)
    print(f"  - dengan teks keluhan   : {len(cand_with_text)}")
    print(f"  - tanpa teks (fallback) : {n_no_text}")

    # bersihkan artefak media/URL; teks yang habis dibersihkan ikut ke fallback
    cleaned = []
    for c in cand_with_text:
        t = clean_for_cluster(c["client_text"])
        if t:
            cleaned.append((c, t))
    n_artifact = len(cand_with_text) - len(cleaned)
    cand = [pair[0] for pair in cleaned]
    texts = [pair[1] for pair in cleaned]
    print(f"  - habis dibersihkan artefak: {n_artifact} (ikut fallback)")

    if not cand:
        print("Tidak ada teks layak diklaster -> tidak ada kategori baru.\n")
        return

    clusters = cluster_texts(texts, threshold)
    big = sum(1 for cl in clusters if len(cl) >= min_samples)
    print(f"Klaster terbentuk       : {len(clusters)} "
          f"({big} layak diproses AI, sisanya < {min_samples} anggota)")

    llm = make_proposal_provider(dry_run=dry_run, provider=provider)

    proposals = []
    report = []
    for idx, cl in enumerate(clusters, 1):
        members = [cand[i] for i in cl]
        member_texts = [texts[i] for i in cl]
        sids = [m["sub_conversation_id"] for m in members]
        contoh = max((m["client_text"] for m in members), key=len)[:150]
        proposed = None
        status, reason = "SKIPPED", ""

        if len(members) >= min_samples:
            prompt = build_proposal_prompt(existing_names, member_texts)
            try:
                raw = llm.complete(prompt)
                obj = extract_json(raw)
                proposed = validate_proposal(obj, existing_names)
            except Exception as exc:
                reason = f"gagal memanggil AI: {exc}"
            if proposed:
                status = "ADDED"
                existing_names = existing_names + [proposed["name"]]
                proposals.append(proposed)
                reason = "memenuhi threshold & usulan valid"
            else:
                reason = reason or "usulan tidak valid / AI menolak / kategori sudah ada"
        else:
            reason = f"anggota {len(members)} < min_samples {min_samples}"

        report.append(
            {
                "cluster_id": idx,
                "n_anggota": len(members),
                "status": status,
                "nama_kategori": proposed["name"] if proposed else "",
                "definition": proposed["definition"] if proposed else "",
                "keywords": ", ".join(proposed["keywords"]) if proposed else "",
                "sub_conversation_ids": "; ".join(sids),
                "contoh_teks": contoh,
                "alasan": reason,
            }
        )
        print(f"  [Klaster {idx}] {len(members)} anggota -> {status}"
              + (f" ({proposed['name']})" if proposed else f" ({reason})"))

    n_fallback_total = n_no_text + n_artifact
    if n_fallback_total:
        report.append(
            {
                "cluster_id": "NO_TEXT",
                "n_anggota": n_fallback_total,
                "status": "SKIPPED",
                "nama_kategori": "",
                "definition": "",
                "keywords": "",
                "sub_conversation_ids": "",
                "contoh_teks": "",
                "alasan": f"{n_fallback_total} kandidat tanpa teks / hanya artefak "
                          f"(dialihkan ke {fallback})",
            }
        )

    # ---- simpan laporan
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "cluster_id", "n_anggota", "status", "nama_kategori", "definition",
        "keywords", "sub_conversation_ids", "contoh_teks", "alasan",
    ]
    with open(REPORT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report)

    # ---- apply ke taksonomi
    n_added = add_categories_to_taxonomy(proposals)

    print(f"\n=== RINGKASAN RECONCILIATION ===")
    print(f"Klaster diproses   : {len(clusters)}")
    print(f"Kategori DITAMBAH  : {n_added}")
    print(f"Klaster SKIPPED    : {sum(1 for r in report if r['status'] == 'SKIPPED')}")
    print(f"Laporan           : {REPORT_FILE}")
    if n_added:
        names = ", ".join(p["name"] for p in proposals)
        print(f"Kategori baru      : {names}")
        print("\n>>> Taksonomi diperbarui. Jalankan 'python main.py label' untuk")
        print("    melabeli ulang sub-percakapan dengan kategori baru tersebut,")
        print("    lalu lanjut pipeline ML (preprocess ->> train).")
    print("=" * 60)
    print("  FASE RECON SELESAI")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconciliation & auto-add kategori")
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER", "openai"),
                        help="openai | gemini (atau via env LLM_PROVIDER)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulasi tanpa API (usulan dari kata dominan klaster)")
    parser.add_argument("--min-samples", type=int, default=MIN_SAMPLES_NEW_CATEGORY,
                        help="Jumlah minimal anggota klaster agar kategori ditambahkan")
    parser.add_argument("--threshold", type=float, default=CLUSTER_THRESHOLD,
                        help="Kemiripan minimal antar dokumen (0-1)")
    args = parser.parse_args()
    run(min_samples=args.min_samples, dry_run=args.dry_run,
        provider=args.provider, threshold=args.threshold)