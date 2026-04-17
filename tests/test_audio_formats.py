"""
测试不同音频格式的支持
使用 audio.pcm, audio.speex, audio.ico 三种格式
"""
import json
import time
import threading
import pytest
import websocket

# pylint:disable=f-string-without-interpolation, unused-argument

class TestPCMFormat:
    """测试 PCM (raw) 格式"""

    def test_pcm_format_recognition(
        self, 
        base_url, 
        real_token, 
        pcm_start_params, 
        pcm_audio_file
    ):
        """测试使用 PCM 格式进行识别"""
        finished = threading.Event()
        messages_received = []

        def on_open(ws):
            print("\n[PCM] 连接已建立")

        def on_message(ws, message):
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            print(f"[PCM] 收到消息: {action}")

            if action == 'connected':
                print("[PCM] 发送 start 指令")
                ws.send(json.dumps(pcm_start_params))

            elif action == 'started':
                print("[PCM] 开始发送 PCM 音频数据")
                # 读取并发送 PCM 音频文件
                with open(pcm_audio_file, 'rb') as f:
                    chunk_size = 1280  # 40ms
                    chunk_count = 0
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                        chunk_count += 1
                        time.sleep(0.04)
                
                print(f"[PCM] 发送了 {chunk_count} 个数据块")
                print("[PCM] 发送 end 指令")
                ws.send(json.dumps({"action": "end"}))

            elif action == 'result':
                result_data = data.get('data', {})
                if result_data.get('sub') == 'iat':
                    text = result_data.get('text', '')
                    print(f"[PCM] 识别结果: {text}")

            elif action == 'finish':
                print("[PCM] 会话结束")
                finished.set()

        def on_error(ws, error):
            print(f"[PCM] 错误: {error}")

        def on_close(ws, close_status_code, close_msg):
            print("[PCM] 连接已关闭")
            finished.set()

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=30), "[PCM] 识别流程超时"

        # 验证收到了识别结果
        actions = [msg.get('action') for msg in messages_received]
        assert 'connected' in actions
        assert 'started' in actions
        assert 'finish' in actions


class TestSpeexFormat:
    """测试 Speex 格式"""

    def test_speex_format_recognition(
        self, 
        base_url, 
        real_token, 
        speex_start_params, 
        speex_audio_file
    ):
        """测试使用 Speex 格式进行识别"""
        finished = threading.Event()
        messages_received = []

        def on_open(ws):
            print("\n[Speex] 连接已建立")

        def on_message(ws, message):
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            print(f"[Speex] 收到消息: {action}")

            if action == 'connected':
                print("[Speex] 发送 start 指令")
                ws.send(json.dumps(speex_start_params))

            elif action == 'started':
                print("[Speex] 开始发送 Speex 音频数据")
                # 读取并发送 Speex 音频文件
                with open(speex_audio_file, 'rb') as f:
                    chunk_size = 70  # Speex 数据块大小
                    chunk_count = 0
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                        chunk_count += 1
                        time.sleep(0.04)
                
                print(f"[Speex] 发送了 {chunk_count} 个数据块")
                print("[Speex] 发送 end 指令")
                ws.send(json.dumps({"action": "end"}))

            elif action == 'result':
                result_data = data.get('data', {})
                if result_data.get('sub') == 'iat':
                    text = result_data.get('text', '')
                    print(f"[Speex] 识别结果: {text}")

            elif action == 'finish':
                print("[Speex] 会话结束")
                finished.set()

        def on_error(ws, error):
            print(f"[Speex] 错误: {error}")

        def on_close(ws, close_status_code, close_msg):
            print("[Speex] 连接已关闭")
            finished.set()

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=30), "[Speex] 识别流程超时"

        # 验证收到了识别结果
        actions = [msg.get('action') for msg in messages_received]
        assert 'connected' in actions
        assert 'started' in actions
        assert 'finish' in actions


class TestICOFormat:
    """测试 ICO 格式"""

    def test_ico_format_recognition(
        self, 
        base_url, 
        real_token, 
        ico_start_params, 
        ico_audio_file
    ):
        """测试使用 ICO 格式进行识别"""
        finished = threading.Event()
        messages_received = []

        def on_open(ws):
            print("\n[ICO] 连接已建立")

        def on_message(ws, message):
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            print(f"[ICO] 收到消息: {action}")

            if action == 'connected':
                print("[ICO] 发送 start 指令")
                ws.send(json.dumps(ico_start_params))

            elif action == 'started':
                print("[ICO] 开始发送 ICO 音频数据")
                # 读取并发送 ICO 音频文件
                with open(ico_audio_file, 'rb') as f:
                    chunk_size = 640  # ICO 数据块大小
                    chunk_count = 0
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                        chunk_count += 1
                        time.sleep(0.04)
                
                print(f"[ICO] 发送了 {chunk_count} 个数据块")
                print("[ICO] 发送 end 指令")
                ws.send(json.dumps({"action": "end"}))

            elif action == 'result':
                result_data = data.get('data', {})
                if result_data.get('sub') == 'iat':
                    text = result_data.get('text', '')
                    print(f"[ICO] 识别结果: {text}")

            elif action == 'finish':
                print("[ICO] 会话结束")
                finished.set()

        def on_error(ws, error):
            print(f"[ICO] 错误: {error}")

        def on_close(ws, close_status_code, close_msg):
            print("[ICO] 连接已关闭")
            finished.set()

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=30), "[ICO] 识别流程超时"

        # 验证收到了识别结果
        actions = [msg.get('action') for msg in messages_received]
        assert 'connected' in actions
        assert 'started' in actions
        assert 'finish' in actions


class TestAudioFormatComparison:
    """比较不同音频格式的测试"""

    def test_load_all_audio_formats(
        self, 
        pcm_audio_data, 
        speex_audio_data, 
        ico_audio_data
    ):
        """测试加载所有音频格式"""
        print("\n音频格式对比:")
        print(f"  PCM:   {len(pcm_audio_data)} bytes")
        print(f"  Speex: {len(speex_audio_data)} bytes")
        print(f"  ICO:   {len(ico_audio_data)} bytes")
        
        assert len(pcm_audio_data) > 0
        assert len(speex_audio_data) > 0
        assert len(ico_audio_data) > 0

    def test_audio_chunks_count(
        self, 
        pcm_audio_chunks, 
        speex_audio_chunks, 
        ico_audio_chunks
    ):
        """测试不同格式的数据块数量"""
        print("\n数据块数量对比:")
        print(f"  PCM:   {len(pcm_audio_chunks)} 块 (1280 bytes/块)")
        print(f"  Speex: {len(speex_audio_chunks)} 块 (70 bytes/块)")
        print(f"  ICO:   {len(ico_audio_chunks)} 块 (640 bytes/块)")
        
        assert len(pcm_audio_chunks) > 0
        assert len(speex_audio_chunks) > 0
        assert len(ico_audio_chunks) > 0


@pytest.mark.parametrize("format_name,audio_file_fixture,start_params_fixture,chunk_size", [
    ("PCM", "pcm_audio_file", "pcm_start_params", 1280),
    ("Speex", "speex_audio_file", "speex_start_params", 70),
    ("ICO", "ico_audio_file", "ico_start_params", 640),
])
class TestAllFormatsParametrized:
    """使用参数化测试所有格式"""

    def test_format_session_creation(
        self, 
        base_url, 
        real_token, 
        format_name,
        audio_file_fixture,
        start_params_fixture,
        chunk_size,
        request
    ):
        """参数化测试：创建不同格式的会话"""
        start_params = request.getfixturevalue(start_params_fixture)
        
        session_started = threading.Event()
        received_data = {}

        def on_open(ws):
            ws.send(json.dumps(start_params))

        def on_message(ws, message):
            data = json.loads(message)
            if data.get('action') == 'started':
                received_data['response'] = data
                session_started.set()
                ws.close()

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert session_started.wait(timeout=10), f"[{format_name}] 会话创建超时"
        assert received_data['response']['action'] == 'started'
        print(f"\n[{format_name}] 会话创建成功，chunk_size={chunk_size}")
