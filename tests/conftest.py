"""
Pytest configuration and fixtures for WebSocket ASR API tests
使用真实音频数据和真实 API 连接
"""
import base64
import os
import pytest


# pylint:disable=f-string-without-interpolation, unused-argument, redefined-outer-name
@pytest.fixture
def real_token():
    """真实的认证 token，从环境变量读取"""
    token = os.environ.get('LISTENAI_API_KEY')
    if not token:
        pytest.skip("需要设置环境变量 LISTENAI_API_KEY")
    return token


@pytest.fixture
def base_url():
    """Base WebSocket URL, 根据 RUN_BUILD_ENV 环境变量选择环境"""
    build_env = os.environ.get('RUN_BUILD_ENV', 'staging')
    if build_env == 'staging':
        return os.environ.get('ASR_API_URL', 'wss://staging-api.listenai.com/v2/asr')
    return os.environ.get('ASR_API_URL', 'wss://api.listenai.com/v2/asr')


@pytest.fixture
def vpr_api_base_url():
    """VPR API Base URL, 根据 RUN_BUILD_ENV 环境变量选择环境"""
    build_env = os.environ.get('RUN_BUILD_ENV', 'staging')
    if build_env == 'staging':
        return os.environ.get('VPR_API_URL', 'https://staging-api.listenai.com')
    return os.environ.get('VPR_API_URL', 'https://api.listenai.com')


# ==================== 音频文件路径 Fixtures ====================

@pytest.fixture
def real_audio_file():
    """真实的音频文件路径（WAV 格式）"""
    audio_path = os.path.join("audio", "今天天气怎么样.wav")
    if not os.path.exists(audio_path):
        pytest.skip(f"音频文件不存在: {audio_path}")
    return audio_path


@pytest.fixture
def pcm_audio_file():
    """PCM 格式音频文件路径"""
    audio_path = os.path.join("audio", "audio.pcm")
    if not os.path.exists(audio_path):
        pytest.skip(f"PCM 音频文件不存在: {audio_path}")
    return audio_path


@pytest.fixture
def speex_audio_file():
    """Speex 格式音频文件路径"""
    audio_path = os.path.join("audio", "audio.speex")
    if not os.path.exists(audio_path):
        pytest.skip(f"Speex 音频文件不存在: {audio_path}")
    return audio_path


@pytest.fixture
def ico_audio_file():
    """ICO 格式音频文件路径"""
    audio_path = os.path.join("audio", "audio.ico")
    if not os.path.exists(audio_path):
        pytest.skip(f"ICO 音频文件不存在: {audio_path}")
    return audio_path


# ==================== 音频数据 Fixtures ====================

@pytest.fixture
def real_audio_data(real_audio_file):
    """从真实 WAV 文件加载音频数据并转换为 PCM"""
    import wave
    
    try:
        with wave.open(real_audio_file, 'rb') as wav_file:
            # 读取 WAV 文件参数
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            # 读取所有音频数据
            audio_data = wav_file.readframes(n_frames)
            
            # 打印音频信息
            print(f"\n[WAV] 音频信息: {framerate}Hz, {sample_width*8}bit, {channels}ch, {n_frames} frames, {len(audio_data)} bytes")
            
            return audio_data
    except Exception as e:
        pytest.skip(f"无法加载音频文件: {e}")


@pytest.fixture
def pcm_audio_data(pcm_audio_file):
    """加载 PCM 格式音频数据"""
    try:
        with open(pcm_audio_file, 'rb') as f:
            audio_data = f.read()
        print(f"\n[PCM] 音频数据大小: {len(audio_data)} bytes")
        return audio_data
    except Exception as e:
        pytest.skip(f"无法加载 PCM 音频文件: {e}")


@pytest.fixture
def speex_audio_data(speex_audio_file):
    """加载 Speex 格式音频数据"""
    try:
        with open(speex_audio_file, 'rb') as f:
            audio_data = f.read()
        print(f"\n[Speex] 音频数据大小: {len(audio_data)} bytes")
        return audio_data
    except Exception as e:
        pytest.skip(f"无法加载 Speex 音频文件: {e}")


@pytest.fixture
def ico_audio_data(ico_audio_file):
    """加载 ICO 格式音频数据"""
    try:
        with open(ico_audio_file, 'rb') as f:
            audio_data = f.read()
        print(f"\n[ICO] 音频数据大小: {len(audio_data)} bytes")
        return audio_data
    except Exception as e:
        pytest.skip(f"无法加载 ICO 音频文件: {e}")


# ==================== 音频数据块 Fixtures ====================

@pytest.fixture
def audio_chunks(real_audio_data):
    """将音频数据分割成 40ms 的数据块（用于 raw PCM）"""
    # 40ms 的数据块大小: 16000 * 2 * 0.04 = 1280 bytes (假设 16kHz 16bit)
    chunk_size = 1280
    chunks = []
    
    for i in range(0, len(real_audio_data), chunk_size):
        chunk = real_audio_data[i:i + chunk_size]
        if len(chunk) > 0:
            chunks.append(chunk)
    
    print(f"音频分割为 {len(chunks)} 个数据块")
    return chunks


@pytest.fixture
def real_audio_chunks(real_audio_data):
    """将真实音频数据分割成 40ms 的数据块（别名）"""
    chunk_size = 1280
    chunks = []
    
    for i in range(0, len(real_audio_data), chunk_size):
        chunk = real_audio_data[i:i + chunk_size]
        if len(chunk) > 0:
            chunks.append(chunk)
    
    return chunks


@pytest.fixture
def pcm_audio_chunks(pcm_audio_data):
    """将 PCM 音频数据分割成 40ms 的数据块"""
    chunk_size = 1280
    chunks = []
    
    for i in range(0, len(pcm_audio_data), chunk_size):
        chunk = pcm_audio_data[i:i + chunk_size]
        if len(chunk) > 0:
            chunks.append(chunk)
    
    print(f"PCM 音频分割为 {len(chunks)} 个数据块")
    return chunks


@pytest.fixture
def speex_audio_chunks(speex_audio_data):
    """将 Speex 音频数据分割成数据块"""
    # Speex 的数据块大小通常是 70 bytes
    chunk_size = 70
    chunks = []
    
    for i in range(0, len(speex_audio_data), chunk_size):
        chunk = speex_audio_data[i:i + chunk_size]
        if len(chunk) > 0:
            chunks.append(chunk)
    
    print(f"Speex 音频分割为 {len(chunks)} 个数据块")
    return chunks


@pytest.fixture
def ico_audio_chunks(ico_audio_data):
    """将 ICO 音频数据分割成数据块"""
    # ICO 格式的数据块大小
    chunk_size = 640  # 根据实际情况调整
    chunks = []
    
    for i in range(0, len(ico_audio_data), chunk_size):
        chunk = ico_audio_data[i:i + chunk_size]
        if len(chunk) > 0:
            chunks.append(chunk)
    
    print(f"ICO 音频分割为 {len(chunks)} 个数据块")
    return chunks


# ==================== 参数配置 Fixtures ====================

@pytest.fixture
def default_start_params():
    """Default start parameters for ASR session (raw PCM)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "0",
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "default",
                "vad_eos": 500,
                "max_eos": 1000
            }
        }
    }


@pytest.fixture
def pcm_start_params():
    """Start parameters for PCM format"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "0",
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            }
        }
    }


@pytest.fixture
def speex_start_params():
    """Start parameters for Speex format"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "speex",
            "speex_size": 70,
            "fullduplex": "0",
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            }
        }
    }


@pytest.fixture
def ico_start_params():
    """Start parameters for ICO format"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "ico",
            "fullduplex": "0",
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            }
        }
    }


@pytest.fixture
def continuous_mode_params():
    """Parameters for continuous recognition mode"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            }
        }
    }


@pytest.fixture
def vad_params():
    """VAD detection parameters"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "asr_properties": {
                "ent": "home-va"
            },
            "vad_properties": {
                "vad_type": "default",
                "vad_eos": 500,
                "max_eos": 1000
            }
        }
    }


@pytest.fixture
def evad_params():
    """EVAD multi-dimensional detection parameters"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "asr_properties": {
                "ent": "home-va"
            },
            "vad_properties": {
                "vad_type": "evad",
                "vad_eos": 500,
                "max_eos": 1000,
                "max_bos": 5000,
                "maybe_eos": 500,
                "audio_gain": "1.0"
            }
        }
    }


@pytest.fixture
def hotword_params():
    """Custom hotword parameters"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "asr_properties": {
                "ent": "home-va",
                "dhw": "dhw=utf-8;今天|天气|怎么样|需要|带伞"
            }
        }
    }


@pytest.fixture
def wake_word_params():
    """Wake word parameters"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "asr_properties": {
                "ent": "home-va"
            },
            "wake_properties": {
                "wake_words_filter": True,
                "words": ["小智同学", "你好小智"]
            }
        }
    }


@pytest.fixture
def punctuation_disabled_params():
    """Parameters with punctuation disabled"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "asr_properties": {
                "ent": "home-va",
                "ptt": 0  # 关闭标点
            }
        }
    }


@pytest.fixture
def realtime_result_params():
    """Parameters for real-time result return"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs"  # 开启实时返回
            }
        }
    }


# ==================== Pytest 配置 ====================

def pytest_configure(config):
    """Pytest configuration"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring real API connection"
    )
    config.addinivalue_line(
        "markers", "requires_token: marks tests that require ASR_API_TOKEN environment variable"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically add markers to integration tests"""
    for item in items:
        if "test_websocket_asr_api" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.requires_token)



# ==================== 声纹识别 (VPR) Fixtures ====================
@pytest.fixture
def vpr_audio_file():
    """声纹识别用的音频文件（杨俊.mp3）"""
    audio_path = os.path.join("audio", "杨俊.mp3")
    if not os.path.exists(audio_path):
        pytest.skip(f"声纹音频文件不存在: {audio_path}")
    return audio_path


@pytest.fixture
def xueyan_audio_file():
    """雪艳的音频文件（用于声纹识别负样本测试）"""
    audio_path = os.path.join("audio", "全双工-雪艳.wav")
    if not os.path.exists(audio_path):
        pytest.skip(f"雪艳音频文件不存在: {audio_path}")
    return audio_path


@pytest.fixture
def female_audio_file():
    """程梅芳的音频文件（女性声纹，用于声纹识别测试）"""
    audio_path = os.path.join("audio", "全双工-程梅芳.wav")
    if not os.path.exists(audio_path):
        pytest.skip(f"程梅芳音频文件不存在: {audio_path}")
    return audio_path


@pytest.fixture
def peijun_audio_file():
    """黄培峻的音频文件（用于声纹识别负样本测试）"""
    audio_path = os.path.join("audio", "全双工-黄培峻.wav")
    if not os.path.exists(audio_path):
        pytest.skip(f"黄培峻音频文件不存在: {audio_path}")
    return audio_path


@pytest.fixture
def vpr_audio_base64(vpr_audio_file):
    """将声纹音频文件转换为 base64 编码"""
    try:
        with open(vpr_audio_file, 'rb') as f:
            audio_data = f.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        print(f"\n[VPR] 音频文件大小: {len(audio_data)} bytes")
        print(f"[VPR] Base64 编码长度: {len(audio_base64)} 字符")
        return audio_base64
    except Exception as e:
        pytest.skip(f"无法加载声纹音频文件: {e}")


@pytest.fixture
def vpr_female_audio_base64(female_audio_file):
    """将程梅芳音频文件转换为 base64 编码"""
    try:
        with open(female_audio_file, 'rb') as f:
            audio_data = f.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        print(f"\n[VPR] 程梅芳音频文件大小: {len(audio_data)} bytes")
        print(f"[VPR] 程梅芳 Base64 编码长度: {len(audio_base64)} 字符")
        return audio_base64
    except Exception as e:
        pytest.skip(f"无法加载程梅芳音频文件: {e}")


@pytest.fixture
def vpr_group_data():
    """创建声纹特征库的数据"""
    import time
    return {
        "name": f"测试声纹库_{int(time.time())}",
        "info": "用于自动化测试的声纹特征库"
    }


@pytest.fixture
def vpr_feature_data(vpr_audio_base64):
    """创建声纹特征的数据"""
    return {
        "name": "杨俊声纹",
        "info": "杨俊的声纹特征数据",
        "audio": {
            "text": "这是杨俊的语音样本",
            "audio_data": vpr_audio_base64,
            "encoding": "lame",
            "channels": 1,
            "sample_rate": 16000,
            "bit_depth": 16
        }
    }


@pytest.fixture
def vpr_female_feature_data(vpr_female_audio_base64):
    """创建程梅芳的声纹特征数据"""
    return {
        "name": "程梅芳声纹",
        "info": "程梅芳的声纹特征数据",
        "audio": {
            "text": "这是程梅芳的语音样本",
            "audio_data": vpr_female_audio_base64,
            "encoding": "lame",
            "channels": 1,
            "sample_rate": 16000,
            "bit_depth": 16
        }
    }


@pytest.fixture
def vpr_group(real_token, vpr_api_base_url, vpr_group_data):
    """创建一个声纹特征库并在测试后清理"""
    import requests
    
    # 创建特征库
    headers = {
        'Authorization': f'Bearer {real_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        f"{vpr_api_base_url}/v1/vpr/group",
        headers=headers,
        json=vpr_group_data, timeout=60
    )
    
    if response.status_code != 200:
        pytest.skip(f"创建声纹特征库失败: {response.text}")
    
    group = response.json()['data']
    group_id = group['id']
    print(f"\n[VPR] 创建声纹特征库成功: {group_id}")
    
    yield group
    
    # 清理：删除特征库
    try:
        requests.delete(
            f"{vpr_api_base_url}/v1/vpr/group/{group_id}",
            headers=headers, timeout=60
        )
        print(f"\n[VPR] 删除声纹特征库: {group_id}")
    except Exception as e:
        print(f"\n[VPR] 清理特征库失败: {e}")


@pytest.fixture
def vpr_feature(real_token, vpr_api_base_url, vpr_group, vpr_feature_data):
    """创建一个声纹特征并在测试后清理"""
    import requests
    
    # 添加 group_id 到特征数据
    feature_data = vpr_feature_data.copy()
    feature_data['group_id'] = vpr_group['id']
    
    # 创建特征
    headers = {
        'Authorization': f'Bearer {real_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        f"{vpr_api_base_url}/v1/vpr/feature",
        headers=headers,
        json=feature_data, timeout=60
    )
    
    if response.status_code != 200:
        pytest.skip(f"创建声纹特征失败: {response.text}")
    
    feature = response.json()['data']
    feature_id = feature['id']
    print(f"\n[VPR] 创建声纹特征成功: {feature_id}")
    
    yield feature
    
    # 清理：删除特征
    try:
        requests.delete(
            f"{vpr_api_base_url}/v1/vpr/feature/{feature_id}",
            headers=headers, timeout=60
        )
        print(f"\n[VPR] 删除声纹特征: {feature_id}")
    except Exception as e:
        print(f"\n[VPR] 清理特征失败: {e}")


@pytest.fixture
def vpr_female_feature(real_token, vpr_api_base_url, vpr_group, vpr_female_feature_data):
    """创建一个声纹特征并在测试后清理"""
    import requests

    # 添加 group_id 到特征数据
    feature_data = vpr_female_feature_data.copy()
    feature_data['group_id'] = vpr_group['id']

    # 创建特征
    headers = {
        'Authorization': f'Bearer {real_token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(
        f"{vpr_api_base_url}/v1/vpr/feature",
        headers=headers,
        json=feature_data, timeout=60
    )

    if response.status_code != 200:
        pytest.skip(f"创建声纹特征失败: {response.text}")

    feature = response.json()['data']
    feature_id = feature['id']
    print(f"\n[VPR] 创建声纹特征成功: {feature_id}")

    yield feature

    # 清理：删除特征
    try:
        requests.delete(
            f"{vpr_api_base_url}/v1/vpr/feature/{feature_id}",
            headers=headers, timeout=60
        )
        print(f"\n[VPR] 删除声纹特征: {feature_id}")
    except Exception as e:
        print(f"\n[VPR] 清理特征失败: {e}")


@pytest.fixture
def vpr_audio_data_params(vpr_audio_base64):
    """Parameters for continuous recognition mode"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "registered",
            },
            "vpr_properties": {
                "audio": {
                    "audio_data": vpr_audio_base64,
                    "aue": "lame",
                },
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_female_audio_data_params(vpr_female_audio_base64):
    """Parameters for continuous recognition mode"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "registered",
            },
            "vpr_properties": {
                "audio": {
                    "audio_data": vpr_female_audio_base64,
                    "aue": "lame",
                },
                "vpr_info": "1",
            }
        }
    }

@pytest.fixture
def vpr_feature_id_params(vpr_group, vpr_feature):
    """Parameters for continuous recognition mode"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "registered",
            },
            "vpr_properties": {
                "feature_id": vpr_feature['id'],
                "group_id": vpr_group['id'],
                "vpr_info": "1",
            }
        }
    }

@pytest.fixture
def vpr_female_feature_id_params(vpr_group, vpr_female_feature):
    """Parameters for continuous recognition mode"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "registered",
            },
            "vpr_properties": {
                "feature_id": vpr_female_feature['id'],
                "group_id": vpr_group['id'],
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_feature_id_only_params(vpr_feature):
    """Parameters with only feature_id (no group_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "registered",
            },
            "vpr_properties": {
                "feature_id": vpr_feature['id'],
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_female_feature_id_only_params(vpr_female_feature):
    """Parameters with only feature_id (no group_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "registered",
            },
            "vpr_properties": {
                "feature_id": vpr_female_feature['id'],
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_group_id_only_params(vpr_group, vpr_feature):
    """Parameters with only group_id (no feature_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "registered",
            },
            "vpr_properties": {
                "group_id": vpr_group['id'],
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_female_group_id_only_params(vpr_group, vpr_female_feature):
    """Parameters with only group_id (no feature_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "registered",
            },
            "vpr_properties": {
                "group_id": vpr_group['id'],
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_realtime_params():
    """Parameters with only group_id (no feature_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "realtime",
            }
        }
    }


@pytest.fixture
def vpr_realtime_feature_id_params(vpr_feature):
    """Parameters with only group_id (no feature_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "realtime",
            },
            "vpr_properties": {
                "feature_id": vpr_feature['id'],
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_female_realtime_feature_id_params(vpr_female_feature):
    """Parameters with only group_id (no feature_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "realtime",
            },
            "vpr_properties": {
                "feature_id": vpr_female_feature['id'],
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_realtime_group_id_params(vpr_group):
    """Parameters with only group_id (no feature_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "realtime",
            },
            "vpr_properties": {
                "group_id": vpr_group['id'],
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_female_realtime_group_id_params(vpr_group):
    """Parameters with only group_id (no feature_id) for female tests"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "realtime",
            },
            "vpr_properties": {
                "group_id": vpr_group['id'],
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_realtime_audio_data_params(vpr_audio_base64):
    """Parameters with only group_id (no feature_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "realtime",
            },
            "vpr_properties": {
                "audio": {
                    "audio_data": vpr_audio_base64,
                    "aue": "lame",
                },
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def vpr_female_realtime_audio_data_params(vpr_female_audio_base64):
    """Parameters with only group_id (no feature_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "realtime",
            },
            "vpr_properties": {
                "audio": {
                    "audio_data": vpr_female_audio_base64,
                    "aue": "lame",
                },
                "vpr_info": "1",
            }
        }
    }


@pytest.fixture
def no_vpr_feature_id_params(vpr_group, vpr_feature):
    """Parameters for continuous recognition mode"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": False,
            },
            "vpr_properties": {
                "feature_id": vpr_feature['id'],
                "group_id": vpr_group['id'],
            }
        }
    }


@pytest.fixture
def no_vpr_feature_id_only_params(vpr_feature):
    """Parameters with only feature_id (no group_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": False,
            },
            "vpr_properties": {
                "feature_id": vpr_feature['id'],
            }
        }
    }


@pytest.fixture
def no_vpr_group_id_only_params(vpr_group, vpr_feature):
    """Parameters with only group_id (no feature_id)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": False,
            },
            "vpr_properties": {
                "group_id": vpr_group['id'],
            }
        }
    }


@pytest.fixture
def no_vpr_feature_id_realtime_params(vpr_group, vpr_feature):
    """Parameters for continuous recognition mode"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": False,
                "vpr_type": "realtime",
            },
            "vpr_properties": {
                "feature_id": vpr_feature['id'],
                "group_id": vpr_group['id'],
            }
        }
    }


@pytest.fixture
def frame_properties_raw_params():
    """frame properties start parameters for ASR session (raw PCM)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "0",
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vad_eos": 500,
                "max_eos": 1000
            },
            "frame_properties": {
                "frame_size": 1280,
                "frame_ms": 40
            }
        }
    }


@pytest.fixture
def frame_properties_ico_params():
    """Default start parameters for ASR session (ico)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "ico",
            "fullduplex": "0",
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vad_eos": 500,
                "max_eos": 1000
            },
            "frame_properties": {
                "frame_size": 40,
                "frame_ms": 20
            }
        }
    }


@pytest.fixture
def frame_properties_wrong_params():
    """frame properties parameters for ASR session (raw PCM)"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "0",
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vad_eos": 500,
                "max_eos": 1000
            },
            "frame_properties": {
                "frame_size": 1024,
                "frame_ms": 40
            }
        }
    }


@pytest.fixture
def continuous_mode_frame_properties_params():
    """Parameters for continuous recognition mode"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vad_eos": 500,
                "max_eos": 1000
            },
            "frame_properties": {
                "frame_size": 1280,
                "frame_ms": 40
            }
        }
    }


@pytest.fixture
def vpr_audio_data_frame_properties_params(vpr_audio_base64):
    """Parameters for continuous recognition mode"""
    return {
        "action": "start",
        "params": {
            "data_type": "audio",
            "aue": "raw",
            "fullduplex": "1",
            "fullduplex_timeout": 60,
            "asr_properties": {
                "ent": "home-va",
                "dwa": "wpgs",
                "ptt": 1
            },
            "vad_properties": {
                "vad_type": "evad",
                "vpr_verify": True,
                "vpr_type": "registered",
            },
            "vpr_properties": {
                "audio": {
                    "audio_data": vpr_audio_base64,
                    "aue": "lame",
                }
            },
            "frame_properties": {
                "frame_size": 1280,
                "frame_ms": 40
            }
        }
    }
