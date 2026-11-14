"""
lib/cache.py — two-tier cache: memory + SQLite  (TODO: you implement)
=====================================================================
Why two tiers?
  - MEMORY (dict): instant, but lost on restart.
  - SQLite (disk): survives restarts, and is where you can inspect what your
    service has learned. Check memory first, then disk, then LLM.

The cache key must be deterministic for the same (text, target). Hashing the
input with sha256 gives you a compact, collision-safe key.

Fill in the TODOs. The method signatures and stats are laid out for you.
"""
import hashlib

import aiosqlite


def _key(text: str, target: str) -> str:
    return hashlib.sha256(f"{target}::{text}".encode("utf-8")).hexdigest()


class TwoTierCache:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._mem: dict[str, str] = {}
        self._stats = {"requests": 0, "memory_hits": 0, "db_hits": 0, "misses": 0}

    async def init(self) -> None:
        """Create the translations table if it doesn't exist."""
        # TODO (YOU): CREATE TABLE IF NOT EXISTS translations(
        #   key TEXT PRIMARY KEY, source TEXT, target TEXT, translated TEXT,
        #   model TEXT, access_count INTEGER DEFAULT 1, created_at TIMESTAMP)
        # and an index on key. Use aiosqlite.connect(self.db_path).
        raise NotImplementedError("Implement TwoTierCache.init()")

    async def get(self, text: str, target: str) -> str | None:
        """Return a cached translation or None. Check memory, then SQLite."""
        self._stats["requests"] += 1
        k = _key(text, target)

        # 1) memory tier
        if k in self._mem:
            self._stats["memory_hits"] += 1
            return self._mem[k]

        # 2) SQLite tier
        # TODO (YOU): SELECT translated FROM translations WHERE key = ?.
        #   On hit: bump access_count, warm the memory tier (self._mem[k]),
        #   record self._stats["db_hits"], and return the value.
        #   On miss: record self._stats["misses"] and return None.
        raise NotImplementedError("Implement TwoTierCache.get()")

    async def set(self, text: str, target: str, translated: str, model: str) -> None:
        """Store a translation in both tiers."""
        k = _key(text, target)
        self._mem[k] = translated
        # TODO (YOU): INSERT the row (upsert on key) into SQLite.
        raise NotImplementedError("Implement TwoTierCache.set()")

    async def size(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM translations") as cur:
                row = await cur.fetchone()
                return row[0] if row else 0

    async def stats(self) -> dict:
        total = self._stats["memory_hits"] + self._stats["db_hits"] + self._stats["misses"]
        hits = self._stats["memory_hits"] + self._stats["db_hits"]
        hit_rate = round(100 * hits / total, 1) if total else 0.0
        return {**self._stats, "hit_rate_pct": hit_rate, "memory_entries": len(self._mem)}
