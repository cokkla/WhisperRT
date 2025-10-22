"""
文件流式转录服务测试脚本

功能说明：
- 测试 file_transcription_stream_service.run_task 的各种场景
- 验证基础转录功能、WebSocket连接、任务取消、错误处理等
- 测试 FileStreamTaskState 状态管理
- 验证与 faster-whisper 模型的集成

使用方法：
python test/test_run_task.py

依赖：
- app.services.file_transcription_stream.file_transcription_stream_service
- app.services.file_transcription_stream.FileStreamTaskState
- faster_whisper.WhisperModel
- 需要测试音频文件：temp_audio/si519.wav

测试场景：
1. 基础文件转录测试
2. 带WebSocket连接的文件转录测试
3. 任务取消功能测试
4. 错误处理测试（不存在的文件）
5. 服务方法测试（创建任务、停止任务等）
"""

import os
import time
import threading
import asyncio
from typing import Dict, Any

from faster_whisper import WhisperModel

from app.services.file_transcription_stream import file_transcription_stream_service, FileStreamTaskState


class MockWebSocket:
    """模拟WebSocket连接，用于测试"""
    def __init__(self):
        self.messages = []
        self.connected = True

    async def send_json(self, data: Dict[str, Any]):
        """模拟发送JSON消息"""
        self.messages.append(data)
        print(f"[WebSocket] 发送消息: {data}")

    def get_messages(self):
        """获取所有接收到的消息"""
        return self.messages.copy()

    def clear_messages(self):
        """清空消息记录"""
        self.messages.clear()


def test_basic_transcription():
    """基础转录测试"""
    print("=" * 50)
    print("测试1: 基础文件转录")
    print("=" * 50)

    # 检查测试文件是否存在
    test_file = '../temp_audio/si519.wav'
    if not os.path.exists(test_file):
        print(f"错误: 测试文件 {test_file} 不存在")
        return False

    # 创建任务状态
    state = FileStreamTaskState(
        task_id='test-basic-001',
        filename='si519.wav',
        language='zh',
        total_seconds=None,
        processed_seconds=0.0,
        status='running',
        cancel_event=threading.Event(),
        subscribers=set(),
        transcript=[],
        temp_file_path=test_file
    )

    print(f"开始转录文件: {test_file}")
    start_time = time.time()

    # 运行转录任务
    file_transcription_stream_service.run_task(state, state.temp_file_path)

    end_time = time.time()
    print(f"转录完成，耗时: {end_time - start_time:.2f}秒")
    print(f"任务状态: {state.status}")
    print(f"转录结果数量: {len(state.transcript)}")

    # 显示转录结果
    if state.transcript:
        print("\n转录结果:")
        for i, item in enumerate(state.transcript, 1):
            print(f"{i}. [{item['timestamp']}] {item['text']} (置信度: {item['confidence']:.3f})")

    return state.status == 'completed'


def test_with_websocket():
    """带WebSocket连接的测试"""
    print("\n" + "=" * 50)
    print("测试2: 带WebSocket连接的文件转录")
    print("=" * 50)

    test_file = '../temp_audio/si519.wav'
    if not os.path.exists(test_file):
        print(f"错误: 测试文件 {test_file} 不存在")
        return False

    # 创建模拟WebSocket
    mock_ws = MockWebSocket()

    # 创建任务状态并添加WebSocket订阅
    state = FileStreamTaskState(
        task_id='test-websocket-002',
        filename='si519.wav',
        language='zh',
        total_seconds=None,
        processed_seconds=0.0,
        status='running',
        cancel_event=threading.Event(),
        subscribers={mock_ws},
        transcript=[],
        temp_file_path=test_file
    )

    print(f"开始转录文件: {test_file} (带WebSocket)")
    start_time = time.time()

    # 运行转录任务
    file_transcription_stream_service.run_task(state, state.temp_file_path)

    end_time = time.time()
    print(f"转录完成，耗时: {end_time - start_time:.2f}秒")
    print(f"任务状态: {state.status}")
    print(f"WebSocket消息数量: {len(mock_ws.get_messages())}")

    # 显示WebSocket消息
    print("\nWebSocket消息:")
    for i, msg in enumerate(mock_ws.get_messages(), 1):
        print(f"{i}. {msg}")

    return state.status == 'completed'


def test_cancellation():
    """任务取消测试"""
    print("\n" + "=" * 50)
    print("测试3: 任务取消功能")
    print("=" * 50)

    test_file = '../temp_audio/si519.wav'
    if not os.path.exists(test_file):
        print(f"错误: 测试文件 {test_file} 不存在")
        return False

    # 创建任务状态
    state = FileStreamTaskState(
        task_id='test-cancel-003',
        filename='si519.wav',
        language='zh',
        total_seconds=None,
        processed_seconds=0.0,
        status='running',
        cancel_event=threading.Event(),
        subscribers=set(),
        transcript=[],
        temp_file_path=test_file
    )

    def cancel_after_delay():
        """延迟3秒后取消任务"""
        time.sleep(3)
        print("3秒后取消任务...")
        state.cancel_event.set()

    # 启动取消线程
    cancel_thread = threading.Thread(target=cancel_after_delay, daemon=True)
    cancel_thread.start()

    print(f"开始转录文件: {test_file} (将在3秒后取消)")
    start_time = time.time()

    # 运行转录任务
    file_transcription_stream_service.run_task(state, state.temp_file_path)

    end_time = time.time()
    print(f"任务结束，耗时: {end_time - start_time:.2f}秒")
    print(f"任务状态: {state.status}")
    print(f"转录结果数量: {len(state.transcript)}")

    return state.status == 'cancelled'


def test_error_handling():
    """错误处理测试"""
    print("\n" + "=" * 50)
    print("测试4: 错误处理")
    print("=" * 50)

    # 使用不存在的文件
    non_existent_file = '../temp_audio/non_existent.wav'

    # 创建任务状态
    state = FileStreamTaskState(
        task_id='test-error-004',
        filename='non_existent.wav',
        language='zh',
        total_seconds=None,
        processed_seconds=0.0,
        status='running',
        cancel_event=threading.Event(),
        subscribers=set(),
        transcript=[],
        temp_file_path=non_existent_file
    )

    print(f"尝试转录不存在的文件: {non_existent_file}")
    start_time = time.time()

    # 运行转录任务
    file_transcription_stream_service.run_task(state, state.temp_file_path)

    end_time = time.time()
    print(f"任务结束，耗时: {end_time - start_time:.2f}秒")
    print(f"任务状态: {state.status}")

    return state.status == 'error'


def test_service_methods():
    """测试服务方法"""
    print("\n" + "=" * 50)
    print("测试5: 服务方法测试")
    print("=" * 50)

    # 测试创建任务
    print("测试创建任务...")
    task_state = file_transcription_stream_service.create_task(
        filename='test.wav',
        language='zh',
        temp_file_path='../temp_audio/test.wav'
    )
    print(f"创建任务成功: {task_state.task_id}")

    # 测试停止任务
    print("测试停止任务...")
    result = file_transcription_stream_service.stop_task(task_state.task_id)
    print(f"停止任务结果: {result}")

    # 测试停止不存在的任务
    print("测试停止不存在的任务...")
    result = file_transcription_stream_service.stop_task('non-existent-task')
    print(f"停止不存在任务结果: {result}")

    return True


def main():
    """主测试函数"""
    print("文件流式转录服务测试开始")
    print("=" * 60)

    # 检查必要的目录和文件
    if not os.path.exists('../temp_audio'):
        print("创建 temp_audio 目录...")
        os.makedirs('../temp_audio', exist_ok=True)

    test_results = []

    # 运行所有测试
    try:
        # 测试1: 基础转录
        result1 = test_basic_transcription()
        test_results.append(("基础转录测试", result1))

        # 测试2: WebSocket连接
        result2 = test_with_websocket()
        test_results.append(("WebSocket连接测试", result2))

        # 测试3: 任务取消
        result3 = test_cancellation()
        test_results.append(("任务取消测试", result3))

        # 测试4: 错误处理
        result4 = test_error_handling()
        test_results.append(("错误处理测试", result4))

        # 测试5: 服务方法
        result5 = test_service_methods()
        test_results.append(("服务方法测试", result5))

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

    # 显示测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "通过" if result else "失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("🎉 所有测试都通过了！")
    else:
        print("⚠️  部分测试失败，请检查相关功能")

# Whisper模型直接测试
model = WhisperModel(
    "large-v3-turbo",
    device= "cpu",
    compute_type="int8",
    cpu_threads=8,
    num_workers=1
)
audio = "../test_audio/si519.wav"

if __name__ == '__main__':
    main()

    segments, info = model.transcribe(audio)
    # Detected language 'en' with probability 0.964498
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    # 生成器对象只能安全遍历一次，若需要多次遍历需要转为列表
    segments = list(segments)
    for segment in segments:
        # [0.00s -> 7.00s]  That added traffic means rising streams of dimes and quarters at tall games.
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

    print(len(list(segments)))
