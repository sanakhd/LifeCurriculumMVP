# app/storage/program_store.py
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from datetime import datetime, date
from enum import Enum

DATA_DIR = Path("data"); DATA_DIR.mkdir(exist_ok=True)
PROGRAMS_FILE = DATA_DIR / "programs.jsonl"

def _json_default(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, Enum):
        return o.value
    return str(o)

def _lines(p: Path) -> Iterable[str]:
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        yield from f

def _read_all() -> List[Dict]:
    out = []
    for line in _lines(PROGRAMS_FILE):
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out

def save_program(program_dict: Dict) -> None:
    with PROGRAMS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(program_dict, ensure_ascii=False, default=_json_default) + "\n")

def get_program(program_id: str) -> Optional[Dict]:
    for obj in _read_all():
        if obj.get("id") == program_id:
            return obj
    return None

def upsert_program(program_dict: Dict) -> None:
    arr = _read_all()
    for i, obj in enumerate(arr):
        if obj.get("id") == program_dict["id"]:
            arr[i] = program_dict
            break
    else:
        arr.append(program_dict)
    with PROGRAMS_FILE.open("w", encoding="utf-8") as f:
        for obj in arr:
            f.write(json.dumps(obj, ensure_ascii=False, default=_json_default) + "\n")

def delete_program(program_id: str) -> bool:
    """Delete a program by ID. Returns True if program was found and deleted, False otherwise."""
    arr = _read_all()
    original_length = len(arr)
    arr = [obj for obj in arr if obj.get("id") != program_id]
    
    if len(arr) == original_length:
        return False  # Program not found
    
    # Rewrite the file without the deleted program
    with PROGRAMS_FILE.open("w", encoding="utf-8") as f:
        for obj in arr:
            f.write(json.dumps(obj, ensure_ascii=False, default=_json_default) + "\n")
    
    return True

def list_programs(offset: int = 0, limit: int = 50) -> List[Dict]:
    items = _read_all()
    return items[offset: offset + limit]

def get_lesson_by_uuid(lesson_uuid: str) -> Optional[tuple]:
    """Find lesson by UUID across all programs. Returns (program_dict, lesson_dict) or None."""
    for program_dict in _read_all():
        lessons = program_dict.get("lessons", [])
        for lesson_dict in lessons:
            if lesson_dict.get("id") == lesson_uuid:
                return program_dict, lesson_dict
    return None

def get_all_lesson_ids() -> List[str]:
    """Get all lesson IDs from all programs in programs.jsonl"""
    lesson_ids = []
    for program_dict in _read_all():
        lessons = program_dict.get("lessons", [])
        for lesson_dict in lessons:
            lesson_id = lesson_dict.get("id")
            if lesson_id:
                lesson_ids.append(lesson_id)
    return lesson_ids
