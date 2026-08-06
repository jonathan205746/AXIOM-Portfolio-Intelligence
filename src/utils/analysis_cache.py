"""
src/utils/analysis_cache.py
Simple file-based cache for portfolio analysis results.
Prevents burning through free API quotas on every page refresh.
"""

import os
import json
import hashlib
import time
from pathlib import Path

CACHE_DIR = Path(os.getenv("ANALYSIS_CACHE_DIR", "/tmp/analysis_cache"))
CACHE_TTL_SECONDS = int(os.getenv("ANALYSIS_CACHE_TTL", "3600"))  # 1 hour default
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _make_key(portfolio_id: int, alpha: float) -> str:
    raw = f"{portfolio_id}:{alpha}"
    return hashlib.md5(raw.encode()).hexdigest()

def get_cached_analysis(portfolio_id: int, alpha: float) -> dict | None:
    key = _make_key(portfolio_id, alpha)
    path = CACHE_DIR / f"{key}.json"
    
    if not path.exists():
        return None
    
    # Check TTL
    age = time.time() - path.stat().st_mtime
    if age > CACHE_TTL_SECONDS:
        path.unlink()
        return None
    
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None

def save_analysis_cache(portfolio_id: int, alpha: float, result: dict):
    key = _make_key(portfolio_id, alpha)
    path = CACHE_DIR / f"{key}.json"
    try:
        with open(path, "w") as f:
            json.dump(result, f)
    except Exception as e:
        print(f"Cache write failed: {e}")