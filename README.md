# pytest-monkey

一个 pytest 插件和 CLI 工具，用于随机顺序多次执行测试，支持可复现的随机测试运行。

## 功能特性

- **随机顺序执行**: 从测试集合中随机选择测试多次运行
- **可复现运行**: 通过 seed 参数保证测试顺序可复现
- **pytest 插件模式**: 作为 pytest 插件无缝集成
- **独立 CLI 工具**: 可作为命令行工具独立使用
- **详细报告**: 自动生成 JSON 和 HTML 格式的测试报告
- **失败控制**: 支持遇到失败时继续执行或立即停止

## 安装

```bash
pip install pytest-monkey
```

或使用 PDM:

```bash
pdm install
```

## 使用方式

### 1. 作为 pytest 插件使用

在 pytest 命令中添加 `--random-runner` 选项:

```bash
# 基本用法 - 运行 100 次随机测试
pytest tests/ --random-runner --random-count 100

# 指定种子复现测试顺序
pytest tests/ --random-runner --random-count 100 --random-seed 42

# 失败时继续执行
pytest tests/ --random-runner --random-count 100 --random-continue-on-fail

# 显示测试输出 (类似 pytest -s)
pytest tests/ --random-runner --random-count 100 --random-no-capture
```

### 2. 作为 CLI 工具使用

直接运行 `random_runner.py`:

```bash
# 从目录运行 100 次随机测试
python random_runner.py tests/ --count 100

# 从单个文件运行 50 次测试
python random_runner.py tests/test_file.py --count 50

# 指定测试方法并设置种子
python random_runner.py tests/test_file.py::test_name --count 20 --seed 42

# 失败时继续执行，详细输出
python random_runner.py tests/ --count 100 --continue-on-fail -v

# 显示测试输出 (类似 pytest -s)
python random_runner.py tests/ --count 100 -s
```

## 参数说明

### pytest 插件参数

| 参数 | 说明 |
|------|------|
| `--random-runner` | 启用随机测试运行模式 |
| `--random-count` | 测试运行次数 (必需) |
| `--random-seed` | 随机种子 (默认自动生成 10 位数字) |
| `--random-continue-on-fail` | 失败时继续执行 |
| `--random-no-capture` | 禁用输出捕获，显示测试输出 |

### CLI 参数

| 参数 | 说明 |
|------|------|
| `test_spec` | 测试目标 (文件/类/方法/目录路径) |
| `--count` | 测试运行次数 (必需) |
| `--seed` | 随机种子 (默认自动生成 10 位数字) |
| `--continue-on-fail` | 失败时继续执行 |
| `--report-dir` | 报告保存目录 (默认 ./reports) |
| `-v, --verbose` | 详细输出模式 |
| `-s, --no-capture` | 禁用输出捕获 |

## 测试报告

每次运行结束后自动生成两种报告:

- **JSON 报告**: `reports/report.json`
- **HTML 报告**: `reports/report.html`

报告包含:
- 随机种子
- 总运行次数、通过/失败统计
- 每次测试的详细结果 (名称、耗时、错误信息)
- 运行时间戳

## 复现测试

运行时会打印随机种子，例如:

```
Random seed: 1234567890
```

使用相同种子可复现相同的测试顺序:

```bash
python random_runner.py tests/ --count 100 --seed 1234567890
```

## 测试选择语法

支持 pytest 标准选择语法:

- 文件: `tests/test_xxx.py`
- 类: `tests/test_xxx.py::TestClass`
- 方法: `tests/test_xxx.py::TestClass::test_method`
- 目录: `tests/`

## 开发

### 项目结构

```
pytest-monkey/
├── runner/
│   ├── core.py       # 核心运行器
│   ├── collector.py  # 测试收集器
│   ├── selector.py   # 随机选择器
│   ├── executor.py   # 测试执行器
│   ├── reporter.py   # 报告生成器
│   └── models.py     # 数据模型
├── pytest_random_runner.py  # pytest 插件入口
├── random_runner.py         # CLI 入口
└── tests/                   # 测试文件
```

### 运行测试

```bash
pytest tests/
```

## 许可证

MIT License