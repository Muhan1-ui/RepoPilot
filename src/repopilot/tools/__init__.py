"""工具注册表：工具的 OpenAI schema + 名字到实现的映射。"""

from .apply_patch import apply_patch
from .read_file import read_file
from .run_tests import run_tests
from .write_file import write_file


def _fn(name: str, desc: str, props: dict, required: tuple[str, ...] = ()) -> dict:
    """拼一个 OpenAI tool schema。"""
    return {"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": props, "required": list(required)}}}


TOOLS = [
    _fn("read_file", "修改代码前查看仓库内文件时使用。返回带行号的行区间；单次最多 200 行，大文件请分段读。",
        {"path": {"type": "string", "description": "仓库内路径，如 stats.py；也接受仓库内绝对路径"},
         "start": {"type": "integer", "description": "起始行，1-based，默认 1"},
         "end": {"type": "integer", "description": "结束行（含），默认文件末尾"}}, ("path",)),
    _fn("apply_patch", "确定要改哪些行后使用。传入标准 unified diff（---/+++/@@），"
                       "上下文必须与刚读到的内容一致；任一 hunk 失败会整批回滚。",
        {"patch": {"type": "string", "description": "unified diff 文本"}}, ("patch",)),
    _fn("run_tests", "每次改完代码后使用，验证是否修好。返回退出码和输出最后 40 行。",
        {"cmd": {"type": "string", "description": "测试命令，默认使用题目的 test_cmd"}}),
    _fn("write_file", "只在 apply_patch 连续失败、收到熔断提醒后使用。先用 read_file 读出完整文件，"
                      "再一次性传入 path 和完整的新文件内容（整文件覆盖，不要传 diff）。",
        {"path": {"type": "string", "description": "仓库内路径，如 stats.py；也接受仓库内绝对路径"},
         "content": {"type": "string", "description": "文件的完整新内容"}}, ("path", "content")),
]

_REGISTRY = {"read_file": read_file, "apply_patch": apply_patch,
             "run_tests": run_tests, "write_file": write_file}


def dispatch(name: str, args: dict, *, repo: str, docker: bool = False) -> str:
    """按模型给出的工具名执行；repo 由运行时注入，模型无权指定路径。"""
    if name not in _REGISTRY:
        raise KeyError(name)
    try:
        if name == "run_tests":
            return run_tests(**(args or {}), repo=repo, docker=docker)
        return _REGISTRY[name](**(args or {}), repo=repo)
    except Exception as e:
        return f"ERROR: {e}"
