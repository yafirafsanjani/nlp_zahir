# __init__.py - ingestion subpackage entry points

from src.ingestion.validator import validate_zip_file, ZipValidationError
from src.ingestion.chat_detector import detect_chat_files, is_whatsapp_chat_content
from src.ingestion.mapping import extract_customer_name, create_chat_mapping
from src.ingestion.media_organizer import organize_media_files, MEDIA_EXTENSIONS
from src.ingestion.zip_handler import ingest_whatsapp_zip

__all__ = [
    'validate_zip_file',
    'ZipValidationError',
    'detect_chat_files',
    'is_whatsapp_chat_content',
    'extract_customer_name',
    'create_chat_mapping',
    'organize_media_files',
    'MEDIA_EXTENSIONS',
    'ingest_whatsapp_zip',
]
