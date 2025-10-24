from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class FileCache:
    def __init__(self, cache_dir: str = ".req-check-cache", expiry: int = 3600):
        """Initialize file-based cache.

        Args:
            cache_dir: Directory to store cache files (default: .req-check-cache in user's home)
            expiry: Cache expiry time in seconds (default: 1 hour)
        """
        self.cache_dir = Path.home() / cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.expiry = expiry

    def get(self, key: str) -> Any | None:
        """Get value from cache if it exists and hasn't expired."""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                # Check if item has custom TTL or use default expiry
                ttl = data.get("ttl", self.expiry)
                if data["timestamp"] + ttl > time.time():
                    return data["value"]
                # Clean up expired cache
                cache_file.unlink(missing_ok=True)
            except (json.JSONDecodeError, KeyError):
                # Clean up invalid cache
                cache_file.unlink(missing_ok=True)
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Save value to cache with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live in seconds (uses default expiry if not specified)
        """
        cache_file = self.cache_dir / f"{key}.json"
        data = {
            "timestamp": time.time(),
            "value": value,
        }
        # Store custom TTL if provided
        if ttl is not None:
            data["ttl"] = ttl

        cache_file.write_text(json.dumps(data))

    def clear(self) -> None:
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)
