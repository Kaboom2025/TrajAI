"""Tests for Phase 8: Record/Replay Cache."""
from __future__ import annotations

import json
import tempfile

import pytest

from trajai.runner.replay import ReplayCache


def test_cache_key_stability() -> None:
    """Cache key should be stable for identical inputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ReplayCache(directory=tmpdir)

        messages = [{"role": "user", "content": "hello"}]
        key1 = cache._compute_cache_key("gpt-4", messages)
        key2 = cache._compute_cache_key("gpt-4", messages)

        assert key1 == key2


def test_cache_key_changes_with_model() -> None:
    """Cache key should change when model changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ReplayCache(directory=tmpdir)

        messages = [{"role": "user", "content": "hello"}]
        key1 = cache._compute_cache_key("gpt-4", messages)
        key2 = cache._compute_cache_key("gpt-3.5-turbo", messages)

        assert key1 != key2


def test_cache_key_changes_with_messages() -> None:
    """Cache key should change when messages change."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ReplayCache(directory=tmpdir)

        messages1 = [{"role": "user", "content": "hello"}]
        messages2 = [{"role": "user", "content": "goodbye"}]

        key1 = cache._compute_cache_key("gpt-4", messages1)
        key2 = cache._compute_cache_key("gpt-4", messages2)

        assert key1 != key2


def test_cache_put_and_get() -> None:
    """Test storing and retrieving cache entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ReplayCache(directory=tmpdir, ttl_hours=24.0)

        messages = [{"role": "user", "content": "test"}]
        response = {"choices": [{"message": {"content": "response"}}]}

        # Store
        cache.put(
            model="gpt-4",
            messages=messages,
            response=response,
            prompt_tokens=10,
            completion_tokens=5,
            cost=0.001,
        )

        # Retrieve
        cached = cache.get(model="gpt-4", messages=messages)

        assert cached is not None
        assert cached.model == "gpt-4"
        assert cached.response == response
        assert cached.prompt_tokens == 10
        assert cached.completion_tokens == 5
        assert cached.cost == 0.001


def test_cache_miss() -> None:
    """Test cache miss when entry doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ReplayCache(directory=tmpdir)

        messages = [{"role": "user", "content": "test"}]
        cached = cache.get(model="gpt-4", messages=messages)

        assert cached is None


def test_cache_ttl_expiration() -> None:
    """Test that expired cache entries are treated as misses."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ReplayCache(directory=tmpdir, ttl_hours=0.001)  # Very short TTL

        messages = [{"role": "user", "content": "test"}]
        response = {"choices": [{"message": {"content": "response"}}]}

        # Store
        cache.put(
            model="gpt-4",
            messages=messages,
            response=response,
        )

        # Manually expire the entry by modifying timestamp
        cache_path = cache._get_cache_path(
            cache._compute_cache_key("gpt-4", messages)
        )
        with open(cache_path, "r") as f:
            data = json.load(f)
        data["timestamp"] = 0  # Very old timestamp
        with open(cache_path, "w") as f:
            json.dump(data, f)

        # Should miss due to expiration
        cached = cache.get(model="gpt-4", messages=messages)
        assert cached is None


def test_cache_clear() -> None:
    """Test clearing all cache entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ReplayCache(directory=tmpdir)

        # Store multiple entries
        for i in range(3):
            cache.put(
                model="gpt-4",
                messages=[{"role": "user", "content": f"test{i}"}],
                response={"result": i},
            )

        # Verify entries exist
        stats = cache.stats()
        assert stats.entry_count == 3

        # Clear
        cache.clear()

        # Verify cleared
        stats = cache.stats()
        assert stats.entry_count == 0


def test_cache_stats() -> None:
    """Test cache statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ReplayCache(directory=tmpdir)

        messages = [{"role": "user", "content": "test"}]

        # Store and retrieve to generate hits
        cache.put(
            model="gpt-4",
            messages=messages,
            response={"result": "test"},
        )

        cache.get(model="gpt-4", messages=messages)
        cache.get(model="gpt-4", messages=messages)
        cache.get(
            model="gpt-4", messages=[{"role": "user", "content": "other"}]
        )  # miss

        stats = cache.stats()
        assert stats.entry_count == 1
        assert stats.hit_count == 2
        assert stats.miss_count == 1
        assert stats.hit_rate == pytest.approx(2/3, rel=0.01)


def test_cache_with_tools() -> None:
    """Test cache key includes tool definitions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ReplayCache(directory=tmpdir)

        messages = [{"role": "user", "content": "test"}]
        tools1 = [{"name": "tool1", "description": "test"}]
        tools2 = [{"name": "tool2", "description": "test"}]

        key1 = cache._compute_cache_key("gpt-4", messages, tools=tools1)
        key2 = cache._compute_cache_key("gpt-4", messages, tools=tools2)

        assert key1 != key2
