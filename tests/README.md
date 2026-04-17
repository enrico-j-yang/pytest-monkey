# WebSocket ASR API 测试套件

## 📚 文档导航

- **[快速参考指南](QUICK_REFERENCE.md)** - 快速开始和常用命令
- **[完整测试文档](TEST_DOCUMENTATION.md)** - 详细的测试用例说明
- **[声纹识别测试指南](VPR_TEST_GUIDE.md)** - 声纹识别测试详解

---

## 🚀 快速开始

### 1. 设置环境变量

```bash
export LISTENAI_API_KEY=your_api_key_here
```

### 2. 准备音频文件

确保 `audio/` 目录包含以下文件：
- `今天天气怎么样.wav` - 杨俊的声音（基础测试、声纹正样本）
- `全双工-雪艳.wav` - 雪艳的声音（声纹负样本）
- `杨俊.mp3` - 杨俊的声音（创建声纹特征）
- `audio.pcm` - PCM 格式音频
- `audio.speex` - Speex 格式音频
- `audio.ico` - ICO 格式音频

### 3. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行声纹识别测试（推荐加 -s 查看详细输出）
pytest tests/test_websocket_asr_api.py::TestContinuousRecognitionWorkflow -v -s
```

---

## 📋 测试概览

### 测试文件

| 文件 | 说明 | 测试数量 |
|------|------|----------|
| `test_websocket_asr_api.py` | WebSocket ASR API 核心功能测试 | 12+ |
| `test_audio_formats.py` | 音频格式支持测试 | 7+ |
| `conftest.py` | Pytest 配置和 Fixtures | 40+ fixtures |

### 主要测试类

| 测试类 | 功能 |
|--------|------|
| `TestWebSocketConnection` | WebSocket 连接测试 |
| `TestSessionCreation` | 会话创建测试 |
| `TestSingleRecognitionWorkflow` | 单次识别流程测试 |
| `TestContinuousRecognitionWorkflow` | 连续识别流程测试 |
| `TestAudioFormats` | 音频格式测试 |
| `TestErrorHandling` | 错误处理测试 |
| `TestAdvancedFeatures` | 高级功能测试（VAD等） |

---

## 🎯 重点测试：声纹识别

### test_continuous_recognition_vpr_audio_data

使用 base64 编码的音频数据进行声纹识别

```bash
pytest tests/test_websocket_asr_api.py::TestContinuousRecognitionWorkflow::test_continuous_recognition_vpr_audio_data -v -s
```

### test_continuous_recognition_vpr_feature_id

使用预先创建的特征 ID 进行声纹识别

```bash
pytest tests/test_websocket_asr_api.py::TestContinuousRecognitionWorkflow::test_continuous_recognition_vpr_feature_id -v -s
```

### 测试逻辑

两个测试都验证以下场景：

| 轮次 | 音频文件 | 说话人 | 预期结果 | 原因 |
|------|----------|--------|----------|------|
| 第1轮 | 今天天气怎么样.wav | 杨俊 | ✅ 有识别结果 | 声纹匹配 |
| 第2轮 | 全双工-雪艳.wav | 雪艳 | ❌ 无识别结果 | 声纹不匹配 |

详细说明请查看 [VPR_TEST_GUIDE.md](VPR_TEST_GUIDE.md)

---

## 🔧 常用命令

### 运行特定测试

```bash
# 连接测试
pytest tests/test_websocket_asr_api.py::TestWebSocketConnection -v

# 单次识别测试
pytest tests/test_websocket_asr_api.py::TestSingleRecognitionWorkflow -v

# 连续识别测试
pytest tests/test_websocket_asr_api.py::TestContinuousRecognitionWorkflow -v

# 音频格式测试
pytest tests/test_audio_formats.py -v
```

### 查看详细输出

```bash
# 显示 print 输出
pytest tests/ -v -s

# 显示更详细的信息
pytest tests/ -vv

# 简短的错误信息
pytest tests/ -v --tb=short
```

### 过滤测试

```bash
# 跳过慢速测试
pytest tests/ -m "not slow" -v

# 只运行集成测试
pytest tests/ -m integration -v

# 运行包含特定关键字的测试
pytest tests/ -k "vpr" -v
```

---

## 📊 测试覆盖范围

### 已覆盖功能 ✅

- WebSocket 连接管理
- 认证和授权
- 会话创建和配置
- 单次识别流程
- 连续识别流程
- 多种音频格式（PCM、Speex、ICO）
- **声纹识别（音频数据和特征 ID）** ⭐
- VAD 语音活动检测
- 自定义热词
- 错误处理

### 待扩展功能 ⏳

- EVAD 多维度检测
- 唤醒词测试
- 标点控制测试
- 实时结果返回测试
- 更多错误场景测试
- 性能和压力测试

---

## 🐛 故障排查

### 测试被跳过

**原因**: 缺少环境变量或音频文件

**解决**:
```bash
# 检查环境变量
echo $LISTENAI_API_KEY

# 检查音频文件
ls -lh audio/
```

### 连接超时

**原因**: 网络问题或 Token 无效

**解决**:
```bash
# 检查网络
ping staging-api.listenai.com

# 验证 Token
curl -H "Authorization: Bearer $LISTENAI_API_KEY" https://staging-api.listenai.com/v1/vpr/group
```

### 声纹识别测试失败

**原因**: 音频文件说话人不正确

**解决**:
- 确认"今天天气怎么样.wav"是杨俊的声音
- 确认"全双工-雪艳.wav"是雪艳的声音
- 查看测试输出中的 VPR 结果

更多故障排查信息请查看 [TEST_DOCUMENTATION.md](TEST_DOCUMENTATION.md#故障排查)

---

## 📁 文件结构

```
tests/
├── README.md                        # 本文档（入口）
├── QUICK_REFERENCE.md              # 快速参考指南
├── TEST_DOCUMENTATION.md           # 完整测试文档
├── VPR_TEST_GUIDE.md              # 声纹识别测试指南
├── conftest.py                     # Pytest 配置和 Fixtures
├── test_websocket_asr_api.py       # WebSocket ASR API 测试
├── test_audio_formats.py           # 音频格式测试
├── run_tests.sh                    # Linux/Mac 运行脚本
└── run_tests.bat                   # Windows 运行脚本
```

---

## 🔗 相关资源

- [Pytest 官方文档](https://docs.pytest.org/)
- [WebSocket-client 文档](https://websocket-client.readthedocs.io/)
- [聆思 ASR API 文档](https://docs.listenai.com/)

---

## 📝 更新日志

### 2024-12-16

#### ✨ 新增
- 声纹识别测试用例修改：测试匹配和不匹配场景
- `xueyan_audio_file` fixture
- 完整的测试文档套件

#### 🔧 修改
- `test_continuous_recognition_vpr_audio_data`: 第1轮测试匹配，第2轮测试不匹配
- `test_continuous_recognition_vpr_feature_id`: 第1轮测试匹配，第2轮测试不匹配

#### 📚 文档
- 创建 `TEST_DOCUMENTATION.md` - 完整测试文档
- 创建 `VPR_TEST_GUIDE.md` - 声纹识别测试指南
- 创建 `QUICK_REFERENCE.md` - 快速参考指南
- 创建 `README.md` - 测试套件入口文档

---

## 💡 提示

- 运行声纹识别测试时建议加 `-s` 参数查看详细输出
- 第一次运行测试时会自动创建声纹特征库和特征
- 测试结束后会自动清理创建的资源
- 如果测试失败，查看输出中的 VPR 结果和识别文本

---

## 📞 获取帮助

```bash
# 查看 pytest 帮助
pytest --help

# 查看可用的 fixtures
pytest --fixtures

# 查看可用的标记
pytest --markers

# 列出所有测试用例（不运行）
pytest --collect-only
```

---

**祝测试顺利！** 🎉
