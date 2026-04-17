"""
简化的 VPR 测试：只测试是否能收到 VPR 相关的消息
"""
import json
import time
import threading
import websocket

# pylint:disable=f-string-without-interpolation, unused-argument

def test_vpr_simple_check(base_url, real_token, vpr_audio_data_params, real_audio_file):
    """简单测试：检查是否收到 VPR 相关消息"""
    messages_received = []
    finished = threading.Event()
    vpr_messages = []
    iat_messages = []

    def on_message(ws, message):
        data = json.loads(message)
        messages_received.append(data)
        action = data.get('action')

        if action == 'connected':
            print("\n[TEST] 发送 start 指令（包含 VPR 配置）")
            ws.send(json.dumps(vpr_audio_data_params))

        elif action == 'started':
            print("[TEST] 会话已创建，发送音频")
            send_audio_data(ws, real_audio_file)
            # 发送完音频后等待一下再结束
            time.sleep(2)
            ws.send(json.dumps({"action": "end"}))

        elif action == 'result':
            result_data = data.get('data', {})
            sub_type = result_data.get('sub', 'unknown')
            
            print(f"[TEST] 收到 result 消息，sub={sub_type}")
            
            if sub_type == 'vpr':
                vpr_messages.append(result_data)
                print(f"[TEST] ✅ 收到 VPR 消息: {json.dumps(result_data, ensure_ascii=False)}")
            elif sub_type == 'iat':
                iat_messages.append(result_data)
                if result_data.get('is_last'):
                    text = result_data.get('text', '')
                    print(f"[TEST] IAT 识别结果: {text}")

        elif action == 'finish':
            print("[TEST] 会话结束")
            finished.set()

    def send_audio_data(ws, audio_file):
        import wave
        with wave.open(audio_file, 'rb') as wav_file:
            audio_data = wav_file.readframes(wav_file.getnframes())
        
        chunk_size = 1280
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
            time.sleep(0.04)

    headers = {'Authorization': f'Bearer {real_token}'}
    ws = websocket.WebSocketApp(
        base_url,
        header=headers,
        on_message=on_message,
        on_error=lambda ws, error: print(f"[TEST] 错误: {error}"),
        on_close=lambda ws, code, msg: finished.set()
    )

    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

    assert finished.wait(timeout=30), "超时"
    
    print(f"\n[TEST] ========== 测试结果 ==========")
    print(f"[TEST] 总消息数: {len(messages_received)}")
    print(f"[TEST] VPR 消息数: {len(vpr_messages)}")
    print(f"[TEST] IAT 消息数: {len(iat_messages)}")
    
    if len(vpr_messages) > 0:
        print(f"[TEST] ✅ 收到了 VPR 消息")
        for i, msg in enumerate(vpr_messages):
            print(f"[TEST] VPR 消息 {i+1}: {json.dumps(msg, ensure_ascii=False, indent=2)}")
    else:
        print(f"[TEST] ❌ 没有收到 VPR 消息")
        print(f"[TEST] 这可能意味着：")
        print(f"[TEST]   1. VPR 功能未启用")
        print(f"[TEST]   2. VPR 配置不正确")
        print(f"[TEST]   3. 需要特殊权限或配置")
    
    print(f"[TEST] ================================\n")
