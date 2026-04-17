"""
临时调试测试：查看 VPR 消息的完整内容
"""
import json
import time
import threading
import websocket


# pylint:disable=f-string-without-interpolation, unused-argument
def test_vpr_debug(base_url, real_token, vpr_audio_data_params, real_audio_file, xueyan_audio_file):
    """调试测试：查看所有消息的完整内容"""
    messages_received = []
    finished = threading.Event()
    rounds_completed = 0

    def on_open(ws):
        print("\n[DEBUG] 连接已建立")

    def on_message(ws, message):
        nonlocal rounds_completed
        data = json.loads(message)
        messages_received.append(data)
        action = data.get('action')
        
        # 打印所有消息的完整内容
        print(f"\n[DEBUG] ========== 收到消息 ==========")
        print(f"[DEBUG] Action: {action}")
        print(f"[DEBUG] 完整消息: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print(f"[DEBUG] ================================\n")

        if action == 'connected':
            print("[DEBUG] 发送 start 指令")
            print(f"[DEBUG] Start 参数: {json.dumps(vpr_audio_data_params, ensure_ascii=False, indent=2)}")
            ws.send(json.dumps(vpr_audio_data_params))

        elif action == 'started':
            print(f"[DEBUG] 会话已创建，发送第1轮音频")
            send_audio_data(ws, real_audio_file)

        elif action == 'result':
            result_data = data.get('data', {})
            sub_type = result_data.get('sub', 'unknown')
            
            if sub_type == 'iat' and result_data.get('is_last'):
                rounds_completed += 1
                text = result_data.get('text', '')
                print(f"[DEBUG] 第 {rounds_completed} 轮识别完成: {text}")

                if rounds_completed < 2:
                    print(f"[DEBUG] 发送第2轮音频")
                    time.sleep(0.5)
                    send_audio_data(ws, xueyan_audio_file)
                else:
                    print("[DEBUG] 发送 end 指令")
                    ws.send(json.dumps({"action": "end"}))

        elif action == 'finish':
            print("[DEBUG] 会话结束")
            finished.set()

    def send_audio_data(ws, audio_file):
        """发送音频数据"""
        import wave
        
        if audio_file.endswith('.wav'):
            with wave.open(audio_file, 'rb') as wav_file:
                audio_data = wav_file.readframes(wav_file.getnframes())
        else:
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
        
        print(f"[DEBUG] 发送音频: {audio_file}, 大小: {len(audio_data)} bytes")
        
        chunk_size = 1280
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
            time.sleep(0.04)

    headers = {'Authorization': f'Bearer {real_token}'}
    ws = websocket.WebSocketApp(
        f"{base_url}/v2/asr",
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=lambda ws, error: print(f"[DEBUG] 错误: {error}"),
        on_close=lambda ws, code, msg: finished.set()
    )

    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

    # 等待完成
    assert finished.wait(timeout=60), "[DEBUG] 超时"
    
    print(f"\n[DEBUG] 总共收到 {len(messages_received)} 条消息")
    print(f"[DEBUG] 完成 {rounds_completed} 轮识别")
