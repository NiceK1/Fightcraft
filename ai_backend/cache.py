"""Caching system for AI-generated assets."""
import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from collections import OrderedDict


class SpriteCache:
    """Two-tier caching system for generated sprites."""

    def __init__(self, cache_dir: str = "assets/cache", memory_size: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Memory cache (LRU)
        self.memory_cache: OrderedDict[str, bytes] = OrderedDict()
        self.memory_size = memory_size

    def _generate_key(self, materials: list, item_type: str, seed: Optional[int] = None) -> str:
        """Generate cache key from parameters."""
        # Sort materials for consistent hashing
        materials_str = "_".join(sorted(materials))
        key_string = f"{materials_str}_{item_type}_{seed if seed else 'random'}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, materials: list, item_type: str, seed: Optional[int] = None) -> Optional[bytes]:
        """Get cached sprite image data."""
        key = self._generate_key(materials, item_type, seed)

        # Check memory cache first
        if key in self.memory_cache:
            # Move to end (most recently used)
            self.memory_cache.move_to_end(key)
            return self.memory_cache[key]

        # Check disk cache
        cache_file = self.cache_dir / f"{key}.png"
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                data = f.read()
            # Add to memory cache
            self._add_to_memory(key, data)
            return data

        return None

    def set(self, materials: list, item_type: str, image_data: bytes, seed: Optional[int] = None):
        """Cache sprite image data."""
        key = self._generate_key(materials, item_type, seed)

        # Save to disk
        cache_file = self.cache_dir / f"{key}.png"
        with open(cache_file, "wb") as f:
            f.write(image_data)

        # Add to memory cache
        self._add_to_memory(key, image_data)

    def _add_to_memory(self, key: str, data: bytes):
        """Add data to memory cache with LRU eviction."""
        if key in self.memory_cache:
            self.memory_cache.move_to_end(key)
        else:
            self.memory_cache[key] = data
            # Evict oldest if over limit
            if len(self.memory_cache) > self.memory_size:
                self.memory_cache.popitem(last=False)


class StatsCache:
    """Caching system for generated stats."""

    def __init__(self, cache_dir: str = "assets/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.cache_dir / "stats_cache.json"

        # Load existing cache
        self.cache: Dict[str, Any] = {}
        if self.stats_file.exists():
            with open(self.stats_file, "r") as f:
                self.cache = json.load(f)

    def _generate_key(self, materials: list, item_type: str) -> str:
        """Generate cache key from parameters."""
        materials_str = "_".join(sorted(materials))
        key_string = f"{materials_str}_{item_type}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, materials: list, item_type: str) -> Optional[Dict[str, Any]]:
        """Get cached stats."""
        key = self._generate_key(materials, item_type)
        return self.cache.get(key)

    def set(self, materials: list, item_type: str, stats: Dict[str, Any]):
        """Cache stats data."""
        key = self._generate_key(materials, item_type)
        self.cache[key] = stats

        # Save to disk
        with open(self.stats_file, "w") as f:
            json.dump(self.cache, f, indent=2)
