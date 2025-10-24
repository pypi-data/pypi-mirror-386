import sqlite3
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def _decode_value(val: Union[bytes, str]) -> str:
    return val.decode(errors="ignore") if isinstance(val, bytes) else val


def _find_full_conversation_headers(obj: Any) -> Optional[List[Dict[str, Any]]]:
    if isinstance(obj, dict):
        if "fullConversationHeadersOnly" in obj and isinstance(
            obj["fullConversationHeadersOnly"], list
        ):
            return obj["fullConversationHeadersOnly"]
        for v in obj.values():
            result = _find_full_conversation_headers(v)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _find_full_conversation_headers(item)
            if result:
                return result
    return None


def _get_vl_format_content(data: Dict[str, Any]) -> Dict[str, Any]:
    content = {"text": data.get("text", "").strip()}
    if content["text"]:
        return content
    content = {"toolFormerData": data.get("toolFormerData", {})}
    if content["toolFormerData"]:
        return content
    content = {"thinking": data.get("thinking", {}).get("text", "").strip()}
    if "thinking" in data:  # might be empty thinking result
        return content
    raise ValueError(f"No content found in bubble data {data}")


def _reconstruct_cursor_session(
    db_entries: Dict[str, Any], session_id: str
) -> tuple[list, list]:
    composer_key = f"composerData:{session_id}"
    bubble_prefix = "bubbleId:"

    bubble_map = {}
    for key, value in db_entries.items():
        if key.startswith(bubble_prefix):
            try:
                bubble_id = key.split(":")[-1]
                if bubble_id in bubble_map:
                    print(f"Duplicate bubbleId found: {bubble_id}")
                    raise ValueError(f"Duplicate bubbleId found: {bubble_id}")
                parsed = json.loads(_decode_value(value))
                bubble_map[bubble_id] = parsed
            except Exception:
                continue

    session = []
    vl_format = []
    if composer_key in db_entries:
        value = db_entries.get(composer_key)
        if value is None:
            logging.warning(f"Composer key {composer_key} found, but value is None.")
            return [], []
        parsed = json.loads(_decode_value(value))
        session.append(parsed)
        headers = _find_full_conversation_headers(parsed)
        if headers:
            for header in headers:
                bubble_id = header["bubbleId"]
                data = bubble_map.get(bubble_id, {})
                session.append({"bubbleId": bubble_id, "header": header, "data": data})
                content = _get_vl_format_content(data)
                vl_format.append(
                    {
                        "role": "user" if header.get("type") == 1 else "assistant",
                        "content": content,
                    }
                )
    else:
        logging.warning(f"Composer key {composer_key} not found in database.")
    return session, vl_format


def is_sqlite_file(path: Path) -> bool:
    """Check if a file is an SQLite database by reading its header."""
    try:
        with open(path, "rb") as f:
            header = f.read(16)
        return header == b"SQLite format 3\x00"
    except IOError:
        return False


def extract_session(
    sqlite_path: Union[str, Path], search_phrase: str
) -> tuple[list, list]:
    path_to_database_file = Path(sqlite_path).expanduser()
    logging.info(f"Extract session from database file: {path_to_database_file}")
    conn = sqlite3.connect(Path(sqlite_path).expanduser())
    cursor = conn.cursor()

    all_entries = {}
    for table in ["cursorDiskKV", "ItemTable"]:
        try:
            cursor.execute(f"SELECT key, value FROM {table};")
            for k, v in cursor.fetchall():
                if k in all_entries:
                    raise ValueError(f"Duplicate key found during merge: {k}")
                all_entries[k] = v
        except sqlite3.OperationalError:
            continue

    # Look for a value containing the search phrase
    matching_session_id = None
    for key, value in all_entries.items():
        try:
            decoded = _decode_value(value)
            if search_phrase in decoded:
                if key.startswith("bubbleId:"):
                    parts = key.split(":")
                    if len(parts) >= 2:
                        matching_session_id = parts[1]
                        break
        except Exception:
            continue

    if not matching_session_id:
        logging.warning(f"No matching session found for search phrase: {search_phrase}")
        return [], []

    session, vl_format = _reconstruct_cursor_session(all_entries, matching_session_id)
    return session, vl_format
