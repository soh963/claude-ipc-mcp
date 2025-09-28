#!/usr/bin/env python3
"""
Cache Manager for Unified IPC System
Codex's implementation - High-performance caching and memory optimization
"""

import time
import hashlib
import pickle
import json
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from collections import OrderedDict
from pathlib import Path
import threading
import heapq
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Individual cache entry"""
    key: str
    value: Any
    size: int
    ttl: float
    created: float
    accessed: float
    access_count: int = 0
    priority: int = 0


class CachePolicy:
    """Base class for cache eviction policies"""

    def evict(self, cache: Dict[str, CacheEntry], target_size: int) -> List[str]:
        """Return keys to evict"""
        raise NotImplementedError


class LRUPolicy(CachePolicy):
    """Least Recently Used eviction policy"""

    def evict(self, cache: Dict[str, CacheEntry], target_size: int) -> List[str]:
        # Sort by last accessed time
        sorted_entries = sorted(
            cache.items(),
            key=lambda x: x[1].accessed
        )

        evict_keys = []
        current_size = sum(e.size for e in cache.values())

        for key, entry in sorted_entries:
            if current_size <= target_size:
                break
            evict_keys.append(key)
            current_size -= entry.size

        return evict_keys


class LFUPolicy(CachePolicy):
    """Least Frequently Used eviction policy"""

    def evict(self, cache: Dict[str, CacheEntry], target_size: int) -> List[str]:
        # Sort by access count
        sorted_entries = sorted(
            cache.items(),
            key=lambda x: x[1].access_count
        )

        evict_keys = []
        current_size = sum(e.size for e in cache.values())

        for key, entry in sorted_entries:
            if current_size <= target_size:
                break
            evict_keys.append(key)
            current_size -= entry.size

        return evict_keys


class TTLPolicy(CachePolicy):
    """Time-To-Live based eviction policy"""

    def evict(self, cache: Dict[str, CacheEntry], target_size: int) -> List[str]:
        current_time = time.time()
        evict_keys = []

        # First evict expired entries
        for key, entry in cache.items():
            if current_time > entry.created + entry.ttl:
                evict_keys.append(key)

        # If still need more space, use LRU
        if evict_keys:
            return evict_keys

        return LRUPolicy().evict(cache, target_size)


class MemoryCache:
    """In-memory cache with configurable eviction policies"""

    def __init__(self, max_size: int = 100 * 1024 * 1024, policy: CachePolicy = None):
        self.max_size = max_size  # Max size in bytes
        self.policy = policy or LRUPolicy()
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]

                # Check TTL
                if time.time() > entry.created + entry.ttl:
                    del self.cache[key]
                    self.stats['misses'] += 1
                    return None

                # Update access info
                entry.accessed = time.time()
                entry.access_count += 1

                # Move to end (MRU position)
                self.cache.move_to_end(key)

                self.stats['hits'] += 1
                return entry.value

            self.stats['misses'] += 1
            return None

    def set(self, key: str, value: Any, ttl: float = 3600, priority: int = 0) -> bool:
        """Set value in cache"""
        # Calculate size
        try:
            size = len(pickle.dumps(value))
        except:
            size = len(str(value))

        # Check if value is too large
        if size > self.max_size:
            logger.warning(f"Value too large for cache: {size} bytes")
            return False

        with self.lock:
            # Remove old entry if exists
            if key in self.cache:
                del self.cache[key]

            # Check if need eviction
            current_size = sum(e.size for e in self.cache.values())
            if current_size + size > self.max_size:
                self._evict(self.max_size - size)

            # Add new entry
            entry = CacheEntry(
                key=key,
                value=value,
                size=size,
                ttl=ttl,
                created=time.time(),
                accessed=time.time(),
                priority=priority
            )

            self.cache[key] = entry
            return True

    def _evict(self, target_size: int):
        """Evict entries to reach target size"""
        evict_keys = self.policy.evict(self.cache, target_size)

        for key in evict_keys:
            del self.cache[key]
            self.stats['evictions'] += 1

    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            total_entries = len(self.cache)
            total_size = sum(e.size for e in self.cache.values())

            return {
                'entries': total_entries,
                'size': total_size,
                'max_size': self.max_size,
                'utilization': f"{(total_size / self.max_size) * 100:.1f}%",
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate': f"{(self.stats['hits'] / max(1, self.stats['hits'] + self.stats['misses'])) * 100:.1f}%",
                'evictions': self.stats['evictions']
            }


class DiskCache:
    """Disk-based cache for persistence"""

    def __init__(self, cache_dir: Path = None, max_size: int = 1024 * 1024 * 1024):
        self.cache_dir = cache_dir or Path.home() / '.claude-ipc-data' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
        self.index: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self._load_index()

    def _load_index(self):
        """Load cache index from disk"""
        index_file = self.cache_dir / 'index.json'
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache index: {e}")
                self.index = {}

    def _save_index(self):
        """Save cache index to disk"""
        index_file = self.cache_dir / 'index.json'
        try:
            with open(index_file, 'w') as f:
                json.dump(self.index, f)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for key"""
        # Hash key for filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        with self.lock:
            if key not in self.index:
                return None

            metadata = self.index[key]

            # Check TTL
            if time.time() > metadata['created'] + metadata['ttl']:
                self.delete(key)
                return None

            # Read from disk
            cache_file = self._get_cache_file(key)
            if not cache_file.exists():
                del self.index[key]
                return None

            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Failed to read cache file: {e}")
                self.delete(key)
                return None

    def set(self, key: str, value: Any, ttl: float = 3600) -> bool:
        """Set value in disk cache"""
        try:
            data = pickle.dumps(value)
            size = len(data)

            # Check size
            if size > self.max_size:
                return False

            with self.lock:
                # Check total size
                total_size = sum(m['size'] for m in self.index.values())
                if total_size + size > self.max_size:
                    self._evict_oldest(self.max_size - size)

                # Write to disk
                cache_file = self._get_cache_file(key)
                with open(cache_file, 'wb') as f:
                    f.write(data)

                # Update index
                self.index[key] = {
                    'size': size,
                    'created': time.time(),
                    'ttl': ttl
                }

                self._save_index()
                return True

        except Exception as e:
            logger.error(f"Failed to write cache: {e}")
            return False

    def _evict_oldest(self, target_size: int):
        """Evict oldest entries to reach target size"""
        sorted_entries = sorted(
            self.index.items(),
            key=lambda x: x[1]['created']
        )

        current_size = sum(m['size'] for m in self.index.values())

        for key, metadata in sorted_entries:
            if current_size <= target_size:
                break

            self.delete(key)
            current_size -= metadata['size']

    def delete(self, key: str) -> bool:
        """Delete from disk cache"""
        with self.lock:
            if key in self.index:
                # Delete file
                cache_file = self._get_cache_file(key)
                if cache_file.exists():
                    cache_file.unlink()

                # Remove from index
                del self.index[key]
                self._save_index()
                return True
            return False


class CacheManager:
    """Main cache manager combining memory and disk caching"""

    def __init__(self,
                 memory_size: int = 100 * 1024 * 1024,
                 disk_size: int = 1024 * 1024 * 1024,
                 policy: str = 'lru'):

        # Select eviction policy
        policies = {
            'lru': LRUPolicy(),
            'lfu': LFUPolicy(),
            'ttl': TTLPolicy()
        }
        cache_policy = policies.get(policy, LRUPolicy())

        # Initialize caches
        self.memory_cache = MemoryCache(memory_size, cache_policy)
        self.disk_cache = DiskCache(max_size=disk_size)

        # Cache configuration
        self.use_disk = True
        self.memory_first = True

        logger.info(f"Cache Manager initialized (Memory: {memory_size}, Disk: {disk_size}, Policy: {policy})")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory then disk)"""
        # Try memory first
        value = self.memory_cache.get(key)
        if value is not None:
            return value

        # Try disk if enabled
        if self.use_disk:
            value = self.disk_cache.get(key)
            if value is not None:
                # Promote to memory cache
                self.memory_cache.set(key, value)
                return value

        return None

    def set(self, key: str, value: Any, ttl: float = 3600, priority: int = 0) -> bool:
        """Set value in cache"""
        # Store in memory
        mem_result = self.memory_cache.set(key, value, ttl, priority)

        # Store in disk if enabled
        if self.use_disk and (not self.memory_first or not mem_result):
            return self.disk_cache.set(key, value, ttl)

        return mem_result

    def delete(self, key: str) -> bool:
        """Delete from all caches"""
        mem_result = self.memory_cache.delete(key)
        disk_result = self.disk_cache.delete(key) if self.use_disk else False
        return mem_result or disk_result

    def clear(self):
        """Clear all caches"""
        self.memory_cache.clear()

        if self.use_disk:
            # Clear disk cache
            for key in list(self.disk_cache.index.keys()):
                self.disk_cache.delete(key)

    def get_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        return {
            'memory': self.memory_cache.get_stats(),
            'disk': {
                'entries': len(self.disk_cache.index),
                'size': sum(m['size'] for m in self.disk_cache.index.values()),
                'max_size': self.disk_cache.max_size
            } if self.use_disk else None
        }

    def cache_message(self, message: Dict) -> str:
        """Cache a message and return cache key"""
        # Generate cache key
        key = f"msg_{message.get('id', '')}_{message.get('type', '')}"

        # Set with default TTL
        self.set(key, message, ttl=300)  # 5 minutes

        return key

    def cache_route(self, from_id: str, to_id: str, route: List[str]):
        """Cache a routing path"""
        key = f"route_{from_id}_{to_id}"
        self.set(key, route, ttl=600)  # 10 minutes

    def get_cached_route(self, from_id: str, to_id: str) -> Optional[List[str]]:
        """Get cached routing path"""
        key = f"route_{from_id}_{to_id}"
        return self.get(key)


def main():
    """Test cache manager"""
    cache = CacheManager(
        memory_size=10 * 1024,  # 10KB for testing
        disk_size=100 * 1024,    # 100KB for testing
        policy='lru'
    )

    # Test basic operations
    print("Testing cache operations...")

    # Set values
    for i in range(10):
        key = f"key_{i}"
        value = f"value_{i}" * 100  # Make it larger
        cache.set(key, value, ttl=60)

    # Get values
    for i in range(5):
        key = f"key_{i}"
        value = cache.get(key)
        print(f"Retrieved {key}: {value[:20] if value else None}...")

    # Test message caching
    message = {
        'id': '12345',
        'type': 'test',
        'content': 'Hello World'
    }
    cache_key = cache.cache_message(message)
    print(f"Cached message with key: {cache_key}")

    # Test routing cache
    cache.cache_route('node1', 'node2', ['router1', 'router2', 'router3'])
    route = cache.get_cached_route('node1', 'node2')
    print(f"Cached route: {route}")

    # Get statistics
    stats = cache.get_stats()
    print(f"Cache stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    main()