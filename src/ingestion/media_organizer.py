# media_organizer.py - Pengorganisasian Media Berdasarkan Unit Percakapan WhatsApp

import os
from pathlib import Path

MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.webp', '.gif',
    '.mp4', '.mov', '.avi', '.m4a', '.mp3', '.aac', '.ogg',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv'
}


def is_media_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS


def organize_media_files(
    extracted_dir: str | Path,
    detected_chats: list[dict],
    chat_identifiers: list[str]
) -> tuple[dict[str, list[Path]], list[dict]]:
    ext_dir = Path(extracted_dir)
    all_media = sorted([p for p in ext_dir.rglob('*') if is_media_file(p)])

    assigned_media = {chat_id: [] for chat_id in chat_identifiers}
    unresolved_media = []

    if not all_media:
        return assigned_media, unresolved_media

    chat_meta = []
    for i, chat in enumerate(detected_chats):
        chat_id = chat_identifiers[i]
        content_lower = chat.get('content', '').lower()
        chat_file_path = chat.get('file_path')
        chat_dir = chat_file_path.parent if chat_file_path else None
        
        chat_meta.append({
            'chat_id': chat_id,
            'content_lower': content_lower,
            'chat_dir': chat_dir
        })

    for media_path in all_media:
        media_name_lower = media_path.name.lower()
        matched_chat_id = None

        for meta in chat_meta:
            if media_name_lower in meta['content_lower']:
                matched_chat_id = meta['chat_id']
                break

        if matched_chat_id is None:
            for meta in chat_meta:
                if meta['chat_dir'] and media_path.parent == meta['chat_dir']:
                    matched_chat_id = meta['chat_id']
                    break

        if matched_chat_id is None and len(detected_chats) == 1:
            matched_chat_id = chat_identifiers[0]

        if matched_chat_id is not None:
            assigned_media[matched_chat_id].append(media_path)
        else:
            unresolved_media.append({
                'file_path': media_path,
                'filename': media_path.name,
                'reason': 'unable_to_determine_chat'
            })

    return assigned_media, unresolved_media
