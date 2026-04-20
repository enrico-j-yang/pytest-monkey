# Claude Code 配置

本项目为 pytest 随机测试运行器插件。

## 项目指南

详细开发规范和项目结构请参阅 [AGENTS.md](AGENTS.md)。

## 快速命令

```bash
# 运行测试
pytest tests/

# 运行随机测试 (CLI)
python random_runner.py tests/ --count 10

# 运行随机测试 (pytest插件)
pytest tests/ --random-runner --random-count 10
```

## 关键文件

- `runner/core.py` - 核心运行器
- `pytest_random_runner.py` - pytest 插件入口
- `random_runner.py` - CLI 入口
- `tests/test_runner/` - 单元测试