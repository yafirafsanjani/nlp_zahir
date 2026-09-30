# app/services/analysis_service.py - Orchestration Service Layer

import json
import logging
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from src.ingestion import ingest_whatsapp_zip, ZipValidationError
from src.pipeline import process_conversations
from src.consolidation import consolidate_master_data
from src.export import export_all_reports

import shutil

def save_session_run_artifacts(session_id: str):
    if not session_id or session_id == 'default_session':
        return

    runs_dir = BASE_DIR / 'data' / 'runs' / session_id
    runs_output_dir = runs_dir / 'output'
    runs_chat_dir = runs_dir / 'raw' / 'chat'

    runs_output_dir.mkdir(parents=True, exist_ok=True)
    runs_chat_dir.mkdir(parents=True, exist_ok=True)

    master_src = BASE_DIR / 'data' / 'output' / 'master_conversations_final.csv'
    if master_src.exists():
        shutil.copy2(master_src, runs_output_dir / 'master_conversations_final.csv')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / 'data' / 'raw'

logger = logging.getLogger('nlp_zahir.service')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# The existing NLP stages write intermediate files globally, so runs must not overlap.
ANALYSIS_LOCK = threading.Lock()


def get_active_session_info(session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Dapatkan informasi metadata dari sesi ingestion yang aktif."""
    if session_id:
        # Cek di target_dir default (data/raw)
        session_file = RAW_DIR / 'chat' / 'ingestion_session.json'
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('session_id') == session_id:
                        return data
            except Exception:
                pass
        
        # Cek di folder runs/<session_id>
        runs_file = BASE_DIR / 'data' / 'runs' / session_id / 'raw' / 'chat' / 'ingestion_session.json'
        if runs_file.exists():
            try:
                with open(runs_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return None
    else:
        # Jika session_id None, cek apakah file chat di data/raw/chat/ tersedia
        chat_dir = RAW_DIR / 'chat'
        if chat_dir.exists() and list(chat_dir.glob('chat_*.txt')):
            session_file = chat_dir / 'ingestion_session.json'
            if session_file.exists():
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    pass
            return {'session_id': 'default_session', 'total_chats': len(list(chat_dir.glob('chat_*.txt')))}
        return None


def process_upload_zip(file_name: str, file_bytes: bytes, max_size_mb: int = 100) -> Dict[str, Any]:
    """Memproses upload berkas ZIP WhatsApp menggunakan existing ingestion logic."""
    if not file_name:
        logger.warning('Upload ditolak: Nama file kosong')
        raise ValueError('Berkas upload harus disediakan.')
        
    if not file_name.lower().endswith('.zip'):
        logger.warning(f'Upload ditolak: Ekstensi bukan .zip ({file_name})')
        raise ValueError('Ekstensi file harus .zip')
        
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        logger.warning(f'Upload ditolak: Ukuran file ({file_size_mb:.2f} MB) melebihi batas {max_size_mb} MB')
        raise ValueError(f'Ukuran file ZIP ({file_size_mb:.2f} MB) melebihi batas aman ({max_size_mb} MB)')

    logger.info(f'Memulai ingestion file ZIP: {file_name} ({file_size_mb:.2f} MB)')

    session_id = 'session_%s_%s' % (datetime.now().strftime('%Y%m%d_%H%M%S'), uuid.uuid4().hex[:6])
    session_raw_dir = BASE_DIR / 'data' / 'runs' / session_id / 'raw'

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        # Keep source chats and customer mapping in a session-owned directory.
        result = ingest_whatsapp_zip(tmp_path, target_dir=session_raw_dir, session_id=session_id)
        logger.info(f'Ingestion selesai sukses. Session ID: {result.get("session_id")}, Total Chats: {result.get("total_chats")}')
        return result
    except ZipValidationError as e:
        logger.warning(f'Validasi ZIP gagal: {str(e)}')
        raise ValueError(str(e))
    except Exception as e:
        logger.error(f'Error tidak terduga saat ingestion: {str(e)}')
        raise RuntimeError('Terjadi kesalahan saat memproses file ZIP.')
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def run_analysis_for_session(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Menjalankan pipeline NLP existing terhadap data yang sudah di-ingest."""
    session_info = get_active_session_info(session_id)
    
    if session_id and not session_info:
        logger.warning(f'Analisis gagal: Session ID {session_id} tidak ditemukan.')
        raise KeyError(f'Session ID {session_id} tidak ditemukan.')

    active_session_id = session_info.get('session_id') if session_info else (session_id or 'default_session')
    
    logger.info(f'Memulai eksekusi NLP pipeline untuk Session ID: {active_session_id}')

    try:
        with ANALYSIS_LOCK:
            try:
                if active_session_id == 'default_session':
                    process_conversations(full_tuning=False)
                else:
                    session_raw_dir = BASE_DIR / 'data' / 'runs' / active_session_id / 'raw'
                    process_conversations(
                        raw_dir=session_raw_dir / 'chat',
                        media_dir=session_raw_dir / 'media',
                        full_tuning=False,
                    )
            except ValueError as exc:
                if 'max_df corresponds to < documents than min_df' not in str(exc):
                    raise
                # A one-issue upload cannot fit TF-IDF with min_df=2. Its pre-trained
                # production model can still produce a genuine inference result.
                logger.info('Dataset sesi terlalu kecil untuk retraining; memakai model produksi yang sudah tersedia.')
                consolidate_master_data()
                export_all_reports()
            save_session_run_artifacts(active_session_id)
        logger.info(f'Analisis NLP pipeline selesai sukses untuk Session ID: {active_session_id}')
        return {
            'success': True,
            'session_id': active_session_id,
            'status': 'completed',
            'message': 'Analysis completed successfully'
        }
    except Exception as e:
        logger.error(f'Kesalahan pada pipeline NLP untuk Session ID {active_session_id}: {str(e)}')
        raise RuntimeError(str(e))
