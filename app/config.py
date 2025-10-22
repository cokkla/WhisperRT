"""
配置模块，包含应用的所有配置参数
"""

# 音频配置
SAMPLE_RATE = 16000 # 采样率 16000Hz
BLOCK_SIZE = 2000  # 块大小 从4000减少到2000，减少音频块延迟
BUFFER_SECONDS = 3  # 缓冲区大小 从5秒减少到3秒，这是最大的延迟优化

# 模型配置
AVAILABLE_MODELS = {
    "tiny": "最小模型，速度最快，精度最低",
    "base": "基础模型，速度快，精度一般",
    "small": "小型模型，速度和精度平衡",
    "large-v3-turbo": "大型模型，精度高，接近tiny的速度"
}
DEFAULT_MODEL = "large-v3-turbo"
DEFAULT_LANGUAGE = None # 不设置语言，自动选择

# 全局设置配置
GLOBAL_SETTINGS = {
    "show_timestamp": False,  # 默认不显示时间戳
    "language": DEFAULT_LANGUAGE,  # 全局语言设置
    "model": DEFAULT_MODEL,  # 全局模型设置
}

LLM_MODEL = {
    "model_name": "qwen-plus",
    "api_key": "sk-b2fc84acf3554474b78f1901805ea26e",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    # "model_name": "deepseek-reasoner",
    # "api_key": "sk-eefa18bfe34a4849a7c7ddf638b472e3",
    # "base_url": "https://api.deepseek.com/v1"
}


# 文件转录配置
FILE_TRANSCRIPTION_CONFIG = {
    "max_file_size": 100 * 1024 * 1024,  # 100MB
    "allowed_formats": [".wav", ".mp3", ".m4a", ".flac", ".ogg"],
    "temp_dir": "temp_audio",
    "output_format": "text",  # 可选: "text", "json"
}

# 反幻觉配置 - 速度优化
# 初始提示词，刚开始中文提示词通用，第二天中文提示词突然会给英文音频造成幻觉，英文提示词又会影响中文音频
# 目前直接在whisper.py中不传入初始提示词
ANTI_HALLUCINATION_CONFIG = {
    "temperature": 0.0,  # 保持确定性
    "no_speech_threshold": 0.6,  # 保持无语音检测
    "condition_on_previous_text": False,  # 是否依赖前文
    "compression_ratio_threshold": 2.4,  # 保持压缩比阈值
    "log_prob_threshold": -1.0,  # 保持对数概率阈值
    "initial_prompt": "请只转写实际听到的语音内容，忽略背景音乐和噪音。",  # 简化prompt
    # "initial_prompt": "Please transcribe only the actual spoken content and ignore background music and noise.",
    # 音频检测阈值 - 更宽松以减少处理时间
    "energy_threshold": 0.015,  # 从0.02降低到0.015
    "confidence_threshold": 0.3,  # 从0.5降低到0.3，接受更多结果，减少误判
    "silence_threshold": 0.01,  # 从0.005放宽到0.01
    "zcr_threshold": 0.15,  # 从0.1放宽到0.15
}

# 幻觉内容检测模式
HALLUCINATION_PATTERNS = [
    r"优优独播剧场",
    r"YoYo Television Series Exclusive",
    r"请不吝点赞",
    r"订阅.*转发.*打赏",
    r"明镜与点点栏目",
    r"支持明镜",
    r"明镜.*栏目",
    r"独播剧场",
    r"点赞.*订阅",
    r"转发.*打赏",
    r"YoYo.*Television",
    r"Series.*Exclusive",
    r"网友们.*支持",
    r"感谢.*观看",
    r"关注.*频道"
]

# 服务器配置
HOST = "0.0.0.0"
PORT = 5444