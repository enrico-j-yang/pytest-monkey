# Agent 配置指南

本文档为 AI 助手提供 pytest-monkey 项目的工作指南。

## 项目概述

pytest-monkey 是一个 pytest 插件和 CLI 工具，用于随机顺序多次执行测试。核心功能：

- 从测试集合中随机选择测试多次运行
- 通过 seed 参数保证测试顺序可复现
- 自动生成 JSON/HTML 测试报告

## 技术栈

- Python 3.12
- pytest (测试框架)
- tqdm (进度条)
- PDM (包管理)

## 项目结构

```
pytest-monkey/
├── runner/               # 核心模块
│   ├── core.py          # RunnerCore - 整合所有组件
│   ├── collector.py     # TestCollector - 收集pytest测试项
│   ├── selector.py      # RandomSelector - 随机选择测试
│   ├── executor.py      # TestExecutor - 执行单个测试
│   ├── reporter.py      # ResultReporter - 生成报告
│   └── models.py        # 数据模型 (TestResult, RunReport)
├── pytest_random_runner.py  # pytest插件入口
├── random_runner.py         # CLI入口
├── tests/                   # 测试目录
└── reports/                 # 报告输出目录 (运行时生成)
```

## 开发规范

### 编码风格

- 使用中文注释和文档字符串 (reporter.py, selector.py 等已有示例)
- 使用 dataclass 定义数据模型
- 函数和类添加类型注解
- 保持模块职责单一

### 测试要求

- 所有新功能必须有对应的单元测试
- 测试文件放在 `tests/test_runner/` 目录
- 使用 pytest 编写测试
- 运行测试: `pytest tests/`

### 代码质量检查

**必须执行的规则**: 每次修改 pytest 脚本后，执行以下 pylint 检查命令:

```bash
pylint --rcfile=.pylintrc --output-format=parseable --disable=R -rn .
```

修复所有 pylint 报告的错误，直到评分达到 10 分。

### 核心组件交互

RunnerCore 是核心协调器，按以下顺序工作:

1. TestCollector.collect() → 收集测试项
2. RandomSelector.select() → 选择随机序列
3. TestExecutor.execute() → 执行每个测试
4. ResultReporter → 记录结果、生成报告

修改任何组件时，确保与 RunnerCore 的接口兼容。

## 常见任务

### 添加新功能

1. 在对应模块中实现功能
2. 更新 RunnerCore (如果需要集成)
3. 更新 CLI/插件参数 (random_runner.py, pytest_random_runner.py)
4. 编写单元测试
5. 更新 README.md

### 修改报告格式

- 修改 `runner/reporter.py` 中的 `generate_html()` 或 `generate_json()`
- 确保数据来自 `runner/models.py` 的 RunReport

### 添加新的选择策略

- 在 `runner/selector.py` 中扩展 RandomSelector
- 或创建新的选择器类，在 RunnerCore 中替换

## 注意事项

- 测试执行使用 pytest.main() 内部机制，确保测试上下文正确
- 随机种子默认生成 10 位数字，便于复现
- 报告目录默认为 `./reports`，运行前会自动创建