"""报表渲染测试。"""

from report import render, total_cents


def test_total_cents_rounds_half_up():
    assert total_cents(["1.005"]) == 101


def test_total_cents_of_115():
    assert total_cents(["1.15"]) == 115


def test_render_single():
    assert render(["1.15"]) == "合计：¥1.15（115 分）"


def test_render_multiple():
    assert render(["0.10", "0.20"]) == "合计：¥0.30（30 分）"


def test_render_empty():
    assert render([]) == "合计：¥0.00（0 分）"
