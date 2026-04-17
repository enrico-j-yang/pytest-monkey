#!/bin/bash

# WebSocket ASR API 测试运行脚本

# 检查是否设置了 token
if [ -z "$ASR_API_TOKEN" ]; then
    echo "错误: 未设置 ASR_API_TOKEN 环境变量"
    echo "请先设置: export ASR_API_TOKEN='your_token_here'"
    exit 1
fi

# 检查音频文件是否存在
if [ ! -f "audio/今天天气怎么样.wav" ]; then
    echo "警告: 音频文件不存在: audio/今天天气怎么样.wav"
    echo "部分测试可能会被跳过"
fi

# 显示配置信息
echo "=========================================="
echo "WebSocket ASR API 测试配置"
echo "=========================================="
echo "API URL: ${ASR_API_URL:-wss://api.listenai.com/v2/asr}"
echo "Token: ${ASR_API_TOKEN:0:20}..."
echo "音频文件: audio/今天天气怎么样.wav"
echo "=========================================="
echo ""

# 运行测试
echo "开始运行测试..."
pytest tests/test_websocket_asr_api.py -v -s "$@"

# 显示测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 所有测试通过！"
else
    echo ""
    echo "❌ 部分测试失败，请查看上面的错误信息"
fi
