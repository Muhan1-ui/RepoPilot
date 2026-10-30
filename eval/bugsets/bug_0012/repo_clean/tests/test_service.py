"""Service 幂等语义测试。"""

from service import Service


def test_duplicate_returns_first_result():
    svc = Service(capacity=2)
    assert svc.handle("a", "one") == "ONE"
    assert svc.handle("a", "two") == "ONE"
    assert svc.processed == ["a"]


def test_new_entry_is_cached_after_overflow():
    svc = Service(capacity=2)
    for req_id in ("a", "b", "c"):
        svc.handle(req_id, req_id)
    assert svc.is_cached("c")


def test_duplicate_after_overflow_is_not_reprocessed():
    svc = Service(capacity=2)
    for req_id in ("a", "b", "c"):
        svc.handle(req_id, req_id)
    svc.handle("c", "again")
    assert svc.processed.count("c") == 1


def test_critical_request_survives_overflow():
    svc = Service(capacity=2)
    svc.handle("c1", "x", critical=True)
    svc.handle("n1", "x")
    svc.handle("n2", "x")
    assert svc.is_cached("c1")


def test_critical_duplicate_is_not_reprocessed():
    svc = Service(capacity=2)
    svc.handle("c1", "x", critical=True)
    svc.handle("n1", "x")
    svc.handle("n2", "x")
    assert svc.handle("c1", "y") == "X"
    assert svc.processed.count("c1") == 1
