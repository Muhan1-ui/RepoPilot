# real_0001 证据链

## 来源

- 上游仓库：https://github.com/tkem/cachetools
- 实际克隆镜像（本机无法直连 GitHub）：https://gitee.com/mirrors/cachetools.git
- 底座 HEAD：`e7104dd52bfe0e3aced6f3439fb6ed4d9c8ff52a`
  （`Update copilot instructions and review.`）
- 注入的 bugfix commit：`2609f068f909197d46c1ad84083fb3b1226db3de`
  （`Fix #417: Re-enable pickling of objects with cached methods.`）

## 候选 bugfix commit（clone 内 `git log --oneline -50`）

| hash | message |
|---|---|
| `2609f06` | Fix #417: Re-enable pickling of objects with cached methods. |
| `b34643f` | Fix @cachedmethod class access with receiver as keyword argument. |
| `95e6add` | Fix #443: Restore autospec calls to @cachedmethod decorated methods |

选用 `2609f06`：其源码 hunk 在 HEAD 上可无冲突反向应用，且它同时改了源码和测试。

## 注入方式

1. `git archive HEAD | tar -x -C repo_clean`：底座 = HEAD 全部内容。
2. `git show 2609f06 -- src ':!tests'` 生成只含**非测试文件**的 patch。
3. 在 `repo_clean` 内 `git apply -R <patch>`：反向应用源码改动；**测试文件保持 HEAD 版本**（即包含该 commit 新增的回归测试）。
4. 追加 `pytest.ini`（`pythonpath = src`、`testpaths = tests`）：cachetools 用 src-layout，容器内未安装包时需要此配置才能直接 `python -m pytest`。该文件是评测适配，不属于上游内容。

未纳入 `repo_clean/`：`.git`、`__pycache__`、`.venv`、`.pytest_cache`。

## 证伪：初始必须红

在 `repo_clean` 上执行 `python -m pytest -q`：

```
18 failed, 369 passed, 1 warning, 10 subtests passed in 1.53s
```

失败测试（12 个测试函数 + 6 个 subtest）：

```
FAILED tests/test_cachedmethod.py::CacheMethodTest::test_decorator_deepcopy_super
FAILED tests/test_cachedmethod.py::CacheMethodTest::test_decorator_pickle
FAILED tests/test_cachedmethod.py::CacheMethodTest::test_decorator_pickle_aliased
FAILED tests/test_cachedmethod.py::CacheMethodTest::test_decorator_pickle_info
FAILED tests/test_cachedmethod.py::CacheMethodTest::test_decorator_pickle_super
FAILED tests/test_cachedmethod.py::DictMethodTest::test_decorator_deepcopy_super
FAILED tests/test_cachedmethod.py::DictMethodTest::test_decorator_pickle
FAILED tests/test_cachedmethod.py::DictMethodTest::test_decorator_pickle_aliased
FAILED tests/test_cachedmethod.py::DictMethodTest::test_decorator_pickle_info
FAILED tests/test_cachedmethod.py::DictMethodTest::test_decorator_pickle_super
FAILED tests/test_cachedmethod.py::UnboundMethodTest::test_class_access_alias
FAILED tests/test_cachedmethod.py::UnboundMethodTest::test_class_access_copy
SUBFAILED(proto=0..5) tests/test_cachedmethod.py::UnboundMethodTest::test_class_access_pickle
```

代表性断言：

```
_pickle.PicklingError: Can't pickle <function Cached.get at 0x...>:
it's not the same object as tests.test_cachedmethod.Cached.get
when serializing dict item '__wrapped__'
when serializing cachetools._descriptor._Unbound state
```

## 证实：正向应用原始 commit 必须绿

在 `repo_clean` 的副本上 `git apply <2609f06 源码 patch>` 后执行同一命令：

```
381 passed, 16 subtests passed in 0.93s
```

## 说明

- 本题初始失败数与 HEAD 全绿基线（381 passed, 16 subtests）对应，说明只是反向注入了该 bugfix 的源码改动，没有误伤其它测试。
