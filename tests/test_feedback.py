"""结构化失败回灌自测：用例名 / file:line / 截断 / 空输出不崩。"""

from repopilot.feedback import MAX_CHARS, format_pytest_failure

SAMPLE = """\
=================================== FAILURES ===================================
______________________________ test_median_even _______________________________

    def test_median_even():
>       assert median([1, 2, 3, 4]) == 2.5
E       assert 3 == 2.5
E        +  where 3 = median([1, 2, 3, 4])

tests/test_stats.py:16: AssertionError
=========================== short test summary info ============================
FAILED tests/test_stats.py::test_median_even - assert 3 == 2.5
1 failed, 3 passed in 0.05s
"""


def test_extracts_failed_name_location_and_assertion():
    out = format_pytest_failure(SAMPLE)
    assert "tests/test_stats.py::test_median_even" in out
    assert "tests/test_stats.py:16" in out
    assert "assert 3 == 2.5" in out
    assert "test_median_even" in out


def test_empty_output_does_not_raise():
    assert format_pytest_failure("") != ""
    assert format_pytest_failure("", "") != ""


def test_unparseable_output_falls_back_to_tail():
    raw = "\n".join(f"line{i}" for i in range(1, 31))
    out = format_pytest_failure(raw)
    assert "尾部 20 行" in out
    assert "line30" in out and "line11" in out and "line10" not in out


def test_long_output_is_truncated_and_marks_omitted():
    blocks = []
    for i in range(12):
        blocks.append(
            f"____ test_case_{i} ____\n"
            f">       assert {i} == {i + 1}\n"
            f"E       assert {i} == {i + 1} " + "x" * 150 + "\n\n"
            f"tests/test_x.py:{i + 1}: AssertionError")
    raw = ("FAILURES\n" + "\n".join(blocks) + "\n"
           + "\n".join(f"FAILED tests/test_x.py::test_case_{i} - assert {i} == {i + 1}"
                       for i in range(12)))
    out = format_pytest_failure(raw)
    assert len(out) <= MAX_CHARS
    assert "另有" in out and "未列出" in out
    assert "FAILED tests/test_x.py::test_case_0" in out


def test_max_failures_limits_listed_cases():
    raw = "\n".join(f"FAILED tests/test_x.py::test_{i} - assert {i} == {i + 1}"
                    for i in range(6))
    out = format_pytest_failure(raw, max_failures=2)
    assert "1) FAILED tests/test_x.py::test_0" in out
    assert "2) FAILED tests/test_x.py::test_1" in out
    assert "test_2" not in out
    assert "另有 4 条未列出" in out
