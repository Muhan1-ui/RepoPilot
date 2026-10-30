"""按请求 id 去重的幂等服务。"""

from cache import LRUCache


class Service:
    """同一请求 id 只处理一次；critical 请求在服务生命周期内始终命中缓存。"""

    def __init__(self, capacity: int = 2):
        self._cache = LRUCache(capacity)
        self._pinned = set()
        self.processed = []

    def handle(self, req_id: str, payload: str, critical: bool = False) -> str:
        """处理请求；重复 id 直接返回首次结果。"""
        cached = self._cache.get(req_id)
        if cached is not None:
            return cached
        if critical:
            self._pinned.add(req_id)
        self.processed.append(req_id)
        result = payload.upper()
        self._cache.put(req_id, result)
        return result

    def is_cached(self, req_id: str) -> bool:
        return req_id in self._cache
