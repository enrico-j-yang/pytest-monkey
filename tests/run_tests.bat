@echo off
REM WebSocket ASR API 测试运行脚本 (Windows)

REM 检查是否设置了 token
if "%ASR_API_TOKEN%"=="" (
    echo 错误: 未设置 ASR_API_TOKEN 环境变量
    echo 请先设置: set ASR_API_TOKEN=your_token_here
    exit /b 1
)

REM 检查音频文件是否存在
if not exist "audio\今天天气怎么样.wav" (
    echo 警告: 音频文件不存在: audio\今天天气怎么样.wav
    echo 部分测试可能会被跳过
)

REM 显示配置信息
echo ==========================================
echo WebSocket ASR API 测试配置
echo ==========================================
if "%ASR_API_URL%"=="" (
    echo API URL: wss://api.listenai.com/v2/asr
) else (
    echo API URL: %ASR_API_URL%
)
echo Token: %ASR_API_TOKEN:~0,20%...
echo 音频文件: audio\今天天气怎么样.wav
echo ==========================================
echo.

REM 运行测试
echo 开始运行测试...
pytest tests\test_websocket_asr_api.py -v -s %*

REM 显示测试结果
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 所有测试通过！
) else (
    echo.
    echo ❌ 部分测试失败，请查看上面的错误信息
)
