# mapping.py - Pemetaan Nama Customer dan Identifier Chat Export WhatsApp

import re
from pathlib import Path

GENERIC_NAMES = {
    'chat',
    'export',
    'whatsapp chat',
    'obrolan whatsapp',
    'messages',
    'chat_parsed',
    'data',
    'whatsapp_export',
}


def extract_customer_name(source_filename: str) -> str | None:
    if not source_filename:
        return None

    stem = Path(source_filename).stem.strip()
    clean_stem = re.sub(r'\s+', ' ', stem)

    prefix_patterns = [
        r'^(?:WhatsApp\s+Chat|Obrolan\s+WhatsApp|Chat)\s*(?:-|with|dengan)\s*(.+)$',
        r'^(?:WhatsApp\s+Chat|Obrolan\s+WhatsApp)\s*-\s*(.+)$',
    ]

    for pat in prefix_patterns:
        match = re.match(pat, clean_stem, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            if extracted and extracted.lower() not in GENERIC_NAMES:
                return extracted

    if clean_stem.lower() in GENERIC_NAMES or re.match(r'^chat_\d+$', clean_stem, re.IGNORECASE):
        return None

    if len(clean_stem) > 1:
        return clean_stem

    return None


def create_chat_mapping(detected_chats: list[dict], chat_identifiers: list[str] = None) -> dict:
    mapping = {}
    
    for i, chat_info in enumerate(detected_chats):
        chat_id = chat_identifiers[i] if chat_identifiers and i < len(chat_identifiers) else 'chat_%d.txt' % (i + 1)
        source_fn = chat_info.get('filename') or chat_info.get('rel_path', 'chat_%d.txt' % (i + 1))
        cust_name = extract_customer_name(source_fn)
        
        mapping[chat_id] = {
            'source_filename': source_fn,
            'customer_name': cust_name
        }
        
    return mapping
