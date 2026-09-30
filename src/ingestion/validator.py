# validator.py - Validasi Keamanan dan Integritas File ZIP Export WhatsApp

import os
import zipfile
from pathlib import Path


class ZipValidationError(ValueError):
    pass


def is_safe_zip_member(member_name: str) -> bool:
    if not member_name:
        return True
    
    clean_name = member_name.replace('\\', '/')
    
    if clean_name.startswith('/'):
        return False
    
    if ':' in clean_name:
        return False
    
    parts = Path(clean_name).parts
    if '..' in parts:
        return False
        
    return True


def validate_zip_file(
    zip_path: str | Path,
    max_size_bytes: int = 100 * 1024 * 1024,
    max_uncompressed_bytes: int = 500 * 1024 * 1024
):
    path = Path(zip_path)
    
    if not path.exists():
        raise ZipValidationError('File ZIP tidak ditemukan: %s' % path)
        
    if not path.is_file():
        raise ZipValidationError('Path bukan merupakan file: %s' % path)
        
    if path.suffix.lower() != '.zip':
        raise ZipValidationError('Ekstensi file harus .zip, diterima: %s' % path.suffix)
        
    file_size = path.stat().st_size
    if file_size > max_size_bytes:
        limit_mb = max_size_bytes / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise ZipValidationError(
            'Ukuran file ZIP (%.2f MB) melebihi batas aman (%.2f MB)' % (actual_mb, limit_mb)
        )
        
    if not zipfile.is_zipfile(path):
        raise ZipValidationError('File bukan merupakan arsip ZIP yang valid: %s' % path.name)
        
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            namelist = zf.namelist()
            if not namelist:
                raise ZipValidationError('Arsip ZIP kosong (tidak ada file): %s' % path.name)
             
            bad_file = zf.testzip()
            if bad_file is not None:
                raise ZipValidationError('Arsip ZIP terkorupsi (file bermasalah: %s)' % bad_file)
                
            total_uncompressed = 0
            has_files = False
            for info in zf.infolist():
                if not is_safe_zip_member(info.filename):
                    raise ZipValidationError(
                        'Terdeteksi potensi serangan path traversal pada member ZIP: %s' % info.filename
                    )
                if not info.is_dir():
                    has_files = True
                total_uncompressed += info.file_size
                
            if not has_files:
                raise ZipValidationError('Arsip ZIP kosong (hanya berisi direktori): %s' % path.name)

            if total_uncompressed > max_uncompressed_bytes:
                limit_unc_mb = max_uncompressed_bytes / (1024 * 1024)
                actual_unc_mb = total_uncompressed / (1024 * 1024)
                raise ZipValidationError(
                    'Total ukuran uncompressed (%.2f MB) melebihi batas aman (%.2f MB)' % (actual_unc_mb, limit_unc_mb)
                )
    except zipfile.BadZipFile as e:
        raise ZipValidationError('File ZIP tidak dapat dibuka atau terkorupsi: %s' % e)
