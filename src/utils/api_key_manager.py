"""
src/utils/api_key_manager.py
Rotates multiple free API keys to avoid rate limits.
Usage: key_manager = APIKeyManager("NEWS_API_KEY")
       api_key = key_manager.get_key()
"""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)

class APIKeyManager:
    def __init__(self, env_var_name: str, delimiter: str = ","):
        raw = os.getenv(env_var_name, "")
        self.keys = [k.strip() for k in raw.split(delimiter) if k.strip()]
        self._index = 0
        self.env_name = env_var_name
        
        if not self.keys:
            logger.warning(f"No keys found for {env_var_name}")
        else:
            logger.info(f"Loaded {len(self.keys)} key(s) for {env_var_name}")

    def get_key(self) -> str:
        """Round-robin key selection."""
        if not self.keys:
            return ""
        key = self.keys[self._index % len(self.keys)]
        self._index += 1
        return key

    def get_all_keys(self) -> List[str]:
        return self.keys.copy()

    def rotate_on_error(self, failed_key: str):
        """Call this when a key fails to temporarily deprioritize it."""
        if failed_key in self.keys and len(self.keys) > 1:
            logger.warning(f"Rotating away from failed key (ends with ...{failed_key[-4:]})")
            # Move failed key to end of rotation
            self.keys.remove(failed_key)
            self.keys.append(failed_key)