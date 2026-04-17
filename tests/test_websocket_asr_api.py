"""
WebSocket ASR API Test Suite
测试 WebSocket 语音识别接口的各种场景 - 使用真实连接
"""
import json
import logging
import time
import threading
import pytest
import websocket

# 配置 logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# pylint:disable=unused-argument

class TestWebSocketConnection:
    """测试 WebSocket 连接相关功能"""

    def test_connection_with_valid_token(self, base_url, real_token):
        """测试使用有效 token 建立连接"""
        connected = threading.Event()
        error_occurred = threading.Event()
        received_data = {}

        def on_open(ws):
            logger.info("WebSocket 连接已建立")

        def on_message(ws, message):
            data = json.loads(message)
            received_data['response'] = data
            if data.get('action') == 'connected':
                connected.set()
            ws.close()

        def on_error(ws, error):
            logger.info("连接错误: %s", error)
            error_occurred.set()

        def on_close(ws, close_status_code, close_msg):
            logger.info("连接已关闭")

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

        # 等待连接或错误
        assert connected.wait(timeout=10), "连接超时"
        assert not error_occurred.is_set(), "连接过程中发生错误"
        assert received_data['response']['action'] == 'connected'
        assert received_data['response']['code'] == '0'

    def test_connection_with_invalid_token(self, base_url):
        """测试使用无效 token 连接失败"""
        error_occurred = threading.Event()
        received_data = {}

        def on_message(ws, message):
            data = json.loads(message)
            received_data['response'] = data
            if data.get('action') == 'error':
                error_occurred.set()
            ws.close()

        def on_error(ws, error):
            error_occurred.set()

        headers = {'Authorization': 'Bearer invalid_token_12345'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_message=on_message,
            on_error=on_error
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # 等待错误发生
        assert error_occurred.wait(timeout=10), "应该收到认证错误"


class TestSessionCreation:
    """测试会话创建相关功能"""

    def test_create_session_with_default_params(self, base_url, real_token, default_start_params):
        """测试使用默认参数创建会话"""
        session_started = threading.Event()
        received_data = {}

        def on_open(ws):
            # 发送会话创建指令
            ws.send(json.dumps(default_start_params))

        def on_message(ws, message):
            data = json.loads(message)
            logger.info("收到消息: %s", json.dumps(data, ensure_ascii=False))
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

        assert session_started.wait(timeout=30), "会话创建超时"
        assert received_data['response']['action'] == 'started'
        assert received_data['response']['code'] == '0'
        assert 'sid' in received_data['response']

    def test_create_session_with_continuous_mode(self, base_url, real_token, continuous_mode_params):
        """测试创建连续识别模式会话"""
        session_started = threading.Event()
        received_data = {}

        def on_open(ws):
            ws.send(json.dumps(continuous_mode_params))

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

        assert session_started.wait(timeout=10), "连续模式会话创建超时"
        assert received_data['response']['action'] == 'started'

    def test_create_session_with_custom_hotwords(self, base_url, real_token):
        """测试使用会话级个性化热词创建会话"""
        session_started = threading.Event()
        received_data = {}

        params = {
            "action": "start",
            "params": {
                "data_type": "audio",
                "aue": "raw",
                "asr_properties": {
                    "ent": "home-va",
                    "dhw": "dhw=utf-8;你好|大家|测试"
                }
            }
        }

        def on_open(ws):
            ws.send(json.dumps(params))

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

        assert session_started.wait(timeout=10), "热词会话创建超时"
        assert received_data['response']['action'] == 'started'


class TestSingleRecognitionWorkflow:
    """测试单次识别完整流程"""

    def test_complete_single_recognition_flow(self, base_url, real_token, default_start_params, real_audio_file):
        """测试单次识别的完整交互流程"""
        messages_received = []
        finished = threading.Event()

        def on_open(ws):
            logger.info("1. 连接已建立")

        def on_message(ws, message):
            data = json.loads(message)
            messages_received.append(data)
            logger.info("收到消息: %s", json.dumps(data, ensure_ascii=False))

            if data.get('action') == 'connected':
                logger.info("2. 收到 connected，发送 start 指令")
                ws.send(json.dumps(default_start_params))

            elif data.get('action') == 'started':
                logger.info("3. 收到 started，开始发送音频数据")
                # 读取并发送音频文件
                with open(real_audio_file, 'rb') as f:
                    chunk_size = 1280  # 40ms 的数据量
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                        time.sleep(0.04)  # 模拟实时音频流

                logger.info("4. 音频发送完毕，发送 end 指令")
                ws.send(json.dumps({"action": "end"}))

            elif data.get('action') == 'result':
                logger.info("5. 收到识别结果: %s", data.get('data', {}).get('text', ''))

            elif data.get('action') == 'finish':
                logger.info("6. 收到 finish，会话结束")
                finished.set()

        def on_error(ws, error):
            logger.info("错误: %s", error)

        def on_close(ws, close_status_code, close_msg):
            logger.info("连接已关闭")
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

        # 等待完成
        assert finished.wait(timeout=30), "识别流程超时"

        # 验证消息序列
        actions = [msg.get('action') for msg in messages_received]
        assert 'connected' in actions
        assert 'started' in actions
        assert 'finish' in actions

        # 检查是否有识别结果
        result_messages = [msg for msg in messages_received if msg.get('action') == 'result']
        if result_messages:
            iat_results = [msg for msg in result_messages if msg.get('data', {}).get('sub') == 'iat']
            if iat_results:
                assert len(iat_results) > 0, "应该收到至少一个识别结果"


class TestContinuousRecognitionWorkflow:
    """测试连续对话模式完整流程"""

    def test_continuous_recognition_multiple_rounds(self, base_url, real_token, continuous_mode_params, real_audio_file):
        """测试连续对话模式多轮识别"""
        messages_received = []
        finished = threading.Event()
        rounds_completed = 0

        def on_open(ws):
            logger.info("连接已建立")

        def on_message(ws, message):
            nonlocal rounds_completed
            data = json.loads(message)
            messages_received.append(data)
            logger.info("收到消息: %s", json.dumps(data, ensure_ascii=False))

            if data.get('action') == 'connected':
                logger.info("发送连续模式 start 指令")
                ws.send(json.dumps(continuous_mode_params))

            elif data.get('action') == 'started':
                logger.info("会话已创建，开始第 %s 轮识别", rounds_completed + 1)
                # 发送第一轮音频
                send_audio_data(ws, real_audio_file)

            elif data.get('action') == 'result':
                result_data = data.get('data', {})
                if result_data.get('sub') == 'iat' and result_data.get('is_last'):
                    rounds_completed += 1
                    logger.info("第 %s 轮识别完成: %s", rounds_completed, result_data.get('text', ''))

                    if rounds_completed < 2:
                        # 继续发送第二轮音频
                        logger.info("开始第 %s 轮识别", rounds_completed + 1)
                        time.sleep(0.5)
                        send_audio_data(ws, real_audio_file)
                    else:
                        # 两轮完成，发送结束指令
                        logger.info("发送 end 指令")
                        ws.send(json.dumps({"action": "end"}))

            elif data.get('action') == 'finish':
                logger.info("会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            """发送音频数据"""
            with open(audio_file, 'rb') as f:
                chunk_size = 1280
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                    time.sleep(0.04)

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # 等待完成
        assert finished.wait(timeout=120), "连续识别流程超时"

        # 验证收到多轮识别结果
        result_messages = [msg for msg in messages_received if msg.get('action') == 'result']
        iat_results = [msg for msg in result_messages if msg.get('data', {}).get('sub') == 'iat']
        logger.info("总共收到 %s 个识别结果", len(iat_results))

    def test_continuous_recognition_vpr_audio_data(self, base_url, real_token, vpr_audio_data_params, real_audio_file, xueyan_audio_file):
        """测试使用音频数据进行声纹识别：杨俊的声纹应该匹配，雪艳的声纹不匹配"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0  # 记录发送了几次音频
        round_vad = {}  # 记录每轮的 VAD 消息
        round_iat = {}  # 记录每轮的 IAT 消息
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0  # 当前轮次
        total_rounds = 2  # 总轮次
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Audio Data] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Audio Data] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Audio Data] 发送连续模式 start 指令（包含杨俊的声纹音频数据）")
                ws.send(json.dumps(vpr_audio_data_params))

            elif action == 'started':
                logger.info("[VPR Audio Data] 会话已创建")
                logger.info("[VPR Audio Data] 第1轮：发送'今天天气怎么样.wav'（预期：有IAT识别结果，声纹匹配）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                # 记录 VAD 消息
                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Audio Data] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Audio Data] 第%s轮收到 VAD END", round_num)
                        # 捕获当前轮次的快照，避免竞态条件
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                # 记录 VPR 结果
                if sub_type == 'vpr':
                    vpr_result = result_data.get('vpr_result', {})
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Audio Data] 第%s轮 VPR 结果: %s", round_num, vpr_result)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Audio Data] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

                # 记录 IAT 识别结果
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Audio Data] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

            elif action == 'finish':
                logger.info("[VPR Audio Data] 会话结束")
                finished.set()

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    # 发送下一轮音频
                    check_and_send_next(ws)
                else:
                    # 最后一轮，发送 end 指令
                    end_session(ws)

        def send_audio_data(ws, audio_file):
            """发送音频数据（WAV格式，需要转换为PCM）"""
            import wave

            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Audio Data] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def check_and_send_next(ws):
            """检查并发送下一个音频"""
            nonlocal audio_sent_count, current_round
            # 发送第二个音频
            with state_lock:
                current_round = 2
                audio_sent_count += 1
            logger.info("[VPR Audio Data] 第2轮：发送'全双工-雪艳.wav'（预期：有VAD但没有IAT，声纹不匹配）")
            send_audio_data(ws, xueyan_audio_file)

        def end_session(ws):
            """结束会话"""
            logger.info("[VPR Audio Data] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Audio Data] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # 等待完成
        assert finished.wait(timeout=120), "[VPR Audio Data] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Audio Data] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))
        
        # 断言：第1轮应该有 IAT 识别结果（声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Audio Data] ✅ 第1轮有 IAT 结果: %s", round_iat[1])
        
        # 断言：第1轮应该有 vpr_info 帧，且 gender="male", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'male', f"第1轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Audio Data] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])
        
        # 断言：第2轮应该有 VAD 但没有 IAT（声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Audio Data] ✅ 第2轮有 VAD: %s", round_vad[2])
        
        # 第2轮不应该有 IAT
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Audio Data] ✅ 第2轮没有 IAT（声纹不匹配）")
        
        # 断言：第2轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'female', f"第2轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data_2['gender']}'"
        assert vpr_info_data_2['age'] == 'adult', f"第2轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data_2['age']}'"
        logger.info("[VPR Audio Data] ✅ 第2轮有 vpr_info: gender=%s, age=%s", vpr_info_data_2['gender'], vpr_info_data_2['age'])

    def test_continuous_recognition_vpr_feature_id(self, base_url, real_token, vpr_feature_id_params, vpr_feature, real_audio_file, xueyan_audio_file):
        """测试使用特征ID进行声纹识别：杨俊的声纹应该匹配，雪艳的声纹不匹配"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0
        round_vad = {}
        round_iat = {}
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0
        total_rounds = 2  # 总轮次
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Feature ID] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Feature ID] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Feature ID] 发送连续模式 start 指令（使用特征ID: %s）", vpr_feature['id'])
                ws.send(json.dumps(vpr_feature_id_params))

            elif action == 'started':
                logger.info("[VPR Feature ID] 会话已创建")
                logger.info("[VPR Feature ID] 第1轮：发送'今天天气怎么样.wav'（预期：有IAT识别结果，声纹匹配）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Feature ID] 第%s轮收到 VAD END", round_num)
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                if sub_type == 'vpr':
                    vpr_result = result_data.get('vpr_result', {})
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID] 第%s轮 VPR 结果: %s", round_num, vpr_result)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Feature ID] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

            elif action == 'finish':
                logger.info("[VPR Feature ID] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            import wave
            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Feature ID] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    check_and_send_next(ws)
                else:
                    end_session(ws)

        def check_and_send_next(ws):
            nonlocal audio_sent_count, current_round
            with state_lock:
                current_round = 2
                audio_sent_count += 1
            logger.info("[VPR Feature ID] 第2轮：发送'全双工-雪艳.wav'（预期：有VAD但没有IAT，声纹不匹配）")
            send_audio_data(ws, xueyan_audio_file)

        def end_session(ws):
            logger.info("[VPR Feature ID] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Feature ID] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[VPR Feature ID] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Feature ID] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))
        
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Feature ID] ✅ 第1轮有 IAT 结果: %s", round_iat[1])
        
        # 断言：第1轮应该有 vpr_info 帧，且 gender="male", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'male', f"第1轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Feature ID] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])
        
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Feature ID] ✅ 第2轮有 VAD: %s", round_vad[2])
        
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Feature ID] ✅ 第2轮没有 IAT（声纹不匹配）")
        
        # 断言：第2轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'female', f"第2轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data_2['gender']}'"
        assert vpr_info_data_2['age'] == 'adult', f"第2轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data_2['age']}'"
        logger.info("[VPR Feature ID] ✅ 第2轮有 vpr_info: gender=%s, age=%s", vpr_info_data_2['gender'], vpr_info_data_2['age'])

    def test_continuous_recognition_vpr_feature_id_only(self, base_url, real_token, vpr_feature_id_only_params, vpr_feature, real_audio_file, xueyan_audio_file):
        """测试只传feature_id不传group_id的声纹识别"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0  # 记录发送了几次音频
        round_vad = {}  # 记录每轮的 VAD 消息
        round_iat = {}  # 记录每轮的 IAT 消息
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0  # 当前轮次
        total_rounds = 2  # 总轮次
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Feature ID Only] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Feature ID Only] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Feature ID Only] 发送 start 指令（只传 feature_id: %s）", vpr_feature['id'])
                ws.send(json.dumps(vpr_feature_id_only_params))

            elif action == 'started':
                logger.info("[VPR Feature ID Only] 会话已创建")
                logger.info("[VPR Feature ID Only] 第1轮：发送'今天天气怎么样.wav'（预期：有IAT识别结果，声纹匹配）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                # 记录 VAD 消息
                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID Only] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Feature ID Only] 第%s轮收到 VAD END", round_num)
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                # 记录 VPR 结果
                if sub_type == 'vpr':
                    vpr_result = result_data.get('vpr_result', {})
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID Only] 第%s轮 VPR 结果: %s", round_num, vpr_result)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID Only] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

                # 记录 IAT 识别结果
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Feature ID Only] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

            elif action == 'finish':
                logger.info("[VPR Feature ID Only] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            """发送音频数据（WAV格式，需要转换为PCM）"""
            import wave

            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Feature ID Only] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    check_and_send_next(ws)
                else:
                    end_session(ws)

        def check_and_send_next(ws):
            """检查并发送下一个音频或结束"""
            nonlocal audio_sent_count, current_round
            with state_lock:
                current_round = 2
                audio_sent_count += 1
            logger.info("[VPR Feature ID Only] 第2轮：发送'全双工-雪艳.wav'（预期：有VAD但没有IAT，声纹不匹配）")
            send_audio_data(ws, xueyan_audio_file)

        def end_session(ws):
            """结束会话"""
            logger.info("[VPR Feature ID Only] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Feature ID Only] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # 等待完成
        assert finished.wait(timeout=120), "[VPR Feature ID Only] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Feature ID Only] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))
        
        # 断言：第1轮应该有 IAT 识别结果（声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Feature ID Only] ✅ 第1轮有 IAT 结果: %s", round_iat[1])
        
        # 断言：第1轮应该有 vpr_info 帧，且 gender="male", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'male', f"第1轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Feature ID Only] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])
        
        # 断言：第2轮应该有 VAD 但没有 IAT（声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Feature ID Only] ✅ 第2轮有 VAD: %s", round_vad[2])
        
        # 第2轮不应该有 IAT
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Feature ID Only] ✅ 第2轮没有 IAT（声纹不匹配）")
        
        # 断言：第2轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'female', f"第2轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data_2['gender']}'"
        assert vpr_info_data_2['age'] == 'adult', f"第2轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data_2['age']}'"
        logger.info("[VPR Feature ID Only] ✅ 第2轮有 vpr_info: gender=%s, age=%s", vpr_info_data_2['gender'], vpr_info_data_2['age'])

    def test_continuous_recognition_vpr_group_id_only(self, base_url, real_token, vpr_group_id_only_params, vpr_group, real_audio_file, xueyan_audio_file):
        """测试只传group_id不传feature_id的声纹识别"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0  # 记录发送了几次音频
        round_vad = {}  # 记录每轮的 VAD 消息
        round_iat = {}  # 记录每轮的 IAT 消息
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0  # 当前轮次
        total_rounds = 2  # 总轮次
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Group ID Only] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Group ID Only] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Group ID Only] 发送 start 指令（只传 group_id: %s）", vpr_group['id'])
                ws.send(json.dumps(vpr_group_id_only_params))

            elif action == 'started':
                logger.info("[VPR Group ID Only] 会话已创建")
                logger.info("[VPR Group ID Only] 第1轮：发送'今天天气怎么样.wav'（预期：有IAT识别结果，声纹匹配）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                # 记录 VAD 消息
                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Group ID Only] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Group ID Only] 第%s轮收到 VAD END", round_num)
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                # 记录 VPR 结果
                if sub_type == 'vpr':
                    vpr_result = result_data.get('vpr_result', {})
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Group ID Only] 第%s轮 VPR 结果: %s", round_num, vpr_result)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Group ID Only] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

                # 记录 IAT 识别结果
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Group ID Only] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

            elif action == 'finish':
                logger.info("[VPR Group ID Only] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            """发送音频数据（WAV格式，需要转换为PCM）"""
            import wave

            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Group ID Only] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    check_and_send_next(ws)
                else:
                    end_session(ws)

        def check_and_send_next(ws):
            """检查并发送下一个音频或结束"""
            nonlocal audio_sent_count, current_round
            with state_lock:
                current_round = 2
                audio_sent_count += 1
            logger.info("[VPR Group ID Only] 第2轮：发送'全双工-雪艳.wav'（预期：有VAD但没有IAT，声纹不匹配）")
            send_audio_data(ws, xueyan_audio_file)

        def end_session(ws):
            """结束会话"""
            logger.info("[VPR Group ID Only] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Group ID Only] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # 等待完成
        assert finished.wait(timeout=120), "[VPR Group ID Only] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Group ID Only] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))
        
        # 断言：第1轮应该有 IAT 识别结果（声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Group ID Only] ✅ 第1轮有 IAT 结果: %s", round_iat[1])
        
        # 断言：第1轮应该有 vpr_info 帧，且 gender="male", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'male', f"第1轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Group ID Only] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])
        
        # 断言：第2轮应该有 VAD 但没有 IAT（声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Group ID Only] ✅ 第2轮有 VAD: %s", round_vad[2])
        
        # 第2轮不应该有 IAT
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Group ID Only] ✅ 第2轮没有 IAT（声纹不匹配）")
        
        # 断言：第2轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'female', f"第2轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data_2['gender']}'"
        assert vpr_info_data_2['age'] == 'adult', f"第2轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data_2['age']}'"
        logger.info("[VPR Group ID Only] ✅ 第2轮有 vpr_info: gender=%s, age=%s", vpr_info_data_2['gender'], vpr_info_data_2['age'])

    def test_continuous_recognition_vpr_audio_data_female(self, base_url, real_token, vpr_female_audio_data_params, female_audio_file, peijun_audio_file):
        """测试使用音频数据进行声纹识别：程梅芳的声纹应该匹配，培峻的声纹不匹配"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0  # 记录发送了几次音频
        round_vad = {}  # 记录每轮的 VAD 消息
        round_iat = {}  # 记录每轮的 IAT 消息
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0  # 当前轮次
        total_rounds = 2  # 总轮次
        state_lock = threading.RLock()  # 保护共享状态的锁


        def on_open(ws):
            logger.info("\n[VPR Audio Data] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Audio Data] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Audio Data] 发送连续模式 start 指令（包含杨俊的声纹音频数据）")
                ws.send(json.dumps(vpr_female_audio_data_params))

            elif action == 'started':
                logger.info("[VPR Audio Data] 会话已创建")
                logger.info("[VPR Audio Data] 第1轮：发送'全双工-程梅芳.wav'（预期：有IAT识别结果，声纹匹配）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, female_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                # 记录 VAD 消息
                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Audio Data] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Audio Data] 第%s轮收到 VAD END", round_num)
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                # 记录 VPR 结果
                if sub_type == 'vpr':
                    vpr_result = result_data.get('vpr_result', {})
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Audio Data] 第%s轮 VPR 结果: %s", round_num, vpr_result)

                # 记录 IAT 识别结果
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Audio Data] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Audio Data] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

            elif action == 'finish':
                logger.info("[VPR Audio Data] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            """发送音频数据（WAV格式，需要转换为PCM）"""
            import wave

            if audio_file.endswith('.wav'):
                logger.info(audio_file)
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Audio Data] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    check_and_send_next(ws)
                else:
                    end_session(ws)

        def check_and_send_next(ws):
            """检查并发送下一个音频或结束"""
            nonlocal audio_sent_count, current_round
            with state_lock:
                current_round = 2
                audio_sent_count += 1
            logger.info("[VPR Audio Data] 第2轮：发送'全双工-黄培峻.wav'（预期：有VAD但没有IAT，声纹不匹配）")
            send_audio_data(ws, peijun_audio_file)

        def end_session(ws):
            """结束会话"""
            logger.info("[VPR Audio Data] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Audio Data] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # 等待完成
        assert finished.wait(timeout=120), "[VPR Audio Data] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Audio Data] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))

        # 断言：第1轮应该有 IAT 识别结果（声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Audio Data] ✅ 第1轮有 IAT 结果: %s", round_iat[1])

        # 断言：第1轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'female', f"第1轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Audio Data] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])

        # 断言：第2轮应该有 VAD 但没有 IAT（声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Audio Data] ✅ 第2轮有 VAD: %s", round_vad[2])

        # 第2轮不应该有 IAT
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Audio Data] ✅ 第2轮没有 IAT（声纹不匹配）")

        # 断言：第2轮应该有 vpr_info 帧，且 gender="male"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'male', f"第2轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data_2['gender']}'"
        logger.info("[VPR Audio Data] ✅ 第2轮有 vpr_info: gender=%s", vpr_info_data_2['gender'])

    def test_continuous_recognition_vpr_feature_id_female(self, base_url, real_token, vpr_female_feature_id_params, vpr_female_feature, female_audio_file, peijun_audio_file):
        """测试使用特征ID进行声纹识别：程梅芳的声纹应该匹配，培峻的声纹不匹配"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0
        round_vad = {}
        round_iat = {}
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0
        total_rounds = 2  # 总轮次
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Feature ID] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Feature ID] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Feature ID] 发送连续模式 start 指令（使用特征ID: %s）", vpr_female_feature['id'])
                ws.send(json.dumps(vpr_female_feature_id_params))

            elif action == 'started':
                logger.info("[VPR Feature ID] 会话已创建")
                logger.info("[VPR Feature ID] 第1轮：发送'全双工-程梅芳.wav'（预期：有IAT识别结果，声纹匹配）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, female_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Feature ID] 第%s轮收到 VAD END", round_num)
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                if sub_type == 'vpr':
                    vpr_result = result_data.get('vpr_result', {})
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID] 第%s轮 VPR 结果: %s", round_num, vpr_result)

                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Feature ID] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

            elif action == 'finish':
                logger.info("[VPR Feature ID] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            import wave
            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Feature ID] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    check_and_send_next(ws)
                else:
                    end_session(ws)

        def check_and_send_next(ws):
            nonlocal audio_sent_count, current_round
            with state_lock:
                current_round = 2
                audio_sent_count += 1
            logger.info("[VPR Feature ID] 第2轮：发送'全双工-黄培峻.wav'（预期：有VAD但没有IAT，声纹不匹配）")
            send_audio_data(ws, peijun_audio_file)

        def end_session(ws):
            logger.info("[VPR Feature ID] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Feature ID] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[VPR Feature ID] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Feature ID] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))

        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Feature ID] ✅ 第1轮有 IAT 结果: %s", round_iat[1])

        # 断言：第1轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'female', f"第1轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Feature ID] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])

        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Feature ID] ✅ 第2轮有 VAD: %s", round_vad[2])

        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Feature ID] ✅ 第2轮没有 IAT（声纹不匹配）")

        # 断言：第2轮应该有 vpr_info 帧，且 gender="male"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'male', f"第2轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data_2['gender']}'"
        logger.info("[VPR Feature ID] ✅ 第2轮有 vpr_info: gender=%s", vpr_info_data_2['gender'])

    def test_continuous_recognition_vpr_feature_id_only_female(self, base_url, real_token, vpr_female_feature_id_only_params, vpr_female_feature, female_audio_file, peijun_audio_file):
        """测试只传feature_id不传group_id的声纹识别"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0  # 记录发送了几次音频
        round_vad = {}  # 记录每轮的 VAD 消息
        round_iat = {}  # 记录每轮的 IAT 消息
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0  # 当前轮次
        total_rounds = 2  # 总轮次
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Feature ID Only] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Feature ID Only] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Feature ID Only] 发送 start 指令（只传 feature_id: %s）", vpr_female_feature['id'])
                ws.send(json.dumps(vpr_female_feature_id_only_params))

            elif action == 'started':
                logger.info("[VPR Feature ID Only] 会话已创建")
                logger.info("[VPR Feature ID Only] 第1轮：发送'全双工-程梅芳.wav'（预期：有IAT识别结果，声纹匹配）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, female_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                # 记录 VAD 消息
                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID Only] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Feature ID Only] 第%s轮收到 VAD END", round_num)
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                # 记录 VPR 结果
                if sub_type == 'vpr':
                    vpr_result = result_data.get('vpr_result', {})
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID Only] 第%s轮 VPR 结果: %s", round_num, vpr_result)

                # 记录 IAT 识别结果
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Feature ID Only] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Feature ID Only] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

            elif action == 'finish':
                logger.info("[VPR Feature ID Only] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            """发送音频数据（WAV格式，需要转换为PCM）"""
            import wave

            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Feature ID Only] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    check_and_send_next(ws)
                else:
                    end_session(ws)

        def check_and_send_next(ws):
            """检查并发送下一个音频或结束"""
            nonlocal audio_sent_count, current_round
            with state_lock:
                current_round = 2
                audio_sent_count += 1
            logger.info("[VPR Feature ID Only] 第2轮：发送'全双工-黄培峻.wav'（预期：有VAD但没有IAT，声纹不匹配）")
            send_audio_data(ws, peijun_audio_file)

        def end_session(ws):
            """结束会话"""
            logger.info("[VPR Feature ID Only] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Feature ID Only] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # 等待完成
        assert finished.wait(timeout=120), "[VPR Feature ID Only] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Feature ID Only] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))

        # 断言：第1轮应该有 IAT 识别结果（声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Feature ID Only] ✅ 第1轮有 IAT 结果: %s", round_iat[1])

        # 断言：第1轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'female', f"第1轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Feature ID Only] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])

        # 断言：第2轮应该有 VAD 但没有 IAT（声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Feature ID Only] ✅ 第2轮有 VAD: %s", round_vad[2])

        # 第2轮不应该有 IAT
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Feature ID Only] ✅ 第2轮没有 IAT（声纹不匹配）")

        # 断言：第2轮应该有 vpr_info 帧，且 gender="male"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'male', f"第2轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data_2['gender']}'"
        logger.info("[VPR Feature ID Only] ✅ 第2轮有 vpr_info: gender=%s", vpr_info_data_2['gender'])

    def test_continuous_recognition_vpr_group_id_only_female(self, base_url, real_token, vpr_female_group_id_only_params, vpr_group, female_audio_file, peijun_audio_file):
        """测试只传group_id不传feature_id的声纹识别"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0  # 记录发送了几次音频
        round_vad = {}  # 记录每轮的 VAD 消息
        round_iat = {}  # 记录每轮的 IAT 消息
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0  # 当前轮次
        total_rounds = 2  # 总轮次
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Group ID Only] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Group ID Only] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Group ID Only] 发送 start 指令（只传 group_id: %s）", vpr_group['id'])
                ws.send(json.dumps(vpr_female_group_id_only_params))

            elif action == 'started':
                logger.info("[VPR Group ID Only] 会话已创建")
                logger.info("[VPR Group ID Only] 第1轮：发送'全双工-程梅芳.wav'（预期：有IAT识别结果，声纹匹配）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, female_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                # 记录 VAD 消息
                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Group ID Only] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Group ID Only] 第%s轮收到 VAD END", round_num)
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                # 记录 VPR 结果
                if sub_type == 'vpr':
                    vpr_result = result_data.get('vpr_result', {})
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Group ID Only] 第%s轮 VPR 结果: %s", round_num, vpr_result)

                # 记录 IAT 识别结果
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Group ID Only] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Group ID Only] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

            elif action == 'finish':
                logger.info("[VPR Group ID Only] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            """发送音频数据（WAV格式，需要转换为PCM）"""
            import wave

            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Group ID Only] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    check_and_send_next(ws)
                else:
                    end_session(ws)

        def check_and_send_next(ws):
            """检查并发送下一个音频或结束"""
            nonlocal audio_sent_count, current_round
            with state_lock:
                current_round = 2
                audio_sent_count += 1
            logger.info("[VPR Group ID Only] 第2轮：发送'全双工-黄培峻.wav'（预期：有VAD但没有IAT，声纹不匹配）")
            send_audio_data(ws, peijun_audio_file)

        def end_session(ws):
            """结束会话"""
            logger.info("[VPR Group ID Only] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Group ID Only] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # 等待完成
        assert finished.wait(timeout=120), "[VPR Group ID Only] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Group ID Only] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))

        # 断言：第1轮应该有 IAT 识别结果（声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Group ID Only] ✅ 第1轮有 IAT 结果: %s", round_iat[1])

        # 断言：第1轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'female', f"第1轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Group ID Only] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])

        # 断言：第2轮应该有 VAD 但没有 IAT（声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Group ID Only] ✅ 第2轮有 VAD: %s", round_vad[2])

        # 第2轮不应该有 IAT
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Group ID Only] ✅ 第2轮没有 IAT（声纹不匹配）")

        # 断言：第2轮应该有 vpr_info 帧，且 gender="male"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'male', f"第2轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data_2['gender']}'"
        logger.info("[VPR Group ID Only] ✅ 第2轮有 vpr_info: gender=%s", vpr_info_data_2['gender'])

    def test_continuous_recognition_vpr_three_rounds(self, base_url, real_token, vpr_realtime_params, real_audio_file, xueyan_audio_file):
        """测试3轮连续识别：第1轮杨俊（有IAT）→ 第2轮雪艳（无IAT）→ 第3轮杨俊（有IAT）"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0
        round_vad = {}
        round_iat = {}
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0
        total_rounds = 3  # 总轮次
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR 3 Rounds] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR 3 Rounds] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR 3 Rounds] 发送连续模式 start 指令（使用realtime）")
                ws.send(json.dumps(vpr_realtime_params))

            elif action == 'started':
                logger.info("[VPR 3 Rounds] 会话已创建")
                logger.info("[VPR 3 Rounds] 第1轮：发送'今天天气怎么样.wav'（杨俊，预期：有IAT识别结果）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR 3 Rounds] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR 3 Rounds] 第%s轮收到 VAD END", round_num)
                        # 捕获当前轮次的快照，避免竞态条件
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                if sub_type == 'vpr':
                    vpr_result = result_data.get('vpr_result', {})
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR 3 Rounds] 第%s轮 VPR 结果: %s", round_num, vpr_result)

                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR 3 Rounds] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

            elif action == 'finish':
                logger.info("[VPR 3 Rounds] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            import wave
            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR 3 Rounds] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    # 发送下一轮音频
                    check_and_send_next(ws)
                else:
                    # 最后一轮，发送 end 指令
                    end_session(ws)

        def check_and_send_next(ws):
            nonlocal audio_sent_count, current_round
            if audio_sent_count == 1:
                # 发送第2轮：雪艳音频
                current_round = 2
                logger.info("[VPR 3 Rounds] 第2轮：发送'全双工-雪艳.wav'（雪艳，预期：有VAD但没有IAT）")
                audio_sent_count += 1
                send_audio_data(ws, xueyan_audio_file)
            elif audio_sent_count == 2:
                # 发送第3轮：杨俊音频
                current_round = 3
                logger.info("[VPR 3 Rounds] 第3轮：发送'今天天气怎么样.wav'（杨俊，预期：有IAT识别结果）")
                audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

        def end_session(ws):
            logger.info("[VPR 3 Rounds] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR 3 Rounds] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[VPR 3 Rounds] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR 3 Rounds] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第3轮 VAD: %s", round_vad.get(3, []))
        logger.info("  第3轮 IAT: %s", round_iat.get(3, []))
        
        # 断言：第1轮应该有 IAT 结果（杨俊，声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR 3 Rounds] ✅ 第1轮有 IAT 结果: %s", round_iat[1])
        
        # 断言：第2轮应该有 VAD 但没有 IAT（雪艳，声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR 3 Rounds] ✅ 第2轮有 VAD: %s", round_vad[2])
        
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR 3 Rounds] ✅ 第2轮没有 IAT（声纹不匹配）")
        
        # 断言：第3轮应该有 IAT 结果（杨俊，声纹匹配）
        assert 3 in round_iat, "第3轮应该有 IAT 结果"
        assert len(round_iat[3]) > 0, "第3轮应该有 IAT 识别文本"
        logger.info("[VPR 3 Rounds] ✅ 第3轮有 IAT 结果: %s", round_iat[3])

    def test_continuous_recognition_vpr_realtime_with_feature_id(self, base_url, real_token, vpr_realtime_feature_id_params, vpr_feature, real_audio_file, xueyan_audio_file):
        """测试realtime模式下传feature_id的3轮连续识别：第1轮杨俊（有IAT+feature_id）→ 第2轮雪艳（无IAT）→ 第3轮杨俊（有IAT+feature_id）"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0
        round_vad = {}
        round_iat = {}
        round_vpr_feature_id = {}
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0
        total_rounds = 3  # 总轮次
        expected_feature_id = vpr_feature['id']
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Realtime Feature ID] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Realtime Feature ID] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Realtime Feature ID] 发送连续模式 start 指令（realtime + feature_id: %s）", expected_feature_id)
                ws.send(json.dumps(vpr_realtime_feature_id_params))

            elif action == 'started':
                logger.info("[VPR Realtime Feature ID] 会话已创建")
                logger.info("[VPR Realtime Feature ID] 第1轮：发送'今天天气怎么样.wav'（杨俊，预期：有IAT+feature_id）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Feature ID] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Realtime Feature ID] 第%s轮收到 VAD END", round_num)
                        # 捕获当前轮次的快照，避免竞态条件
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                if sub_type == 'vpr':
                    vpr_feature_id_val = result_data.get('vpr_feature_id')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Feature ID] 第%s轮收到 VPR feature_id: %s", round_num, vpr_feature_id_val)
                    if vpr_feature_id_val:
                        if round_num not in round_vpr_feature_id:
                            round_vpr_feature_id[round_num] = []
                        round_vpr_feature_id[round_num].append(vpr_feature_id_val)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Feature ID] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Realtime Feature ID] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

            elif action == 'finish':
                logger.info("[VPR Realtime Feature ID] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            import wave
            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Realtime Feature ID] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    # 发送下一轮音频
                    check_and_send_next(ws)
                else:
                    # 最后一轮，发送 end 指令
                    end_session(ws)

        def check_and_send_next(ws):
            nonlocal audio_sent_count, current_round
            if audio_sent_count == 1:
                # 发送第2轮：雪艳音频
                current_round = 2
                logger.info("[VPR Realtime Feature ID] 第2轮：发送'全双工-雪艳.wav'（雪艳，预期：有VAD但没有IAT）")
                audio_sent_count += 1
                send_audio_data(ws, xueyan_audio_file)
            elif audio_sent_count == 2:
                # 发送第3轮：杨俊音频
                current_round = 3
                logger.info("[VPR Realtime Feature ID] 第3轮：发送'今天天气怎么样.wav'（杨俊，预期：有IAT+feature_id）")
                audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

        def end_session(ws):
            logger.info("[VPR Realtime Feature ID] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Realtime Feature ID] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[VPR Realtime Feature ID] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Realtime Feature ID] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第1轮 feature_id: %s", round_vpr_feature_id.get(1, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))
        logger.info("  第3轮 VAD: %s", round_vad.get(3, []))
        logger.info("  第3轮 IAT: %s", round_iat.get(3, []))
        logger.info("  第3轮 feature_id: %s", round_vpr_feature_id.get(3, []))
        logger.info("  第3轮 vpr_info: %s", round_vpr_info.get(3, []))
        
        # 断言：第1轮应该有 IAT 结果（杨俊，声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Realtime Feature ID] ✅ 第1轮有 IAT 结果: %s", round_iat[1])
        
        # 断言：第1轮应该有 feature_id
        assert 1 in round_vpr_feature_id, "第1轮应该有 feature_id"
        assert len(round_vpr_feature_id[1]) > 0, "第1轮应该返回 feature_id"
        assert expected_feature_id in round_vpr_feature_id[1], f"第1轮的 feature_id 应该是 {expected_feature_id}"
        logger.info("[VPR Realtime Feature ID] ✅ 第1轮有 feature_id: %s", round_vpr_feature_id[1])
        
        # 断言：第1轮应该有 vpr_info 帧，且 gender="male", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'male', f"第1轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Realtime Feature ID] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])
        
        # 断言：第2轮应该有 VAD 但没有 IAT（雪艳，声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Realtime Feature ID] ✅ 第2轮有 VAD: %s", round_vad[2])
        
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Realtime Feature ID] ✅ 第2轮没有 IAT（声纹不匹配）")
        
        # 断言：第2轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'female', f"第2轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data_2['gender']}'"
        assert vpr_info_data_2['age'] == 'adult', f"第2轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data_2['age']}'"
        logger.info("[VPR Realtime Feature ID] ✅ 第2轮有 vpr_info: gender=%s, age=%s", vpr_info_data_2['gender'], vpr_info_data_2['age'])
        
        # 断言：第3轮应该有 IAT 结果（杨俊，声纹匹配）
        assert 3 in round_iat, "第3轮应该有 IAT 结果"
        assert len(round_iat[3]) > 0, "第3轮应该有 IAT 识别文本"
        logger.info("[VPR Realtime Feature ID] ✅ 第3轮有 IAT 结果: %s", round_iat[3])
        
        # 断言：第3轮应该有 feature_id
        assert 3 in round_vpr_feature_id, "第3轮应该有 feature_id"
        assert len(round_vpr_feature_id[3]) > 0, "第3轮应该返回 feature_id"
        assert expected_feature_id in round_vpr_feature_id[3], f"第3轮的 feature_id 应该是 {expected_feature_id}"
        logger.info("[VPR Realtime Feature ID] ✅ 第3轮有 feature_id: %s", round_vpr_feature_id[3])
        
        # 断言：第3轮应该有 vpr_info 帧，且 gender="male", age="adult"
        assert 3 in round_vpr_info, "第3轮应该有 vpr_info 帧"
        assert round_vpr_info[3] is not None, "第3轮应该有 vpr_info 数据"
        vpr_info_data_3 = round_vpr_info[3]
        assert vpr_info_data_3['gender'] == 'male', f"第3轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data_3['gender']}'"
        assert vpr_info_data_3['age'] == 'adult', f"第3轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data_3['age']}'"
        logger.info("[VPR Realtime Feature ID] ✅ 第3轮有 vpr_info: gender=%s, age=%s", vpr_info_data_3['gender'], vpr_info_data_3['age'])


    def test_continuous_recognition_vpr_realtime_with_group_id(self, base_url, real_token, vpr_realtime_group_id_params, vpr_feature, real_audio_file, xueyan_audio_file):
        """测试realtime模式下传group_id的3轮连续识别：第1轮杨俊（有IAT+feature_id）→ 第2轮雪艳（无IAT）→ 第3轮杨俊（有IAT+feature_id）"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0
        round_vad = {}
        round_iat = {}
        round_vpr_feature_id = {}
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0
        total_rounds = 3  # 总轮次
        expected_feature_id = vpr_feature['id']
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Realtime Group ID] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Realtime Group ID] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Realtime Group ID] 发送连续模式 start 指令（realtime + group_id）")
                ws.send(json.dumps(vpr_realtime_group_id_params))

            elif action == 'started':
                logger.info("[VPR Realtime Group ID] 会话已创建")
                logger.info("[VPR Realtime Group ID] 第1轮：发送'今天天气怎么样.wav'（杨俊，预期：有IAT+feature_id）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Group ID] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Realtime Group ID] 第%s轮收到 VAD END", round_num)
                        # 捕获当前轮次的快照，避免竞态条件
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                if sub_type == 'vpr':
                    vpr_feature_id_val = result_data.get('vpr_feature_id')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Group ID] 第%s轮收到 VPR feature_id: %s", round_num, vpr_feature_id_val)
                    if vpr_feature_id_val:
                        if round_num not in round_vpr_feature_id:
                            round_vpr_feature_id[round_num] = []
                        round_vpr_feature_id[round_num].append(vpr_feature_id_val)

                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Realtime Group ID] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

            elif action == 'finish':
                logger.info("[VPR Realtime Group ID] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            import wave
            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Realtime Group ID] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    # 发送下一轮音频
                    check_and_send_next(ws)
                else:
                    # 最后一轮，发送 end 指令
                    end_session(ws)

        def check_and_send_next(ws):
            nonlocal audio_sent_count, current_round
            if audio_sent_count == 1:
                # 发送第2轮：雪艳音频
                current_round = 2
                logger.info("[VPR Realtime Group ID] 第2轮：发送'全双工-雪艳.wav'（雪艳，预期：有VAD但没有IAT）")
                audio_sent_count += 1
                send_audio_data(ws, xueyan_audio_file)
            elif audio_sent_count == 2:
                # 发送第3轮：杨俊音频
                current_round = 3
                logger.info("[VPR Realtime Group ID] 第3轮：发送'今天天气怎么样.wav'（杨俊，预期：有IAT+feature_id）")
                audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

        def end_session(ws):
            logger.info("[VPR Realtime Group ID] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Realtime Group ID] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[VPR Realtime Group ID] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Realtime Group ID] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第1轮 feature_id: %s", round_vpr_feature_id.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第3轮 VAD: %s", round_vad.get(3, []))
        logger.info("  第3轮 IAT: %s", round_iat.get(3, []))
        logger.info("  第3轮 feature_id: %s", round_vpr_feature_id.get(3, []))
        
        # 断言：第1轮应该有 IAT 结果（杨俊，声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Realtime Group ID] ✅ 第1轮有 IAT 结果: %s", round_iat[1])
        
        # 断言：第1轮应该有 feature_id
        assert 1 in round_vpr_feature_id, "第1轮应该有 feature_id"
        assert len(round_vpr_feature_id[1]) > 0, "第1轮应该返回 feature_id"
        assert expected_feature_id in round_vpr_feature_id[1], f"第1轮的 feature_id 应该是 {expected_feature_id}"
        logger.info("[VPR Realtime Group ID] ✅ 第1轮有 feature_id: %s", round_vpr_feature_id[1])
        
        # 断言：第2轮应该有 VAD 但没有 IAT（雪艳，声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Realtime Group ID] ✅ 第2轮有 VAD: %s", round_vad[2])
        
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Realtime Group ID] ✅ 第2轮没有 IAT（声纹不匹配）")
        
        # 断言：第3轮应该有 IAT 结果（杨俊，声纹匹配）
        assert 3 in round_iat, "第3轮应该有 IAT 结果"
        assert len(round_iat[3]) > 0, "第3轮应该有 IAT 识别文本"
        logger.info("[VPR Realtime Group ID] ✅ 第3轮有 IAT 结果: %s", round_iat[3])
        
        # 断言：第3轮应该有 feature_id
        assert 3 in round_vpr_feature_id, "第3轮应该有 feature_id"
        assert len(round_vpr_feature_id[3]) > 0, "第3轮应该返回 feature_id"
        assert expected_feature_id in round_vpr_feature_id[3], f"第3轮的 feature_id 应该是 {expected_feature_id}"
        logger.info("[VPR Realtime Group ID] ✅ 第3轮有 feature_id: %s", round_vpr_feature_id[3])


    def test_continuous_recognition_vpr_realtime_with_audio_data(self, base_url, real_token, vpr_realtime_audio_data_params, real_audio_file):
        """测试realtime模式下同时传audio_data：预期返回错误（code=400, action=error）"""
        messages_received = []
        finished = threading.Event()
        error_received = False
        error_code = None
        error_desc = None

        def on_open(ws):
            logger.info("\n[VPR Realtime Error] 连接已建立")

        def on_message(ws, message):
            nonlocal error_received, error_code, error_desc
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            code = data.get('code')
            logger.info("[VPR Realtime Error] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Realtime Error] 发送 start 指令（realtime + feature_id，预期返回错误）")
                ws.send(json.dumps(vpr_realtime_audio_data_params))

            elif action == 'error':
                error_received = True
                error_code = code
                error_desc = data.get('desc', '')
                logger.info("[VPR Realtime Error] 收到错误: code=%s, desc=%s", code, error_desc)
                finished.set()

            elif action == 'started':
                logger.info("[VPR Realtime Error] ⚠️ 意外收到 started 消息（不应该成功创建会话）")
                finished.set()

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Realtime Error] WebSocket 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=30), "[VPR Realtime Error] 等待错误响应超时"

        # 验证结果
        logger.info("\n[VPR Realtime Error] 测试结果汇总:")
        logger.info("  收到错误: %s", error_received)
        logger.info("  错误码: %s", error_code)
        logger.info("  错误描述: %s", error_desc)

        # 断言：应该收到错误响应
        assert error_received, "应该收到 action='error' 的响应"
        assert error_code == '400', f"错误码应该是 '400'，实际是 '{error_code}'"
        logger.info("[VPR Realtime Error] ✅ 收到预期的错误响应: code=400, action=error")
        logger.info("[VPR Realtime Error] ✅ 错误描述: %s", error_desc)

    def test_continuous_recognition_vpr_realtime_with_feature_id_female(self, base_url, real_token, vpr_female_realtime_feature_id_params, vpr_female_feature, female_audio_file, peijun_audio_file):
        """测试realtime模式下传feature_id的3轮连续识别：第1轮程梅芳（有IAT+feature_id）→ 第2轮黄培峻（无IAT）→ 第3轮程梅芳（有IAT+feature_id）"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0
        round_vad = {}
        round_iat = {}
        round_vpr_feature_id = {}
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0
        total_rounds = 3  # 总轮次
        expected_feature_id = vpr_female_feature['id']
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Realtime Feature ID] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Realtime Feature ID] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Realtime Feature ID] 发送连续模式 start 指令（realtime + feature_id: %s）", expected_feature_id)
                ws.send(json.dumps(vpr_female_realtime_feature_id_params))

            elif action == 'started':
                logger.info("[VPR Realtime Feature ID] 会话已创建")
                logger.info("[VPR Realtime Feature ID] 第1轮：发送'全双工-程梅芳.wav'（程梅芳，预期：有IAT+feature_id）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, female_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Feature ID] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Realtime Feature ID] 第%s轮收到 VAD END", round_num)
                        # 捕获当前轮次的快照，避免竞态条件
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                if sub_type == 'vpr':
                    vpr_feature_id_val = result_data.get('vpr_feature_id')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Feature ID] 第%s轮收到 VPR feature_id: %s", round_num, vpr_feature_id_val)
                    if vpr_feature_id_val:
                        if round_num not in round_vpr_feature_id:
                            round_vpr_feature_id[round_num] = []
                        round_vpr_feature_id[round_num].append(vpr_feature_id_val)

                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Realtime Feature ID] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Feature ID] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

            elif action == 'finish':
                logger.info("[VPR Realtime Feature ID] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            import wave
            logger.info(audio_file)
            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Realtime Feature ID] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    # 发��下一轮音频
                    check_and_send_next(ws)
                else:
                    # 最后一轮，发送 end 指令
                    end_session(ws)

        def check_and_send_next(ws):
            nonlocal audio_sent_count, current_round
            if audio_sent_count == 1:
                # 发送第2轮：黄培峻音频
                current_round = 2
                logger.info("[VPR Realtime Feature ID] 第2轮：发送'全双工-黄培峻.wav'（黄培峻，预期：有VAD但没有IAT）")
                audio_sent_count += 1
                send_audio_data(ws, peijun_audio_file)
            elif audio_sent_count == 2:
                # 发送第3轮：程梅芳音频
                current_round = 3
                logger.info("[VPR Realtime Feature ID] 第3轮：发送'全双工-程梅芳.wav'（程梅芳，预期：有IAT+feature_id）")
                audio_sent_count += 1
                send_audio_data(ws, female_audio_file)

        def end_session(ws):
            logger.info("[VPR Realtime Feature ID] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Realtime Feature ID] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[VPR Realtime Feature ID] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Realtime Feature ID] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第1轮 feature_id: %s", round_vpr_feature_id.get(1, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))
        logger.info("  第3轮 VAD: %s", round_vad.get(3, []))
        logger.info("  第3轮 IAT: %s", round_iat.get(3, []))
        logger.info("  第3轮 feature_id: %s", round_vpr_feature_id.get(3, []))
        logger.info("  第3轮 vpr_info: %s", round_vpr_info.get(3, []))

        # 断言：第1轮应该有 IAT 结果（杨俊，声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Realtime Feature ID] ✅ 第1轮有 IAT 结果: %s", round_iat[1])

        # 断言：第1轮应该有 feature_id
        assert 1 in round_vpr_feature_id, "第1轮应该有 feature_id"
        assert len(round_vpr_feature_id[1]) > 0, "第1轮应该返回 feature_id"
        assert expected_feature_id in round_vpr_feature_id[1], f"第1轮的 feature_id 应该是 {expected_feature_id}"
        logger.info("[VPR Realtime Feature ID] ✅ 第1轮有 feature_id: %s", round_vpr_feature_id[1])

        # 断言：第1轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'female', f"第1轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Realtime Feature ID] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])

        # 断言：第2轮应该有 VAD 但没有 IAT（雪艳，声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Realtime Feature ID] ✅ 第2轮有 VAD: %s", round_vad[2])

        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Realtime Feature ID] ✅ 第2轮没有 IAT（声纹不匹配）")

        # 断言：第2轮应该有 vpr_info 帧，且 gender="male"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'male', f"第2轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data_2['gender']}'"
        logger.info("[VPR Realtime Feature ID] ✅ 第2轮有 vpr_info: gender=%s", vpr_info_data_2['gender'])

        # 断言：第3轮应该有 IAT 结果（杨俊，声纹匹配）
        assert 3 in round_iat, "第3轮应该有 IAT 结果"
        assert len(round_iat[3]) > 0, "第3轮应该有 IAT 识别文本"
        logger.info("[VPR Realtime Feature ID] ✅ 第3轮有 IAT 结果: %s", round_iat[3])

        # 断言：第3轮应该有 feature_id
        assert 3 in round_vpr_feature_id, "第3轮应该有 feature_id"
        assert len(round_vpr_feature_id[3]) > 0, "第3轮应该返回 feature_id"
        assert expected_feature_id in round_vpr_feature_id[3], f"第3轮的 feature_id 应该是 {expected_feature_id}"
        logger.info("[VPR Realtime Feature ID] ✅ 第3轮有 feature_id: %s", round_vpr_feature_id[3])

        # 断言：第3轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 3 in round_vpr_info, "第3轮应该有 vpr_info 帧"
        assert round_vpr_info[3] is not None, "第3轮应该有 vpr_info 数据"
        vpr_info_data_3 = round_vpr_info[3]
        assert vpr_info_data_3['gender'] == 'female', f"第3轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data_3['gender']}'"
        assert vpr_info_data_3['age'] == 'adult', f"第3轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data_3['age']}'"
        logger.info("[VPR Realtime Feature ID] ✅ 第3轮有 vpr_info: gender=%s, age=%s", vpr_info_data_3['gender'], vpr_info_data_3['age'])


    def test_continuous_recognition_vpr_realtime_with_group_id_female(self, base_url, real_token, vpr_female_realtime_group_id_params, vpr_female_feature, female_audio_file, peijun_audio_file):
        """测试realtime模式下传group_id的3轮连续识别：第1轮程梅芳（有IAT+feature_id）→ 第2轮黄培峻（无IAT）→ 第3轮程梅芳（有IAT+feature_id）"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0
        round_vad = {}
        round_iat = {}
        round_vpr_feature_id = {}
        round_vpr_info = {}  # 记录每轮的 vpr_info 帧
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0
        total_rounds = 3  # 总轮次
        expected_feature_id = vpr_female_feature['id']
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Realtime Group ID] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Realtime Group ID] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Realtime Group ID] 发送连续模式 start 指令（realtime + group_id）")
                ws.send(json.dumps(vpr_female_realtime_group_id_params))

            elif action == 'started':
                logger.info("[VPR Realtime Group ID] 会话已创建")
                logger.info("[VPR Realtime Group ID] 第1轮：发送'全双工-程梅芳.wav'（程梅芳，预期：有IAT+feature_id）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, female_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Group ID] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Realtime Group ID] 第%s轮收到 VAD END", round_num)
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                if sub_type == 'vpr':
                    vpr_feature_id = result_data.get('vpr_feature_id')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Group ID] 第%s轮收到 VPR feature_id: %s", round_num, vpr_feature_id)
                    if vpr_feature_id:
                        if round_num not in round_vpr_feature_id:
                            round_vpr_feature_id[round_num] = []
                        round_vpr_feature_id[round_num].append(vpr_feature_id)

                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Realtime Group ID] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

                # 记录 vpr_info 帧
                if sub_type == 'vpr_info':
                    gender = result_data.get('gender', '')
                    age = result_data.get('age', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Realtime Group ID] 第%s轮收到 vpr_info: gender=%s, age=%s", round_num, gender, age)
                    round_vpr_info[round_num] = {'gender': gender, 'age': age}

            elif action == 'finish':
                logger.info("[VPR Realtime Group ID] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            import wave
            logger.info(audio_file)
            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Realtime Group ID] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    # 发送下一轮音频
                    check_and_send_next(ws)
                else:
                    # 最后一轮，发送 end 指令
                    end_session(ws)

        def check_and_send_next(ws):
            nonlocal audio_sent_count, current_round
            if audio_sent_count == 1:
                # 发送第2轮：黄培峻音频
                current_round = 2
                logger.info("[VPR Realtime Group ID] 第2轮：发送'全双工-黄培峻.wav'（黄培峻，预期：有VAD但没有IAT）")
                audio_sent_count += 1
                send_audio_data(ws, peijun_audio_file)
            elif audio_sent_count == 2:
                # 发送第3轮：程梅芳音频
                current_round = 3
                logger.info("[VPR Realtime Group ID] 第3轮：发送'全双工-程梅芳.wav'（程梅芳，预期：有IAT+feature_id）")
                audio_sent_count += 1
                send_audio_data(ws, female_audio_file)

        def end_session(ws):
            logger.info("[VPR Realtime Group ID] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Realtime Group ID] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[VPR Realtime Group ID] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Realtime Group ID] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第1轮 feature_id: %s", round_vpr_feature_id.get(1, []))
        logger.info("  第1轮 vpr_info: %s", round_vpr_info.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))
        logger.info("  第2轮 vpr_info: %s", round_vpr_info.get(2, []))
        logger.info("  第3轮 VAD: %s", round_vad.get(3, []))
        logger.info("  第3轮 IAT: %s", round_iat.get(3, []))
        logger.info("  第3轮 feature_id: %s", round_vpr_feature_id.get(3, []))
        logger.info("  第3轮 vpr_info: %s", round_vpr_info.get(3, []))

        # 断言：第1轮应该有 IAT 结果（杨俊，声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Realtime Group ID] ✅ 第1轮有 IAT 结果: %s", round_iat[1])

        # 断言：第1轮应该有 feature_id
        assert 1 in round_vpr_feature_id, "第1轮应该有 feature_id"
        assert len(round_vpr_feature_id[1]) > 0, "第1轮应该返回 feature_id"
        assert expected_feature_id in round_vpr_feature_id[1], f"第1轮的 feature_id 应该是 {expected_feature_id}"
        logger.info("[VPR Realtime Group ID] ✅ 第1轮有 feature_id: %s", round_vpr_feature_id[1])

        # 断言：第1轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 1 in round_vpr_info, "第1轮应该有 vpr_info 帧"
        assert round_vpr_info[1] is not None, "第1轮应该有 vpr_info 数据"
        vpr_info_data = round_vpr_info[1]
        assert vpr_info_data['gender'] == 'female', f"第1轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data['gender']}'"
        assert vpr_info_data['age'] == 'adult', f"第1轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data['age']}'"
        logger.info("[VPR Realtime Group ID] ✅ 第1轮有 vpr_info: gender=%s, age=%s", vpr_info_data['gender'], vpr_info_data['age'])

        # 断言：第2轮应该有 VAD 但没有 IAT（雪艳，声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Realtime Group ID] ✅ 第2轮有 VAD: %s", round_vad[2])

        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Realtime Group ID] ✅ 第2轮没有 IAT（声纹不匹配）")

        # 断言：第2轮应该有 vpr_info 帧，且 gender="male"
        assert 2 in round_vpr_info, "第2轮应该有 vpr_info 帧"
        assert round_vpr_info[2] is not None, "第2轮应该有 vpr_info 数据"
        vpr_info_data_2 = round_vpr_info[2]
        assert vpr_info_data_2['gender'] == 'male', f"第2轮 vpr_info gender 应该是 'male'，实际是 '{vpr_info_data_2['gender']}'"
        logger.info("[VPR Realtime Group ID] ✅ 第2轮有 vpr_info: gender=%s", vpr_info_data_2['gender'])

        # 断言：第3轮应该有 IAT 结果（杨俊，声纹匹配）
        assert 3 in round_iat, "第3轮应该有 IAT 结果"
        assert len(round_iat[3]) > 0, "第3轮应该有 IAT 识别文本"
        logger.info("[VPR Realtime Group ID] ✅ 第3轮有 IAT 结果: %s", round_iat[3])

        # 断言：第3轮应该有 feature_id
        assert 3 in round_vpr_feature_id, "第3轮应该有 feature_id"
        assert len(round_vpr_feature_id[3]) > 0, "第3轮应该返回 feature_id"
        assert expected_feature_id in round_vpr_feature_id[3], f"第3轮的 feature_id 应该是 {expected_feature_id}"
        logger.info("[VPR Realtime Group ID] ✅ 第3轮有 feature_id: %s", round_vpr_feature_id[3])

        # 断言：第3轮应该有 vpr_info 帧，且 gender="female", age="adult"
        assert 3 in round_vpr_info, "第3轮应该有 vpr_info 帧"
        assert round_vpr_info[3] is not None, "第3轮应该有 vpr_info 数据"
        vpr_info_data_3 = round_vpr_info[3]
        assert vpr_info_data_3['gender'] == 'female', f"第3轮 vpr_info gender 应该是 'female'，实际是 '{vpr_info_data_3['gender']}'"
        assert vpr_info_data_3['age'] == 'adult', f"第3轮 vpr_info age 应该是 'adult'，实际是 '{vpr_info_data_3['age']}'"
        logger.info("[VPR Realtime Group ID] ✅ 第3轮有 vpr_info: gender=%s, age=%s", vpr_info_data_3['gender'], vpr_info_data_3['age'])


    def test_continuous_recognition_no_vpr_feature_id(self, base_url, real_token, no_vpr_feature_id_params, vpr_feature, real_audio_file):
        """测试不开声纹但传vpr_properties：预期有识别结果、VAD和VPR帧，且vpr_feature_id与传入的feature_id一致"""
        messages_received = []
        finished = threading.Event()
        has_vad = False
        has_vad_end = False
        has_iat = False
        has_vpr = False
        vpr_feature_id = None
        iat_text = None
        expected_feature_id = no_vpr_feature_id_params['params']['vpr_properties']['feature_id']

        def on_open(ws):
            logger.info("\n[No VPR Feature ID] 连接已建立")

        def on_message(ws, message):
            nonlocal has_vad, has_vad_end, has_iat, has_vpr, vpr_feature_id, iat_text
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[No VPR Feature ID] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[No VPR Feature ID] 发送 start 指令（vpr_verify=False，但传了 feature_id: %s）", expected_feature_id)
                ws.send(json.dumps(no_vpr_feature_id_params))

            elif action == 'started':
                logger.info("[No VPR Feature ID] 会话已创建，发送音频")
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')
                
                # 检查 VAD
                if sub_type == 'vad':
                    has_vad = True
                    vad_info = result_data.get('info', '')
                    logger.info("[No VPR Feature ID] 收到 VAD: %s", vad_info)
                    
                    # 收到 VAD end 后等待1秒再结束会话
                    if vad_info == 'end' and not has_vad_end:
                        has_vad_end = True
                        logger.info("[No VPR Feature ID] VAD 结束，1秒后发送 end 指令")
                        threading.Timer(1.0, lambda: end_session(ws)).start()
                
                # 检查 VPR
                if sub_type == 'vpr':
                    has_vpr = True
                    vpr_feature_id = result_data.get('vpr_feature_id')
                    logger.info("[No VPR Feature ID] 收到 VPR 帧，vpr_feature_id: %s", vpr_feature_id)
                
                # 检查 IAT（必须是 is_last=True）
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last and text:  # 必须是 is_last=True 且有文本
                        has_iat = True
                        iat_text = text
                        logger.info("[No VPR Feature ID] 收到 IAT (is_last=True): '%s'", text)
                    elif text:
                        logger.info("[No VPR Feature ID] 收到 IAT (is_last=False): '%s'", text)

            elif action == 'finish':
                logger.info("[No VPR Feature ID] 会话结束")
                finished.set()
            
            elif action == 'error':
                logger.info("[No VPR Feature ID] ⚠️ 收到错误: %s", data.get('desc'))
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
            
            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            logger.info("[No VPR Feature ID] 音频发送完成")

        def end_session(ws):
            """结束会话"""
            logger.info("[No VPR Feature ID] 发送 end 指令")
            ws.send(json.dumps({"action": "end"}))
            # 发送 end 后等待0.5秒让服务器处理，然后关闭连接
            threading.Timer(0.5, ws.close()).start()

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[No VPR Feature ID] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[No VPR Feature ID] 连续识别流程超时"

        # 验证结果
        logger.info("\n[No VPR Feature ID] 测试结果汇总:")
        logger.info("  收到 VAD: %s", has_vad)
        logger.info("  收到 IAT: %s, 文本: %s", has_iat, iat_text)
        logger.info("  收到 VPR: %s, vpr_feature_id: %s", has_vpr, vpr_feature_id)
        logger.info("  预期 feature_id: %s", expected_feature_id)
        
        # 断言：应该有 IAT 识别结果
        assert has_iat, "应该有 IAT 识别结果"
        assert iat_text, "IAT 应该有识别文本"
        logger.info("[No VPR Feature ID] ✅ 有 IAT 结果: '%s'", iat_text)
        
        # 断言：应该有 VAD
        assert has_vad, "应该有 VAD 消息"
        logger.info("[No VPR Feature ID] ✅ 有 VAD 消息")
        
        # 断言：应该有 VPR 帧
        assert has_vpr, "应该有 sub='vpr' 的帧"
        logger.info("[No VPR Feature ID] ✅ 有 VPR 帧")
        
        # 断言：vpr_feature_id 应该与传入的 feature_id 一致
        assert vpr_feature_id == expected_feature_id, \
            f"vpr_feature_id 应该与传入的 feature_id 一致，预期: {expected_feature_id}，实际: {vpr_feature_id}"
        logger.info("[No VPR Feature ID] ✅ vpr_feature_id 与传入的 feature_id 一致: %s", vpr_feature_id)

    def test_continuous_recognition_no_vpr_feature_id_only(self, base_url, real_token, no_vpr_feature_id_only_params, vpr_feature, real_audio_file):
        """测试不开声纹只传feature_id不传group_id：预期有识别结果、VAD和VPR帧，且vpr_feature_id与传入的feature_id一致"""
        messages_received = []
        finished = threading.Event()
        has_vad = False
        has_vad_end = False
        has_iat = False
        has_vpr = False
        vpr_feature_id = None
        iat_text = None
        expected_feature_id = no_vpr_feature_id_only_params['params']['vpr_properties']['feature_id']

        def on_open(ws):
            logger.info("\n[No VPR Feature ID Only] 连接已建立")

        def on_message(ws, message):
            nonlocal has_vad, has_vad_end, has_iat, has_vpr, vpr_feature_id, iat_text
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[No VPR Feature ID Only] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[No VPR Feature ID Only] 发送 start 指令（vpr_verify=False，只传 feature_id: %s）", expected_feature_id)
                ws.send(json.dumps(no_vpr_feature_id_only_params))

            elif action == 'started':
                logger.info("[No VPR Feature ID Only] 会话已创建，发送音频")
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')
                
                # 检查 VAD
                if sub_type == 'vad':
                    has_vad = True
                    vad_info = result_data.get('info', '')
                    logger.info("[No VPR Feature ID Only] 收到 VAD: %s", vad_info)
                    
                    # 收到 VAD end 后等待1秒再结束会话
                    if vad_info == 'end' and not has_vad_end:
                        has_vad_end = True
                        logger.info("[No VPR Feature ID Only] VAD 结束，1秒后发送 end 指令")
                        threading.Timer(1.0, lambda: end_session(ws)).start()
                
                # 检查 VPR
                if sub_type == 'vpr':
                    has_vpr = True
                    vpr_feature_id = result_data.get('vpr_feature_id')
                    logger.info("[No VPR Feature ID Only] 收到 VPR 帧，vpr_feature_id: %s", vpr_feature_id)
                
                # 检查 IAT（必须是 is_last=True）
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last and text:  # 必须是 is_last=True 且有文本
                        has_iat = True
                        iat_text = text
                        logger.info("[No VPR Feature ID Only] 收到 IAT (is_last=True): '%s'", text)
                    elif text:
                        logger.info("[No VPR Feature ID Only] 收到 IAT (is_last=False): '%s'", text)

            elif action == 'finish':
                logger.info("[No VPR Feature ID Only] 会话结束")
                finished.set()
            
            elif action == 'error':
                logger.info("[No VPR Feature ID Only] ⚠️ 收到错误: %s", data.get('desc'))
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
            
            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            logger.info("[No VPR Feature ID Only] 音频发送完成")

        def end_session(ws):
            """结束会话"""
            logger.info("[No VPR Feature ID Only] 发送 end 指令")
            ws.send(json.dumps({"action": "end"}))
            # 发送 end 后等待0.5秒让服务器处理，然后关闭连接
            threading.Timer(0.5, ws.close()).start()

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[No VPR Feature ID Only] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[No VPR Feature ID Only] 连续识别流程超时"

        # 验证结果
        logger.info("\n[No VPR Feature ID Only] 测试结果汇总:")
        logger.info("  收到 VAD: %s", has_vad)
        logger.info("  收到 IAT: %s, 文本: %s", has_iat, iat_text)
        logger.info("  收到 VPR: %s, vpr_feature_id: %s", has_vpr, vpr_feature_id)
        logger.info("  预期 feature_id: %s", expected_feature_id)
        
        # 断言：应该有 IAT 识别结果
        assert has_iat, "应该有 IAT 识别结果"
        assert iat_text, "IAT 应该有识别文本"
        logger.info("[No VPR Feature ID Only] ✅ 有 IAT 结果: '%s'", iat_text)
        
        # 断言：应该有 VAD
        assert has_vad, "应该有 VAD 消息"
        logger.info("[No VPR Feature ID Only] ✅ 有 VAD 消息")
        
        # 断言：应该有 VPR 帧
        assert has_vpr, "应该有 sub='vpr' 的帧"
        logger.info("[No VPR Feature ID Only] ✅ 有 VPR 帧")
        
        # 断言：vpr_feature_id 应该与传入的 feature_id 一致
        assert vpr_feature_id == expected_feature_id, \
            f"vpr_feature_id 应该与传入的 feature_id 一致，预期: {expected_feature_id}，实际: {vpr_feature_id}"
        logger.info("[No VPR Feature ID Only] ✅ vpr_feature_id 与传入的 feature_id 一致: %s", vpr_feature_id)

    def test_continuous_recognition_no_vpr_group_id_only(self, base_url, real_token, no_vpr_group_id_only_params, vpr_group, real_audio_file):
        """测试不开声纹只传group_id不传feature_id：预期有识别结果、VAD和VPR帧"""
        messages_received = []
        finished = threading.Event()
        has_vad = False
        has_vad_end = False
        has_iat = False
        has_vpr = False
        vpr_feature_id = None
        iat_text = None
        expected_group_id = no_vpr_group_id_only_params['params']['vpr_properties']['group_id']

        def on_open(ws):
            logger.info("\n[No VPR Group ID Only] 连接已建立")

        def on_message(ws, message):
            nonlocal has_vad, has_vad_end, has_iat, has_vpr, vpr_feature_id, iat_text
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[No VPR Group ID Only] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[No VPR Group ID Only] 发送 start 指令（vpr_verify=False，只传 group_id: %s）", expected_group_id)
                ws.send(json.dumps(no_vpr_group_id_only_params))

            elif action == 'started':
                logger.info("[No VPR Group ID Only] 会话已创建，发送音频")
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')
                
                # 检查 VAD
                if sub_type == 'vad':
                    has_vad = True
                    vad_info = result_data.get('info', '')
                    logger.info("[No VPR Group ID Only] 收到 VAD: %s", vad_info)
                    
                    # 收到 VAD end 后等待1秒再结束会话
                    if vad_info == 'end' and not has_vad_end:
                        has_vad_end = True
                        logger.info("[No VPR Group ID Only] VAD 结束，1秒后发送 end 指令")
                        threading.Timer(1.0, lambda: end_session(ws)).start()
                
                # 检查 VPR
                if sub_type == 'vpr':
                    has_vpr = True
                    vpr_feature_id = result_data.get('vpr_feature_id')
                    logger.info("[No VPR Group ID Only] 收到 VPR 帧，vpr_feature_id: %s", vpr_feature_id)
                
                # 检查 IAT（必须是 is_last=True）
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last and text:  # 必须是 is_last=True 且有文本
                        has_iat = True
                        iat_text = text
                        logger.info("[No VPR Group ID Only] 收到 IAT (is_last=True): '%s'", text)
                    elif text:
                        logger.info("[No VPR Group ID Only] 收到 IAT (is_last=False): '%s'", text)

            elif action == 'finish':
                logger.info("[No VPR Group ID Only] 会话结束")
                finished.set()
            
            elif action == 'error':
                logger.info("[No VPR Group ID Only] ⚠️ 收到错误: %s", data.get('desc'))
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
            
            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            logger.info("[No VPR Group ID Only] 音频发送完成")

        def end_session(ws):
            """结束会话"""
            logger.info("[No VPR Group ID Only] 发送 end 指令")
            ws.send(json.dumps({"action": "end"}))
            # 发送 end 后等待0.5秒让服务器处理，然后关闭连接
            threading.Timer(0.5, ws.close()).start()

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[No VPR Group ID Only] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[No VPR Group ID Only] 连续识别流程超时"

        # 验证结果
        logger.info("\n[No VPR Group ID Only] 测试结果汇总:")
        logger.info("  收到 VAD: %s", has_vad)
        logger.info("  收到 IAT: %s, 文本: %s", has_iat, iat_text)
        logger.info("  收到 VPR: %s, vpr_feature_id: %s", has_vpr, vpr_feature_id)
        logger.info("  预期 group_id: %s", expected_group_id)
        
        # 断言：应该有 IAT 识别结果
        assert has_iat, "应该有 IAT 识别结果"
        assert iat_text, "IAT 应该有识别文本"
        logger.info("[No VPR Group ID Only] ✅ 有 IAT 结果: '%s'", iat_text)
        
        # 断言：应该有 VAD
        assert has_vad, "应该有 VAD 消息"
        logger.info("[No VPR Group ID Only] ✅ 有 VAD 消息")
        
        # 断言：应该有 VPR 帧
        assert has_vpr, "应该有 sub='vpr' 的帧"
        logger.info("[No VPR Group ID Only] ✅ 有 VPR 帧")
        
        # 注意：只传 group_id 时，vpr_feature_id 可能是 group 中任意一个 feature 的 ID
        logger.info("[No VPR Group ID Only] ✅ vpr_feature_id: %s", vpr_feature_id)
        
    def test_continuous_recognition_no_vpr_no_feature_id(self, base_url, real_token, no_vpr_feature_id_params, vpr_feature, xueyan_audio_file):
        """测试不开声纹但传vpr_properties：预期有识别结果、VAD和VPR帧，且vpr_feature_id与传入的feature_id一致"""
        messages_received = []
        finished = threading.Event()
        has_vad = False
        has_vad_end = False
        has_iat = False
        has_vpr = False
        vpr_feature_id = None
        iat_text = None
        expected_feature_id = no_vpr_feature_id_params['params']['vpr_properties']['feature_id']

        def on_open(ws):
            logger.info("\n[No VPR Feature ID] 连接已建立")

        def on_message(ws, message):
            nonlocal has_vad, has_vad_end, has_iat, has_vpr, vpr_feature_id, iat_text
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[No VPR Feature ID] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[No VPR Feature ID] 发送 start 指令（vpr_verify=False，但传了 feature_id: %s）", expected_feature_id)
                ws.send(json.dumps(no_vpr_feature_id_params))

            elif action == 'started':
                logger.info("[No VPR Feature ID] 会话已创建，发送音频")
                send_audio_data(ws, xueyan_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')
                
                # 检查 VAD
                if sub_type == 'vad':
                    has_vad = True
                    vad_info = result_data.get('info', '')
                    logger.info("[No VPR No Feature ID] 收到 VAD: %s", vad_info)
                    
                    # 收到 VAD end 后等待1秒再结束会话
                    if vad_info == 'end' and not has_vad_end:
                        has_vad_end = True
                        logger.info("[No VPR No Feature ID] VAD 结束，1秒后发送 end 指令")
                        threading.Timer(1.0, lambda: end_session(ws)).start()
                
                # 检查 VPR
                if sub_type == 'vpr':
                    has_vpr = True
                    vpr_feature_id = result_data.get('vpr_feature_id')
                    logger.info("[No VPR No Feature ID] 收到 VPR 帧，vpr_feature_id: %s", vpr_feature_id)
                
                # 检查 IAT（必须是 is_last=True）
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last and text:  # 必须是 is_last=True 且有文本
                        has_iat = True
                        iat_text = text
                        logger.info("[No VPR No Feature ID] 收到 IAT (is_last=True): '%s'", text)
                    elif text:
                        logger.info("[No VPR No Feature ID] 收到 IAT (is_last=False): '%s'", text)

            elif action == 'finish':
                logger.info("[No VPR No Feature ID] 会话结束")
                finished.set()
            
            elif action == 'error':
                logger.info("[No VPR Feature ID] ⚠️ 收到错误: %s", data.get('desc'))
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
            
            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            logger.info("[No VPR Feature ID] 音频发送完成")

        def end_session(ws):
            """结束会话"""
            logger.info("[No VPR Feature ID] 发送 end 指令")
            ws.send(json.dumps({"action": "end"}))
            # 发送 end 后等待0.5秒让服务器处理，然后关闭连接
            threading.Timer(0.5, ws.close()).start()

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[No VPR Feature ID] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[No VPR Feature ID] 连续识别流程超时"

        # 验证结果
        logger.info("\n[No VPR Feature ID] 测试结果汇总:")
        logger.info("  收到 VAD: %s", has_vad)
        logger.info("  收到 IAT: %s, 文本: %s", has_iat, iat_text)
        logger.info("  预期 feature_id: %s", expected_feature_id)
        
        # 断言：应该有 IAT 识别结果
        assert has_iat, "应该有 IAT 识别结果"
        assert iat_text, "IAT 应该有识别文本"
        logger.info("[No VPR Feature ID] ✅ 有 IAT 结果: '%s'", iat_text)
        
        # 断言：应该有 VAD
        assert has_vad, "应该有 VAD 消息"
        logger.info("[No VPR Feature ID] ✅ 有 VAD 消息")
        
        # 断言：应该有 VPR 帧
        assert not has_vpr, "应该没有 sub='vpr' 的帧"
        logger.info("[No VPR Feature ID] ✅ 没有 VPR 帧")

    def test_continuous_recognition_no_vpr_realtime(self, base_url, real_token, no_vpr_feature_id_realtime_params, vpr_feature, real_audio_file):
        """测试不开声纹但传vpr_properties：预期有识别结果、VAD和VPR帧，且vpr_feature_id与传入的feature_id一致"""
        messages_received = []
        finished = threading.Event()
        has_vad = False
        has_vad_end = False
        has_iat = False
        has_vpr = False
        vpr_feature_id = None
        iat_text = None
        expected_feature_id = no_vpr_feature_id_realtime_params['params']['vpr_properties']['feature_id']

        def on_open(ws):
            logger.info("\n[No VPR Feature ID] 连接已建立")

        def on_message(ws, message):
            nonlocal has_vad, has_vad_end, has_iat, has_vpr, vpr_feature_id, iat_text
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[No VPR Feature ID] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[No VPR Feature ID] 发送 start 指令（vpr_verify=False，但传了 feature_id: %s）", expected_feature_id)
                ws.send(json.dumps(no_vpr_feature_id_realtime_params))

            elif action == 'started':
                logger.info("[No VPR Feature ID] 会话已创建，发送音频")
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                # 检查 VAD
                if sub_type == 'vad':
                    has_vad = True
                    vad_info = result_data.get('info', '')
                    logger.info("[No VPR Feature ID] 收到 VAD: %s", vad_info)

                    # 收到 VAD end 后等待1秒再结束会话
                    if vad_info == 'end' and not has_vad_end:
                        has_vad_end = True
                        logger.info("[No VPR Feature ID] VAD 结束，1秒后发送 end 指令")
                        threading.Timer(1.0, lambda: end_session(ws)).start()

                # 检查 VPR
                if sub_type == 'vpr':
                    has_vpr = True
                    vpr_feature_id = result_data.get('vpr_feature_id')
                    logger.info("[No VPR Feature ID] 收到 VPR 帧，vpr_feature_id: %s", vpr_feature_id)

                # 检查 IAT（必须是 is_last=True）
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last and text:  # 必须是 is_last=True 且有文本
                        has_iat = True
                        iat_text = text
                        logger.info("[No VPR Feature ID] 收到 IAT (is_last=True): '%s'", text)
                    elif text:
                        logger.info("[No VPR Feature ID] 收到 IAT (is_last=False): '%s'", text)

            elif action == 'finish':
                logger.info("[No VPR Feature ID] 会话结束")
                finished.set()

            elif action == 'error':
                logger.info("[No VPR Feature ID] ⚠️ 收到错误: %s", data.get('desc'))
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

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            logger.info("[No VPR Feature ID] 音频发送完成")

        def end_session(ws):
            """结束会话"""
            logger.info("[No VPR Feature ID] 发送 end 指令")
            ws.send(json.dumps({"action": "end"}))
            # 发送 end 后等待0.5秒让服务器处理，然后关闭连接
            threading.Timer(0.5, ws.close()).start()

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[No VPR Feature ID] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        assert finished.wait(timeout=120), "[No VPR Feature ID] 连续识别流程超时"

        # 验证结果
        logger.info("\n[No VPR Feature ID] 测试结果汇总:")
        logger.info("  收到 VAD: %s", has_vad)
        logger.info("  收到 IAT: %s, 文本: %s", has_iat, iat_text)
        logger.info("  收到 VPR: %s, vpr_feature_id: %s", has_vpr, vpr_feature_id)
        logger.info("  预期 feature_id: %s", expected_feature_id)

        # 断言：应该有 IAT 识别结果
        assert has_iat, "应该有 IAT 识别结果"
        assert iat_text, "IAT 应该有识别文本"
        logger.info("[No VPR Feature ID] ✅ 有 IAT 结果: '%s'", iat_text)

        # 断言：应该有 VAD
        assert has_vad, "应该有 VAD 消息"
        logger.info("[No VPR Feature ID] ✅ 有 VAD 消息")

        # 断言：应该有 VPR 帧
        assert has_vpr, "应该有 sub='vpr' 的帧"
        logger.info("[No VPR Feature ID] ✅ 有 VPR 帧")

        # 断言：vpr_feature_id 应该与传入的 feature_id 一致
        assert vpr_feature_id == expected_feature_id, \
            f"vpr_feature_id 应该与传入的 feature_id 一致，预期: {expected_feature_id}，实际: {vpr_feature_id}"
        logger.info("[No VPR Feature ID] ✅ vpr_feature_id 与传入的 feature_id 一致: %s", vpr_feature_id)
    # 测试连续对话模式完整流程


    def test_continuous_recognition_multiple_rounds_frame_properties(self, base_url, real_token, continuous_mode_frame_properties_params, real_audio_file):
        """测试连续对话模式多轮识别"""
        messages_received = []
        finished = threading.Event()
        rounds_completed = 0

        def on_open(ws):
            logger.info("连接已建立")

        def on_message(ws, message):
            nonlocal rounds_completed
            data = json.loads(message)
            messages_received.append(data)
            logger.info("收到消息: %s", json.dumps(data, ensure_ascii=False))

            if data.get('action') == 'connected':
                logger.info("发送连续模式 start 指令")
                ws.send(json.dumps(continuous_mode_frame_properties_params))

            elif data.get('action') == 'started':
                logger.info("会话已创建，开始第 %s 轮识别", rounds_completed + 1)
                # 发送第一轮音频
                send_audio_data(ws, real_audio_file)

            elif data.get('action') == 'result':
                result_data = data.get('data', {})
                if result_data.get('sub') == 'iat' and result_data.get('is_last'):
                    rounds_completed += 1
                    logger.info("第 %s 轮识别完成: %s", rounds_completed, result_data.get('text', ''))

                    if rounds_completed < 2:
                        # 继续发送第二轮音频
                        logger.info("开始第 %s 轮识别", rounds_completed + 1)
                        time.sleep(0.5)
                        send_audio_data(ws, real_audio_file)
                    else:
                        # 两轮完成，发送结束指令
                        logger.info("发送 end 指令")
                        ws.send(json.dumps({"action": "end"}))

            elif data.get('action') == 'finish':
                logger.info("会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            """发送音频数据"""
            with open(audio_file, 'rb') as f:
                chunk_size = 1280
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                    time.sleep(0.04)

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # 等待完成
        assert finished.wait(timeout=120), "连续识别流程超时"

        # 验证收到多轮识别结果
        result_messages = [msg for msg in messages_received if msg.get('action') == 'result']
        iat_results = [msg for msg in result_messages if msg.get('data', {}).get('sub') == 'iat']
        logger.info("总共收到 %s 个识别结果", len(iat_results))
        vad_messages = [msg for msg in result_messages if msg.get('data', {}).get('sub') == 'vad']
        logger.info("总共收到 %s 个 vad 消息", len(vad_messages))

        for i, vad_msg in enumerate(vad_messages):
            result_data = vad_msg.get('data', {})
            info = result_data.get('info')
            is_last = (i == len(vad_messages) - 1)

            if info == 'start':
                assert 'bos_ms' in result_data, "vad start 消息应包含 bos_ms 字段"
                assert isinstance(result_data.get('bos_ms'), int), "bos_ms 应为整型"
            elif info == 'end':
                if is_last:
                    logger.info("最后一个 vad end 消息（第 %s 个），不验证 eos_ms", i+1)
                else:
                    assert 'eos_ms' in result_data, "vad end 消息应包含 eos_ms 字段"
                    assert isinstance(result_data.get('eos_ms'), int), "eos_ms 应为整型"

    def test_continuous_recognition_vpr_audio_data_frame_properties(self, base_url, real_token, vpr_audio_data_frame_properties_params, real_audio_file, xueyan_audio_file):
        """测试使用音频数据进行声纹识别：杨俊的声纹应该匹配，雪艳的声纹不匹配"""
        messages_received = []
        finished = threading.Event()
        audio_sent_count = 0  # 记录发送了几次音频
        round_vad = {}  # 记录每轮的 VAD 消息
        round_iat = {}  # 记录每轮的 IAT 消息
        round_vad_end_received = {}  # 记录每轮是否已收到 VAD END
        current_round = 0  # 当前轮次
        total_rounds = 2  # 总轮次
        state_lock = threading.RLock()  # 保护共享状态的锁

        def on_open(ws):
            logger.info("\n[VPR Audio Data] 连接已建立")

        def on_message(ws, message):
            nonlocal audio_sent_count, current_round
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("[VPR Audio Data] 收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("[VPR Audio Data] 发送连续模式 start 指令（包含杨俊的声纹音频数据）")
                ws.send(json.dumps(vpr_audio_data_frame_properties_params))

            elif action == 'started':
                logger.info("[VPR Audio Data] 会话已创建")
                logger.info("[VPR Audio Data] 第1轮：发送'今天天气怎么样.wav'（预期：有IAT识别结果，声纹匹配）")
                with state_lock:
                    current_round = 1
                    audio_sent_count += 1
                send_audio_data(ws, real_audio_file)

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                # 记录 VAD 消息
                if sub_type == 'vad':
                    vad_info = result_data.get('info', '')
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Audio Data] 第%s轮收到 VAD: %s", round_num, vad_info)
                    if round_num not in round_vad:
                        round_vad[round_num] = []
                    round_vad[round_num].append(vad_info)

                    # 收到 VAD END 后触发下一轮或结束
                    if vad_info == 'end' and round_num not in round_vad_end_received:
                        round_vad_end_received[round_num] = True
                        logger.info("[VPR Audio Data] 第%s轮收到 VAD END", round_num)
                        # 捕获当前轮次的快照，避免竞态条件
                        threading.Timer(0.5, lambda r=round_num: handle_vad_end(ws, r)).start()

                # 记录 VPR 结果
                if sub_type == 'vpr':
                    vpr_result = result_data.get('vpr_result', {})
                    with state_lock:
                        round_num = current_round
                    logger.info("[VPR Audio Data] 第%s轮 VPR 结果: %s", round_num, vpr_result)

                # 记录 IAT 识别结果
                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    is_last = result_data.get('is_last', False)
                    if is_last:
                        with state_lock:
                            round_num = current_round
                        logger.info("[VPR Audio Data] 第%s轮收到 IAT (is_last=True): '%s'", round_num, text)
                        if round_num not in round_iat:
                            round_iat[round_num] = []
                        round_iat[round_num].append(text)

            elif action == 'finish':
                logger.info("[VPR Audio Data] 会话结束")
                finished.set()

        def send_audio_data(ws, audio_file):
            """发送音频数据（WAV格式，需要转换为PCM）"""
            import wave

            if audio_file.endswith('.wav'):
                with wave.open(audio_file, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
            else:
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()

            chunk_size = 1280
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
            with state_lock:
                round_num = current_round
            logger.info("[VPR Audio Data] 第%s轮音频发送完成，等待 VAD END...", round_num)

        def handle_vad_end(ws, round_snapshot):
            """处理 VAD END 事件"""
            with state_lock:
                if round_snapshot < total_rounds:
                    # 发送下一轮音频
                    check_and_send_next(ws)
                else:
                    # 最后一轮，发送 end 指令
                    end_session(ws)

        def check_and_send_next(ws):
            """检查并发送下一个音频或结束"""
            nonlocal audio_sent_count, current_round
            # 发送第二个音频
            current_round = 2
            logger.info("[VPR Audio Data] 第2轮：发送'全双工-雪艳.wav'（预期：有VAD但没有IAT，声纹不匹配）")
            audio_sent_count += 1
            send_audio_data(ws, xueyan_audio_file)

        def end_session(ws):
            """结束会话"""
            logger.info("[VPR Audio Data] 所有音频发送完毕，发送 end 指令")
            ws.send(json.dumps({"action": "end"}))

        headers = {'Authorization': f'Bearer {real_token}'}
        ws = websocket.WebSocketApp(
            base_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, error: logger.info("[VPR Audio Data] 错误: %s", error),
            on_close=lambda ws, code, msg: finished.set()
        )

        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # 等待完成
        assert finished.wait(timeout=120), "[VPR Audio Data] 连续识别流程超时"

        # 验证结果
        logger.info("\n[VPR Audio Data] 测试结果汇总:")
        logger.info("  第1轮 VAD: %s", round_vad.get(1, []))
        logger.info("  第1轮 IAT: %s", round_iat.get(1, []))
        logger.info("  第2轮 VAD: %s", round_vad.get(2, []))
        logger.info("  第2轮 IAT: %s", round_iat.get(2, []))

        # 断言：第1轮应该有 IAT 识别结果（声纹匹配）
        assert 1 in round_iat, "第1轮应该有 IAT 结果"
        assert len(round_iat[1]) > 0, "第1轮应该有 IAT 识别文本"
        logger.info("[VPR Audio Data] ✅ 第1轮有 IAT 结果: %s", round_iat[1])

        # 断言：第2轮应该有 VAD 但没有 IAT（声纹不匹配）
        assert 2 in round_vad, "第2轮应该有 VAD 消息"
        assert len(round_vad[2]) > 0, "第2轮应该收到 VAD 消息"
        logger.info("[VPR Audio Data] ✅ 第2轮有 VAD: %s", round_vad[2])

        # 第2轮不应该有 IAT
        if 2 in round_iat and len(round_iat[2]) > 0:
            assert False, f"第2轮不应该有 IAT 结果（声纹不匹配），但收到了: {round_iat[2]}"
        logger.info("[VPR Audio Data] ✅ 第2轮没有 IAT（声纹不匹配）")

        # 验证 vad 消息的 bos_ms 和 eos_ms 字段
        vad_messages = [msg for msg in messages_received if msg.get('action') == 'result' and msg.get('data', {}).get('sub') == 'vad']
        logger.info("[VPR Audio Data] 总共收到 %s 个 vad 消息", len(vad_messages))

        for i, vad_msg in enumerate(vad_messages):
            result_data = vad_msg.get('data', {})
            info = result_data.get('info')
            is_last = (i == len(vad_messages) - 1)

            if info == 'start':
                assert 'bos_ms' in result_data, "vad start 消息应包含 bos_ms 字段"
                assert isinstance(result_data.get('bos_ms'), int), "bos_ms 应为整型"
                logger.info("[VPR Audio Data] ✅ vad start 有 bos_ms: %s", result_data.get('bos_ms'))
            elif info == 'end':
                if is_last:
                    logger.info("[VPR Audio Data] 最后一个 vad end 消息（第 %s 个），不验证 eos_ms", i+1)
                else:
                    assert 'eos_ms' in result_data, "vad end 消息应包含 eos_ms 字段"
                    assert isinstance(result_data.get('eos_ms'), int), "eos_ms 应为整型"
                    logger.info("[VPR Audio Data] ✅ vad end 有 eos_ms: %s", result_data.get('eos_ms'))


class TestAudioFormats:
    """测试不同音频格式支持"""

    @pytest.mark.parametrize("audio_format", ["raw"])
    def test_different_audio_formats(self, base_url, real_token, audio_format, real_audio_file):
        """测试不同音频编码格式"""
        session_started = threading.Event()
        received_data = {}

        params = {
            "action": "start",
            "params": {
                "data_type": "audio",
                "aue": audio_format,
                "asr_properties": {"ent": "home-va"}
            }
        }

        def on_open(ws):
            ws.send(json.dumps(params))

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

        assert session_started.wait(timeout=10), f"{audio_format} 格式会话创建超时"
        assert received_data['response']['action'] == 'started'


class TestErrorHandling:
    """测试错误处理功能"""

    def test_handle_parameter_error(self, base_url, real_token):
        """测试处理参数错误"""
        error_received = threading.Event()
        received_data = {}

        # 发送错误的参数
        invalid_params = {
            "action": "start",
            "params": {
                "data_type": "invalid_type",  # 无效的数据类型
                "aue": "raw"
            }
        }

        def on_open(ws):
            ws.send(json.dumps(invalid_params))

        def on_message(ws, message):
            data = json.loads(message)
            logger.info("收到消息: %s", json.dumps(data, ensure_ascii=False))
            if data.get('action') == 'error':
                received_data['response'] = data
                error_received.set()
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

        # 等待错误响应
        if error_received.wait(timeout=10):
            assert received_data['response']['action'] == 'error'
            logger.info("收到错误码: %s", received_data['response'].get('code'))


class TestAdvancedFeatures:
    """测试高级功能"""

    def test_vad_detection(self, base_url, real_token, real_audio_file):
        """测试 VAD 语音活动检测"""
        vad_received = threading.Event()
        messages_received = []

        params = {
            "action": "start",
            "params": {
                "data_type": "audio",
                "aue": "raw",
                "asr_properties": {"ent": "home-va"},
                "vad_properties": {
                    "vad_type": "default",
                    "vad_eos": 500,
                    "max_eos": 1000
                }
            }
        }

        def on_open(ws):
            logger.info("连接已建立")

        def on_message(ws, message):
            data = json.loads(message)
            messages_received.append(data)
            logger.info("收到消息: %s", json.dumps(data, ensure_ascii=False))

            if data.get('action') == 'connected':
                ws.send(json.dumps(params))

            elif data.get('action') == 'started':
                # 发送音频数据
                with open(real_audio_file, 'rb') as f:
                    chunk_size = 1280
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                        time.sleep(0.04)
                ws.send(json.dumps({"action": "end"}))

            elif data.get('action') == 'result':
                data_field = data.get('data')
                if isinstance(data_field, dict) and data_field.get('sub') == 'vad':
                    logger.info("收到 VAD 结果: %s", data_field)
                    vad_received.set()

            elif data.get('action') == 'finish':
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

        time.sleep(15)  # 等待处理完成

        # 检查是否收到 VAD 结果
        vad_results = [
            msg for msg in messages_received 
            if isinstance(msg.get('data'), dict) and msg.get('data').get('sub') == 'vad'
        ]
        logger.info("收到 %s 个 VAD 结果", len(vad_results))


    def test_frame_properties_raw(self, base_url, real_token, frame_properties_raw_params, real_audio_file):
        """测试frame_properties raw格式"""
        messages_received = []
        finished = threading.Event()

        def on_open(ws):
            logger.info("1. 连接已建立")

        def on_message(ws, message):
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("2. 收到 connected，发送 start 指令")
                ws.send(json.dumps(frame_properties_raw_params))

            elif action == 'started':
                logger.info("3. 收到 started，开始发送音频数据")
                self._send_audio_data(ws, real_audio_file)
                logger.info("4. 音频发送完毕，等待 vad end")

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                if sub_type == 'vad':
                    info = result_data.get('info', '')
                    logger.info("收到 VAD 结果: %s", info)
                    if info == 'end':
                        logger.info("5. 收到 vad end，发送 end 指令")
                        ws.send(json.dumps({"action": "end"}))

                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    if text:
                        logger.info("5. 收到识别结果: %s", text)

            elif action == 'finish':
                logger.info("6. 收到 finish，会话结束")
                finished.set()

        def on_error(ws, error):
            logger.info("错误: %s", error)

        def on_close(ws, close_status_code, close_msg):
            logger.info("连接已关闭")
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

        assert finished.wait(timeout=30), "识别流程超时"

        # 验证消息序列
        actions = [msg.get('action') for msg in messages_received]
        assert 'connected' in actions
        assert 'started' in actions
        assert 'finish' in actions

        # 检查 vad 类型消息
        result_messages = [msg for msg in messages_received if msg.get('action') == 'result']
        vad_messages = [msg for msg in result_messages if msg.get('data', {}).get('sub') == 'vad']
        for vad_msg in vad_messages:
            result_data = vad_msg.get('data', {})
            info = result_data.get('info')
            if info == 'start':
                assert 'bos_ms' in result_data, "vad start 消息应包含 bos_ms 字段"
                assert isinstance(result_data.get('bos_ms'), int), "bos_ms 应为整型"
            elif info == 'end':
                assert 'eos_ms' in result_data, "vad end 消息应包含 eos_ms 字段"
                assert isinstance(result_data.get('eos_ms'), int), "eos_ms 应为整型"

    def _send_audio_data(self, ws, audio_file):
        """发送音频数据"""
        with open(audio_file, 'rb') as f:
            chunk_size = 1280  # 40ms 的数据量
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)

    def test_frame_properties_ico(self, base_url, real_token, frame_properties_ico_params, ico_audio_file):
        """测试frame_properties raw格式"""
        messages_received = []
        finished = threading.Event()

        def on_open(ws):
            logger.info("1. 连接已建立")

        def on_message(ws, message):
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("2. 收到 connected，发送 start 指令")
                ws.send(json.dumps(frame_properties_ico_params))

            elif action == 'started':
                logger.info("3. 收到 started，开始发送音频数据")
                self._send_audio_data(ws, ico_audio_file)
                logger.info("4. 音频发送完毕，等待 vad end")

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                if sub_type == 'vad':
                    info = result_data.get('info', '')
                    logger.info("收到 VAD 结果: %s", info)
                    if info == 'end':
                        logger.info("5. 收到 vad end，发送 end 指令")
                        ws.send(json.dumps({"action": "end"}))

                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    if text:
                        logger.info("5. 收到识别结果: %s", text)

            elif action == 'finish':
                logger.info("6. 收到 finish，会话结束")
                finished.set()

        def on_error(ws, error):
            logger.info("错误: %s", error)

        def on_close(ws, close_status_code, close_msg):
            logger.info("连接已关闭")
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

        assert finished.wait(timeout=30), "识别流程超时"

        # 验证消息序列
        actions = [msg.get('action') for msg in messages_received]
        assert 'connected' in actions
        assert 'started' in actions
        assert 'finish' in actions

        # 检查 vad 类型消息
        result_messages = [msg for msg in messages_received if msg.get('action') == 'result']
        vad_messages = [msg for msg in result_messages if msg.get('data', {}).get('sub') == 'vad']
        for vad_msg in vad_messages:
            result_data = vad_msg.get('data', {})
            info = result_data.get('info')
            if info == 'start':
                assert 'bos_ms' in result_data, "vad start 消息应包含 bos_ms 字段"
                assert isinstance(result_data.get('bos_ms'), int), "bos_ms 应为整型"
            elif info == 'end':
                assert 'eos_ms' in result_data, "vad end 消息应包含 eos_ms 字段"
                assert isinstance(result_data.get('eos_ms'), int), "eos_ms 应为整型"

    def _send_audio_data(self, ws, audio_file):
        """发送音频数据"""
        with open(audio_file, 'rb') as f:
            chunk_size = 1280  # 40ms 的数据量
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)


    def test_frame_properties_wrong(self, base_url, real_token, frame_properties_wrong_params, real_audio_file):
        """测试frame_properties 不应该出现的情况"""
        messages_received = []
        finished = threading.Event()

        def on_open(ws):
            logger.info("1. 连接已建立")

        def on_message(ws, message):
            data = json.loads(message)
            messages_received.append(data)
            action = data.get('action')
            logger.info("收到消息: %s", json.dumps(data, ensure_ascii=False))

            if action == 'connected':
                logger.info("2. 收到 connected，发送 start 指令")
                ws.send(json.dumps(frame_properties_wrong_params))

            elif action == 'started':
                logger.info("3. 收到 started，开始发送音频数据")
                self._send_audio_data(ws, real_audio_file)
                logger.info("4. 音频发送完毕，等待 vad end")

            elif action == 'result':
                result_data = data.get('data', {})
                sub_type = result_data.get('sub')

                if sub_type == 'vad':
                    info = result_data.get('info', '')
                    logger.info("收到 VAD 结果: %s", info)
                    if info == 'end':
                        logger.info("5. 收到 vad end，发送 end 指令")
                        ws.send(json.dumps({"action": "end"}))

                if sub_type == 'iat':
                    text = result_data.get('text', '')
                    if text:
                        logger.info("5. 收到识别结果: %s", text)

            elif action == 'finish':
                logger.info("6. 收到 finish，会话结束")
                finished.set()

        def on_error(ws, error):
            logger.info("错误: %s", error)

        def on_close(ws, close_status_code, close_msg):
            logger.info("连接已关闭")
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

        assert finished.wait(timeout=30), "识别流程超时"

        # 验证消息序列
        actions = [msg.get('action') for msg in messages_received]
        assert 'connected' in actions
        assert 'started' in actions
        assert 'finish' in actions

        # 检查 vad 类型消息
        result_messages = [msg for msg in messages_received if msg.get('action') == 'result']
        vad_messages = [msg for msg in result_messages if msg.get('data', {}).get('sub') == 'vad']
        for vad_msg in vad_messages:
            result_data = vad_msg.get('data', {})
            info = result_data.get('info')
            if info == 'start':
                assert 'bos_ms' in result_data, "vad start 消息不应包含 bos_ms 字段"
            elif info == 'end':
                assert 'eos_ms' in result_data, "vad end 消息不应包含 eos_ms 字段"

    def _send_audio_data(self, ws, audio_file):
        """发送音频数据"""
        with open(audio_file, 'rb') as f:
            chunk_size = 1280  # 40ms 的数据量
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                time.sleep(0.04)
