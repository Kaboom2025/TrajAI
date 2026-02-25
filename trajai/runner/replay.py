"""Record/Replay Cache for LLM responses.

This module provides caching functionality to store and replay LLM API responses
for deterministic test runs and cost savings.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class CacheMissError(Exception):
    """Raised when a cache entry is not found in replay-only mode."""
    pass


@dataclass
class CachedResponse:
    """A cached LLM response entry."""
    model: str
    response: dict[str, Any]
    prompt_tokens: int
    completion_tokens: int
    cost: float
    timestamp: float
    cache_key_inputs: dict[str, Any]  # For debugging


@dataclass
class CacheStats:
    """Statistics about the cache."""
    entry_count: int
    total_size_bytes: int
    hit_count: int = 0
    miss_count: int = 0

    @property
    def hit_rate(self) -> float:
        """Hit rate as a fraction (0.0 to 1.0)."""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return self.hit_count / total

    @property
    def estimated_savings_usd(self) -> float:
        """Estimated cost savings from cache hits."""
        # This is a rough estimate - actual savings depend on cache hit rate
        # We'll compute this based on average cost per entry
        return 0.0  # TODO: Implement if needed


class ReplayCache:
    """Manages LLM response caching for deterministic re-runs.

    Cache entries are stored as JSON files in `.trajai/cache/`, keyed by
    a hash of the request parameters (model, prompt, tools, etc.).
    """

    def __init__(
        self,
        directory: str | Path = ".trajai/cache",
        ttl_hours: float = 168.0,  # 7 days default
    ):
        self.directory = Path(directory)
        self.ttl_hours = ttl_hours
        self._hit_count = 0
        self._miss_count = 0

        # Ensure cache directory exists
        self.directory.mkdir(parents=True, exist_ok=True)

    def _compute_cache_key(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Compute a SHA-256 hash of the request parameters.

        The cache key includes:
        - Model name
        - System prompt (hashed)
        - Full message history
        - Tool definitions (names + schemas)
        - Temperature setting
        """
        key_data = {
            "model": model,
            "messages": messages,
            "tools": tools or [],
            "temperature": temperature,
            "system_prompt": system_prompt,
        }

        # Serialize to JSON for hashing
        key_json = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        key_hash = hashlib.sha256(key_json.encode("utf-8")).hexdigest()
        return key_hash

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.directory / f"{cache_key}.json"

    def get(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[CachedResponse]:
        """Retrieve a cached response if available and not expired.

        Returns None if cache miss or expired.
        """
        cache_key = self._compute_cache_key(
            model, messages, tools, temperature, system_prompt
        )
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            self._miss_count += 1
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check TTL
            timestamp = data.get("timestamp", 0)
            age_hours = (datetime.now().timestamp() - timestamp) / 3600
            if age_hours > self.ttl_hours:
                self._miss_count += 1
                return None

            # Deserialize
            cached = CachedResponse(
                model=data["model"],
                response=data["response"],
                prompt_tokens=data.get("prompt_tokens", 0),
                completion_tokens=data.get("completion_tokens", 0),
                cost=data.get("cost", 0.0),
                timestamp=data["timestamp"],
                cache_key_inputs=data.get("cache_key_inputs", {}),
            )

            self._hit_count += 1
            return cached

        except (json.JSONDecodeError, KeyError, IOError):
            # Corrupted cache file - treat as miss
            self._miss_count += 1
            return None

    def put(
        self,
        model: str,
        messages: list[dict[str, Any]],
        response: dict[str, Any],
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0,
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        """Store a response in the cache."""
        cache_key = self._compute_cache_key(
            model, messages, tools, temperature, system_prompt
        )
        cache_path = self._get_cache_path(cache_key)

        cache_entry = {
            "model": model,
            "response": response,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": cost,
            "timestamp": datetime.now().timestamp(),
            "cache_key_inputs": {
                "model": model,
                "message_count": len(messages),
                "tool_count": len(tools) if tools else 0,
                "temperature": temperature,
                "has_system_prompt": system_prompt is not None,
            },
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)
        except IOError:
            # Log but don't fail - caching is best-effort
            pass

    def clear(self) -> None:
        """Delete all cache entries."""
        if self.directory.exists():
            for cache_file in self.directory.glob("*.json"):
                try:
                    cache_file.unlink()
                except IOError:
                    pass
        self._hit_count = 0
        self._miss_count = 0

    def stats(self) -> CacheStats:
        """Get cache statistics."""
        entry_count = 0
        total_size = 0

        if self.directory.exists():
            for cache_file in self.directory.glob("*.json"):
                entry_count += 1
                try:
                    total_size += cache_file.stat().st_size
                except OSError:
                    pass

        return CacheStats(
            entry_count=entry_count,
            total_size_bytes=total_size,
            hit_count=self._hit_count,
            miss_count=self._miss_count,
        )
