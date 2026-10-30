"""固定容量的 LRU 缓存。"""

from collections import OrderedDict


class LRUCache:
    """容量固定的缓存：命中会刷新为最近使用，超出容量时淘汰最久未用的条目。"""

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._data = OrderedDict()
        self.evicted = []

    def get(self, key):
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key, value):
        if key in self._data:
            self._data[key] = value
            self._data.move_to_end(key)
            return
        self._data[key] = value
        while len(self._data) > self.capacity:
            victim, _ = self._data.popitem(last=True)
            self.evicted.append(victim)

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        """按从最久未用到最近使用的顺序返回键。"""
        return list(self._data)
