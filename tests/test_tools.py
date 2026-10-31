"""工具层自测：行号/截断/越界、diff 应用与回滚、测试输出尾部、沙箱命令。"""

import sys

from repopilot.sandbox import build_docker_cmd
from repopilot.tools import apply_patch, read_file, run_tests


def test_read_file_range_truncation_and_escape(tmp_path):
    (tmp_path / "a.txt").write_text(
        "".join(f"line{i}\n" for i in range(1, 251)), encoding="utf-8")
    assert read_file("a.txt", 10, 12, repo=str(tmp_path)) == "10|line10\n11|line11\n12|line12"
    full = read_file("a.txt", repo=str(tmp_path))
    assert full.splitlines()[199] == "200|line200"
    assert full.splitlines()[-1] == "…(truncated, 共 250 行)"
    assert read_file("../x", repo=str(tmp_path)).startswith("ERROR:")


def test_read_file_accepts_absolute_path_inside_repo(tmp_path):
    target = tmp_path / "pkg" / "a.txt"
    target.parent.mkdir()
    target.write_text("hello\nworld\n", encoding="utf-8")
    assert read_file(str(target), repo=str(tmp_path)) == "1|hello\n2|world"


def test_read_file_rejects_absolute_path_outside_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    out = read_file(str(outside), repo=str(repo))
    assert out.startswith("ERROR:")
    assert str(repo.resolve()) in out


def test_read_file_repo_root_is_directory_hint_not_escape(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    for path in (".", str(tmp_path.resolve())):
        out = read_file(path, repo=str(tmp_path))
        assert out.startswith("ERROR:")
        assert "是目录" in out and "a.py" in out and "sub/" in out
        assert "escapes repo" not in out
        assert len(out) <= 200


def test_read_file_inside_dir_hints_but_outside_dir_escapes(tmp_path):
    repo = tmp_path / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "a.py").write_text("x = 1\n", encoding="utf-8")
    inside = read_file("pkg", repo=str(repo))
    assert inside.startswith("ERROR:") and "是目录" in inside
    assert "escapes repo" not in inside

    outside = tmp_path / "outside_dir"
    outside.mkdir()
    out = read_file(str(outside), repo=str(repo))
    assert out.startswith("ERROR:") and "escapes repo" in out
    assert str(repo.resolve()) in out


def test_apply_patch_ok_and_rollback(tmp_path):
    (tmp_path / "f.py").write_text("a = 1\nb = 2\n", encoding="utf-8")
    ok = apply_patch("--- a/f.py\n+++ b/f.py\n@@ -1,2 +1,2 @@\n a = 1\n-b = 2\n+b = 3\n",
                     repo=str(tmp_path))
    assert ok.startswith("OK") and (tmp_path / "f.py").read_text(encoding="utf-8") == "a = 1\nb = 3\n"
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("y = 1\n", encoding="utf-8")
    bad = ("--- a/a.py\n+++ b/a.py\n@@ -1,1 +1,1 @@\n-x = 1\n+x = 2\n"
           "--- a/b.py\n+++ b/b.py\n@@ -1,1 +1,1 @@\n-z = 1\n+z = 2\n")
    out = apply_patch(bad, repo=str(tmp_path))
    assert out.startswith("ERROR:") and "hunk 1 failed" in out
    assert (tmp_path / "a.py").read_text(encoding="utf-8") == "x = 1\n"
    assert (tmp_path / "b.py").read_text(encoding="utf-8") == "y = 1\n"


def test_run_tests_tail_and_sandbox(tmp_path):
    (tmp_path / "test_bad.py").write_text(
        "def test_bad():\n    assert 1 == 2\n", encoding="utf-8")
    out = run_tests(f"{sys.executable} -m pytest -q", repo=str(tmp_path))
    assert out.startswith("exit_code=1") and "test_bad" in out
    assert len(out.splitlines()) <= 42
    cmd = build_docker_cmd(".", "python -m pytest -q")
    for flag in ("--network=none", "--memory=1g", "--cpus=1", "/ws"):
        assert any(flag in part for part in cmd)
    assert cmd[-1] == "python -m pytest -q"


def test_run_tests_rejects_pipe_that_swallows_exit_code(tmp_path):
    out = run_tests(f"{sys.executable} -m pytest -q | tail -60", repo=str(tmp_path))
    assert out.startswith("ERROR:") and "元字符" in out


def test_run_tests_rejects_semicolon(tmp_path):
    out = run_tests(f"{sys.executable} -m pytest -q; true", repo=str(tmp_path))
    assert out.startswith("ERROR:") and "元字符" in out


def test_run_tests_failure_returns_structured_feedback(tmp_path):
    (tmp_path / "test_two.py").write_text(
        "def test_a():\n    assert 1 == 2\n\n\ndef test_b():\n    assert [1, 2] == [1, 3]\n",
        encoding="utf-8")
    out = run_tests(f"{sys.executable} -m pytest -q", repo=str(tmp_path))
    assert out.startswith("exit_code=1")
    assert "FAILED" in out
    assert "test_two.py::test_a" in out and "test_two.py::test_b" in out
    assert "test_two.py:" in out
    assert "assert 1 == 2" in out

