"""LRUCache 行为测试。"""

import pytest

from cache import LRUCache


def test_put_and_get():
    c = LRUCache(2)
    c.put("a", 1)
    assert c.get("a") == 1
    assert c.get("zzz") is None


def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert c.keys() == ["b", "c"]
    assert c.evicted == ["a"]


def test_get_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert c.keys() == ["a", "c"]
    assert c.evicted == ["b"]


def test_update_existing_does_not_evict():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 9)
    assert c.get("a") == 9
    assert c.evicted == []
    assert c.keys() == ["b", "a"]


def test_contains():
    c = LRUCache(2)
    c.put("a", 1)
    assert "a" in c
    assert "b" not in c


def test_capacity_must_be_positive():
    with pytest.raises(ValueError):
        LRUCache(0)
