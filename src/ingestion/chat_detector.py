# chat_detector.py - Deteksi dan Validasi File Percakapan WhatsApp (.txt)

import re
from pathlib import Path
from src.parser import MESSAGE_PATTERN, SYSTEM_PATTERN, DATE_START_PATTERN, clean_line

GENERIC_WHATSAPP_TIMESTAMP = re.compile(
    r'^\s*\[?\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}[,\s]+\d{1,2}[:\.]\d{2}'
)


def is_whatsapp_chat_content(content: str) -> bool:
    if not content or not content.strip():
        return False
        
    lines = content.splitlines()
    valid_count = 0
    
    for line in lines:
        cleaned = clean_line(line.rstrip('\r\n'))
        if not cleaned.strip():
            continue
            
        if (
            MESSAGE_PATTERN.match(cleaned)
            or SYSTEM_PATTERN.match(cleaned)
            or DATE_START_PATTERN.match(cleaned)
            or GENERIC_WHATSAPP_TIMESTAMP.match(cleaned)
        ):
            valid_count += 1
            
    return valid_count >= 1


def detect_chat_files(extracted_dir: str | Path) -> list[dict]:
    ext_dir: Path = Path(extracted_dir)
    txt_paths = sorted(ext_dir.rglob('*.txt'))
    
    detected = []
    
    for txt_path in txt_paths:
        content = None
        for enc in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252'):
            try:
                content = txt_path.read_text(encoding=enc)
                break
            except Exception:
                continue
                
        if content is None:
            continue
            
        if is_whatsapp_chat_content(content):
            rel_path = txt_path.relative_to(ext_dir)
            
            lines = content.splitlines()
            msg_count = sum(
                1 for line in lines
                if MESSAGE_PATTERN.match(clean_line(line.rstrip('\r\n')))
                or SYSTEM_PATTERN.match(clean_line(line.rstrip('\r\n')))
                or GENERIC_WHATSAPP_TIMESTAMP.match(clean_line(line.rstrip('\r\n')))
            )
            
            detected.append({
                'file_path': txt_path,
                'rel_path': str(rel_path).replace('\\', '/'),
                'filename': txt_path.name,
                'content': content,
                'message_count': msg_count
            })
            
    detected.sort(key=lambda x: x['rel_path'].lower())
    return detected
