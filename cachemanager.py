# cachemanager.py
import json
import hashlib
from pathlib import Path

CACHE_DIR = Path.home() / ".pippilot_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _interp_hash(interpreter: str) -> str:
    return hashlib.sha256(interpreter.encode("utf-8")).hexdigest()[:12]

def get_cached_packages(interpreter: str):
    cache_file = CACHE_DIR / f"{_interp_hash(interpreter)}.json"
    if not cache_file.exists():
        return None
    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return None

def save_cached_packages(interpreter: str, packages: list):
    cache_file = CACHE_DIR / f"{_interp_hash(interpreter)}.json"
    try:
        cache_file.write_text(json.dumps(packages), encoding="utf-8")
    except Exception:
        pass

def clear_cache():
    for file in CACHE_DIR.glob("*.json"):
        try:
            file.unlink()
        except:
            pass
