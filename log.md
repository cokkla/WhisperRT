# 修改日志

## 2024-12-19

### 项目结构分析和API设计文档
- **任务**: 分析WhisprRT项目的整体架构和API设计
- **分析内容**:
  - 详细分析了项目文件结构，包括每个文件的具体作用
  - 确认项目使用FastAPI作为后端框架
  - 整理了完整的RESTful API接口文档
  - 文档化了WebSocket通信协议
  - 提供了典型使用流程示例
- **项目架构特点**:
  - 基于FastAPI的模块化设计
  - 支持完全离线运行的实时语音转写
  - 内置反幻觉优化机制
  - 提供Web界面和API接口
- **API设计**:
  - 音频设备管理API
  - 转写控制API
  - 反幻觉配置API
  - 显示设置API
  - WebSocket实时通信
- **修改文件**: `log.md` (添加分析记录)

### 修复pyproject.toml配置问题
- **问题**: 使用 `pip install -e .` 时报错，提示发现多个顶级包
- **原因**: pyproject.toml缺少包发现和构建系统配置
- **解决方案**: 
  - 添加了 `[build-system]` 配置
  - 添加了 `[tool.setuptools.packages.find]` 配置，指定只包含 `app*` 包
  - 添加了 `[tool.setuptools.package-data]` 配置，包含静态文件和模板文件
- **修改文件**: `pyproject.toml`

### 创建requirements.txt文件
- **目的**: 为不熟悉pyproject.toml的用户提供传统的依赖安装方式
- **内容**: 包含所有项目依赖及其版本要求
- **修改文件**: `requirements.txt`

### 实现音频文件转录和说话人识别功能
- **任务**: 基于faster-whisper + pyannote.audio实现音频转录并区分说话人
- **实现内容**:
  - 添加了pyannote.audio、torch、python-multipart、pydub等必要依赖
  - 扩展了配置文件，添加说话人识别和文件转录相关配置
  - 创建了说话人识别服务类，实现音频说话人分离和识别
  - 创建了文件转录服务类，处理音频文件上传、转录和说话人识别
  - 扩展了数据模型，添加文件转录相关的请求/响应schema
  - 创建了文件转录API端点，提供RESTful接口
  - 更新了路由注册，集成新的API端点
- **核心功能**:
  - 支持多种音频格式上传（wav、mp3、m4a、flac、ogg）
  - 自动音频格式转换（统一转换为16kHz WAV格式）
  - 使用faster-whisper进行高精度转录
  - 使用pyannote.audio进行说话人分离和识别
  - 支持时间戳显示和句子合并
  - 输出格式：speaker1 [0.00s - 2.00s] 欢迎大家参与今天的会议
- **API接口**:
  - POST /api/transcribe_file - 上传音频文件进行转录
  - GET /api/speaker_config - 获取说话人识别配置
  - POST /api/update_speaker_config - 更新说话人识别配置
  - GET /api/file_transcription_config - 获取文件转录配置
  - POST /api/test_speaker_diarization - 测试说话人识别服务
- **修改文件**: 
  - `pyproject.toml` (添加依赖)
  - `app/config.py` (添加配置)
  - `app/services/speaker_diarization.py` (新建)
  - `app/services/file_transcription.py` (新建)
  - `app/models/schemas.py` (扩展数据模型)
  - `app/api/endpoints/file_transcription.py` (新建)
  - `app/api/router.py` (更新路由)

### 实现全局配置管理，统一实时转录和文件转录设置
- **任务**: 将时间戳显示、语言选择、模型选择等设置为全局配置，统一管理实时转录和文件转录
- **实现内容**:
  - 在 `app/config.py` 中添加了 `GLOBAL_SETTINGS` 全局配置
  - 设置默认值：时间戳显示为 `False`，说话人识别为 `True`
  - 修改了 `app/models/schemas.py`，删除重复参数，添加全局设置管理schema
  - 更新了 `app/services/transcription.py`，使其使用全局配置
  - 更新了 `app/services/file_transcription.py`，使其使用全局配置
  - 修改了转录API端点，添加全局设置管理功能
  - 简化了文件转录API端点，移除重复参数
- **核心改进**:
  - 语言选择、时间戳显示、模型选择等设置现在是全局的
  - 实时转录和文件转录使用相同的配置
  - 避免了重复的参数定义和配置不一致问题
  - 提供了统一的全局设置管理接口
- **新增API接口**:
  - `GET /api/global_settings` - 获取当前全局设置
  - `POST /api/update_global_settings` - 更新全局设置
- **修改的API接口**:
  - `POST /api/transcribe_file` - 简化参数，使用全局配置
  - `POST /api/set_timestamp` - 现在更新全局设置
  - `POST /api/change_model` - 现在更新全局设置
  - `POST /api/change_language` - 现在更新全局设置
- **修改文件**:
  - `app/config.py` (添加全局设置配置)
  - `app/models/schemas.py` (删除重复参数，添加全局设置schema)
  - `app/services/transcription.py` (使用全局配置)
  - `app/services/file_transcription.py` (使用全局配置)
  - `app/api/endpoints/transcription.py` (添加全局设置管理)
  - `app/api/endpoints/file_transcription.py` (简化参数)

### 使用本地模型目录（方案B）
- **目的**: 脱离网络、固定模型版本，直接从项目内目录加载模型
- **变更**:
  - `app/config.py`
    - `DEFAULT_MODEL` -> `models/faster-whisper/large-v3-turbo`
    - `SPEAKER_DIARIZATION_CONFIG.model_name` -> `models/pyannote/speaker-diarization-community-1`
    - 新增本地基础路径 `SPEAKER_DIARIZATION_CONFIG.local_model_base_path = models/pyannote`
- **本地目录结构（示例）**:
  - `models/`
    - `faster-whisper/large-v3-turbo/`  # ct2 模型文件（model.bin, config.json, vocabulary.json 等）
    - `pyannote/speaker-diarization-community-1/`  # 含 config.json 与权重（pytorch_model.bin 或 model.safetensors）
    - 若需要：`pyannote/wespeaker-voxceleb-resnet34-LM/`、`pyannote/xvec_transform.npz`、`pyannote/plda.npz`
- **注意**:
  - 确保上述目录与文件完整，否则会回退到远程下载
  - 如需改回远程加载，可将 `model_name` 改为 Hub 路径（如 `pyannote/...`）或设置 `HF_HOME`

### 启动脚本修复与说明
- 新增 `start_server.cmd`：一键重定向 HuggingFace/CT2 缓存到 `models/` 并启动服务
- 处理内容：
  - 设置 `HF_HOME/HUGGINGFACE_HUB_CACHE/CTRANSLATE2_CACHE_DIR`
  - 自动创建目录
  - `chcp 65001` 解决中文输出乱码
  - 优先 `conda activate llm`，失败回退 `conda run -n llm`
  - 启动命令：`uvicorn app.main:app --reload`

## 2025-10-15

### 优化 start_server.cmd 启动脚本的小问题
- **变更原因**: 注释与实际端口行为不一致，且存在冗余目录判断。
- **变更内容**:
  - 明确使用 `--host 127.0.0.1 --port 8000` 启动 Uvicorn，避免端口来源歧义。
  - 启动前输出访问地址 `http://127.0.0.1:8000`，便于快速访问。
  - 移除对 `CTRANSLATE2_CACHE_DIR` 的冗余 `if defined` 判断，直接按需创建目录。
  - 修正无 Conda 场景下的提示命令为带 `--host/--port` 的版本。
- **受影响文件**: `start_server.cmd`

### 修复本地 pyannote 模型路径被当作 Hub Repo 校验的问题
- **问题**: 将 `models\\pyannote\\speaker-diarization-3.1` 作为本地路径时，被 `Pipeline.from_pretrained` 误当作仓库名触发 `HFValidationError`。
- **原因**: 相对路径未解析为绝对路径，且反斜杠形式在某些路径判断中不稳健。
- **修复**:
  - 在 `app/services/speaker_diarization.py` 中新增 `_resolve_model_path`，将配置路径解析为项目根目录下的绝对路径。
  - 加载逻辑优先使用解析后的本地绝对路径，避免触发 HuggingFace Repo 校验。
  - 若路径看起来是本地路径但不存在，主动抛出 `FileNotFoundError`，避免误判为远程仓库。
  - 将 `app/config.py` 中 pyannote 本地路径改为正斜杠形式，增强兼容性。
- **受影响文件**: `app/services/speaker_diarization.py`
  `app/config.py`

### 修复pyannote.audio本地模型加载问题
- **问题**: 即使配置了本地模型路径，pyannote.audio仍然尝试从HuggingFace下载模型
- **原因分析**:
  - 本地模型文件结构可能不完整
  - 缺少依赖的子模型（如segmentation-3.0）
  - 模型加载逻辑没有正确处理本地路径
- **解决方案**:
  - 改进了 `app/services/speaker_diarization.py` 中的模型加载逻辑
  - 添加了本地模型路径检测和验证功能
  - 增强了错误处理和诊断信息
  - 创建了模型设置辅助脚本 `setup_local_models.py`
- **核心改进**:
  - 自动检测本地模型路径是否存在
  - 验证本地模型文件结构完整性
  - 提供详细的错误信息和解决建议
  - 支持本地模型和远程模型的灵活切换
- **新增功能**:
  - 模型文件结构验证 (`_validate_local_model` 方法)
  - 详细的错误诊断和解决建议
  - 本地模型设置脚本 (`setup_local_models.py`)
- **修改文件**:
  - `app/services/speaker_diarization.py` (改进模型加载逻辑)
  - `app/config.py` (增强本地模型配置)
  - `setup_local_models.py` (新建模型设置脚本)

## 2025-01-27

### 移除说话人识别功能，简化项目为纯转录功能
- **任务**: 分析项目并移除说话人识别功能，只保留实时转录和文件上传转录功能
- **移除内容**:
  - 删除了 `app/services/speaker_diarization.py` 说话人识别服务文件
  - 移除了文件转录API中的说话人识别相关端点
  - 简化了文件转录服务，移除说话人识别相关方法
  - 清理了配置文件中的说话人识别相关配置
  - 移除了数据模型中的说话人识别相关schema
  - 更新了项目依赖，移除pyannote.audio和torch包
- **保留功能**:
  - 实时语音转录功能（WebSocket）
  - 文件上传转录功能
  - 反幻觉配置和优化
  - 音频设备管理
  - 模型切换和语言选择
- **API变更**:
  - 移除了 `/api/speaker_config` 端点
  - 移除了 `/api/update_speaker_config` 端点
  - 移除了 `/api/test_speaker_diarization` 端点
  - 简化了 `/api/transcribe_file` 端点，移除说话人识别参数
  - 更新了全局设置，移除说话人识别相关配置
- **配置变更**:
  - 移除了 `SPEAKER_DIARIZATION_CONFIG` 配置
  - 简化了 `GLOBAL_SETTINGS`，移除说话人识别相关设置
  - 简化了 `FILE_TRANSCRIPTION_CONFIG`，移除句子合并相关配置
- **依赖变更**:
  - 移除了 `pyannote.audio>=3.1.1` 依赖
  - 移除了 `torch>=2.0.0` 依赖
- **修改文件**:
  - `app/services/speaker_diarization.py` (删除)
  - `app/api/endpoints/file_transcription.py` (简化API端点)
  - `app/services/file_transcription.py` (简化服务方法)
  - `app/config.py` (移除说话人识别配置)
  - `app/models/schemas.py` (移除说话人识别模型)
  - `app/api/endpoints/transcription.py` (更新全局设置)
  - `pyproject.toml` (移除相关依赖)
  - `start_server.cmd` (更新启动脚本)

### 更新启动脚本以适应简化后的项目
- **任务**: 修改 `start_server.cmd` 以适应移除说话人识别功能后的项目
- **修改内容**:
  - 更新了注释，移除了关于下载模型到 `models/` 目录的过时说明
  - 简化了环境变量设置，只保留 `CTRANSLATE2_CACHE_DIR`（faster-whisper 需要）
  - 移除了 HuggingFace 相关的环境变量设置（不再需要）
  - 统一了 host 设置为 `0.0.0.0`，与配置文件保持一致
  - 更新了错误提示中的手动启动命令
- **优化效果**:
  - 启动脚本更加简洁，只设置必要的环境变量
  - 与配置文件中的 host/port 设置保持一致
  - 移除了不再需要的 HuggingFace 模型缓存设置
- **修改文件**: `start_server.cmd`

### 添加 /transcribe_file 接口调试功能
- **任务**: 为 `/transcribe_file` 接口添加完整的调试支持
- **实现内容**:
  - 修改了 `app/core/logging.py`，将日志级别改为DEBUG，添加函数名和行号信息
  - 增强了 `app/api/endpoints/file_transcription.py` 中的调试日志，添加详细的请求信息记录
  - 改进了 `app/services/file_transcription.py` 中的调试信息，记录文件处理的每个步骤
  - 创建了 `start_debug_server.cmd` 调试专用启动脚本，启用详细日志和热重载
  - 创建了 `test_transcribe_file.py` 测试脚本，提供完整的接口测试功能
- **调试功能**:
  - 详细的请求日志记录（文件类型、大小、处理步骤）
  - 完整的错误堆栈跟踪
  - 临时文件操作日志
  - 音频格式转换过程日志
  - 转录处理时间统计
- **测试工具**:
  - 自动测试多种音频格式
  - 错误情况测试（空文件、不支持格式）
  - 配置接口测试
  - 详细的测试结果报告
- **使用方法**:
  1. 运行 `start_debug_server.cmd` 启动调试服务器
  2. 运行 `python test_transcribe_file.py` 进行接口测试
  3. 查看控制台输出获取详细调试信息
- **修改文件**:
  - `app/core/logging.py` (启用DEBUG日志)
  - `app/api/endpoints/file_transcription.py` (添加详细调试日志)
  - `app/services/file_transcription.py` (添加处理步骤日志)
  - `start_debug_server.cmd` (新建调试启动脚本)
  - `test_transcribe_file.py` (新建测试脚本)