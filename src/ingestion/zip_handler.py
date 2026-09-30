# zip_handler.py - Main Entry Point Ingestion ZIP WhatsApp Export

import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
import zipfile

from src.ingestion.validator import validate_zip_file, is_safe_zip_member, ZipValidationError
from src.ingestion.chat_detector import detect_chat_files
from src.ingestion.mapping import create_chat_mapping
from src.ingestion.media_organizer import organize_media_files


def ingest_whatsapp_zip(
    zip_path: str | Path,
    target_dir: str | Path | None = None,
    session_id: str | None = None,
    clean_target: bool = False
) -> dict:
    zip_p = Path(zip_path).resolve()
    
    validate_zip_file(zip_p)

    if session_id is None:
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        short_id = uuid.uuid4().hex[:6]
        session_id = 'session_%s_%s' % (timestamp_str, short_id)

    if target_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent
        target_path = base_dir / 'data' / 'raw'
    else:
        target_path = Path(target_dir).resolve()

    chat_target_dir = target_path / 'chat'
    media_target_dir = target_path / 'media'
    
    chat_target_dir.mkdir(parents=True, exist_ok=True)
    media_target_dir.mkdir(parents=True, exist_ok=True)

    warnings = []

    with tempfile.TemporaryDirectory(prefix='wa_ingest_') as tmp_dir:
        tmp_path = Path(tmp_dir).resolve()

        with zipfile.ZipFile(zip_p, 'r') as zf:
            for member in zf.infolist():
                if not is_safe_zip_member(member.filename):
                    raise ZipValidationError('Terdeteksi potensi serangan path traversal pada member ZIP: %s' % member.filename)
                target_file_path = (tmp_path / member.filename).resolve()
                if not str(target_file_path).startswith(str(tmp_path)):
                    raise ZipValidationError('Terdeteksi path traversal di luar target directory: %s' % member.filename)
                zf.extract(member, tmp_path)

        detected_chats = detect_chat_files(tmp_path)

        if not detected_chats:
            warnings.append('Tidak ditemukan file percakapan WhatsApp (.txt) yang valid dalam ZIP.')
            session_metadata = {
                'status': 'warning',
                'session_id': session_id,
                'target_dir': str(target_path),
                'total_chats': 0,
                'total_media': 0,
                'chat_files': [],
                'media_files': {},
                'mapping_file': str(chat_target_dir / 'chat_mapping.json'),
                'unresolved_files': [],
                'warnings': warnings,
                'timestamp': datetime.now().isoformat()
            }
            return session_metadata

        if clean_target:
            for old_txt in chat_target_dir.glob('chat_*.txt'):
                try:
                    old_txt.unlink()
                except Exception:
                    pass
            for item in media_target_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
            start_idx = 1
            chat_mapping = {}
        else:
            existing_indices = []
            for p in chat_target_dir.glob('chat_*.txt'):
                m = re.match(r'^chat_(\d+)\.txt$', p.name, re.IGNORECASE)
                if m:
                    existing_indices.append(int(m.group(1)))
            start_idx = (max(existing_indices) + 1) if existing_indices else 1

            chat_mapping = {}
            existing_mapping_file = chat_target_dir / 'chat_mapping.json'
            if existing_mapping_file.exists():
                try:
                    with open(existing_mapping_file, 'r', encoding='utf-8') as f:
                        chat_mapping = json.load(f)
                except Exception:
                    chat_mapping = {}

        chat_identifiers = ['chat_%d.txt' % (start_idx + i) for i in range(len(detected_chats))]
        chat_names = ['chat_%d' % (start_idx + i) for i in range(len(detected_chats))]

        new_mapping = create_chat_mapping(detected_chats, chat_identifiers)
        chat_mapping.update(new_mapping)

        assigned_media, unresolved_list = organize_media_files(tmp_path, detected_chats, chat_names)

        copied_chat_files = []
        for i, chat_info in enumerate(detected_chats):
            dest_file_name = chat_identifiers[i]
            dest_file_path = chat_target_dir / dest_file_name
            with open(dest_file_path, 'w', encoding='utf-8') as out_f:
                out_f.write(chat_info['content'])
            copied_chat_files.append(dest_file_name)

        mapping_path = chat_target_dir / 'chat_mapping.json'
        with open(mapping_path, 'w', encoding='utf-8') as mf:
            json.dump(chat_mapping, mf, indent=4, ensure_ascii=False)

        copied_media_map = {}
        total_media_count = 0

        for chat_name, media_paths in assigned_media.items():
            dest_folder = media_target_dir / chat_name
            dest_folder.mkdir(parents=True, exist_ok=True)
            copied_media_map[chat_name] = []

            for m_path in media_paths:
                dest_m_path = dest_folder / m_path.name
                shutil.copy2(m_path, dest_m_path)
                copied_media_map[chat_name].append(m_path.name)
                total_media_count += 1

        unresolved_info = []
        if unresolved_list:
            unresolved_dir = media_target_dir / 'unresolved'
            unresolved_dir.mkdir(parents=True, exist_ok=True)
            for u in unresolved_list:
                m_path = u['file_path']
                dest_m_path = unresolved_dir / m_path.name
                shutil.copy2(m_path, dest_m_path)
                total_media_count += 1
                unresolved_info.append({
                    'filename': u['filename'],
                    'reason': u['reason']
                })

        session_info = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'source_zip': zip_p.name,
            'total_chats': len(copied_chat_files),
            'total_media': total_media_count,
            'chat_files': copied_chat_files,
            'media_files': copied_media_map,
            'unresolved_files': unresolved_info,
            'warnings': warnings
        }
        
        session_path = chat_target_dir / 'ingestion_session.json'
        with open(session_path, 'w', encoding='utf-8') as sf:
            json.dump(session_info, sf, indent=4, ensure_ascii=False)

        return {
            'status': 'success',
            'session_id': session_id,
            'target_dir': str(target_path),
            'total_chats': len(copied_chat_files),
            'total_media': total_media_count,
            'chat_files': copied_chat_files,
            'media_files': copied_media_map,
            'mapping_file': str(mapping_path),
            'unresolved_files': unresolved_info,
            'warnings': warnings
        }
