"""
文件流式转录服务简化测试脚本

功能说明：
- 快速测试 file_transcription_stream_service.run_task 方法
- 专门用于测试 run_task 功能的核心逻辑
- 包含基础功能测试和取消功能测试
- 提供简化的测试流程，便于快速验证

使用方法：
python test/test_run_task_simple.py

依赖：
- app.services.file_transcription_stream.file_transcription_stream_service
- app.services.file_transcription_stream.FileStreamTaskState
- 需要测试音频文件：test_audio/市民专线.mp3 或 test_audio/市民专线.mp3

测试场景：
1. 基础 run_task 功能测试
2. run_task 取消功能测试
"""

import os
import time
import threading

from app.services.file_transcription_stream import file_transcription_stream_service, FileStreamTaskState

file_path = "test/test_audio/市民专线.mp3"

def quick_test_run_task():
    """快速测试 run_task 方法"""
    print("快速测试 file_transcription_stream_service.run_task")
    print("=" * 50)
    
    # 检查测试文件
    test_file = file_path
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        print("请确保 test_audio/市民专线.mp3 文件存在")
        return False
    
    print(f"✅ 找到测试文件: {test_file}")
    
    # 创建任务状态
    state = FileStreamTaskState(
        task_id='quick-test-001',
        filename='市民专线.mp3',
        language='auto',
        total_seconds=None,
        processed_seconds=0.0,
        status='running',
        cancel_event=threading.Event(),
        subscribers=set(),
        transcript=[],
        temp_file_path=test_file
    )
    
    print(f"📝 创建任务: {state.task_id}")
    print(f"🎵 文件: {state.filename}")
    print(f"🌐 语言: {state.language}")
    print(f"📁 路径: {state.temp_file_path}")
    
    # 开始测试
    print("\n🚀 开始运行 run_task...")
    start_time = time.time()
    
    try:
        # 调用 run_task 方法
        file_transcription_stream_service.run_task(state, state.temp_file_path)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ run_task 执行完成")
        print(f"⏱️  耗时: {duration:.2f}秒")
        print(f"📊 任务状态: {state.status}")
        print(f"📝 转录结果数量: {len(state.transcript)}")
        
        # 显示转录结果
        if state.transcript:
            print(f"\n📄 转录结果:")
            for i, item in enumerate(state.transcript, 1):
                print(f"  {i}. [{item['timestamp']}] {item['text']}")
                print(f"     置信度: {item['confidence']:.3f}")
        else:
            print("⚠️  没有转录结果")
        
        # 判断测试是否成功
        success = state.status in ['completed', 'cancelled']
        if success:
            print(f"\n🎉 测试成功! 状态: {state.status}")
        else:
            print(f"\n❌ 测试失败! 状态: {state.status}")
        
        return success
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n❌ run_task 执行出错")
        print(f"⏱️  耗时: {duration:.2f}秒")
        print(f"🚨 错误信息: {str(e)}")
        
        import traceback
        print(f"\n📋 详细错误:")
        traceback.print_exc()
        
        return False


def test_with_cancellation():
    """测试带取消功能的 run_task"""
    print("\n" + "=" * 50)
    print("测试 run_task 取消功能")
    print("=" * 50)
    
    test_file = file_path
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    # 创建任务状态
    state = FileStreamTaskState(
        task_id='cancel-test-002',
        filename='市民专线.mp3',
        language='zh',
        total_seconds=None,
        processed_seconds=0.0,
        status='running',
        cancel_event=threading.Event(),
        subscribers=set(),
        transcript=[],
        temp_file_path=test_file
    )
    
    def cancel_after_2_seconds():
        """2秒后取消任务"""
        time.sleep(2)
        print("🛑 2秒后取消任务...")
        state.cancel_event.set()
    
    # 启动取消线程
    cancel_thread = threading.Thread(target=cancel_after_2_seconds, daemon=True)
    cancel_thread.start()
    
    print(f"🚀 开始运行 run_task (2秒后自动取消)...")
    start_time = time.time()
    
    try:
        file_transcription_stream_service.run_task(state, state.temp_file_path)
        
        end_time = time.time()
        duration = end_time - start_time

        # 运行到此步时 state.status='completed'
        print(f"\n✅ run_task 执行完成")
        print(f"⏱️  耗时: {duration:.2f}秒")
        print(f"📊 任务状态: {state.status}")
        print(f"📝 转录结果数量: {len(state.transcript)}")
        
        success = state.status == 'cancelled'
        if success:
            print(f"\n🎉 取消测试成功!")
        else:
            print(f"\n❌ 取消测试失败! 状态: {state.status}")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 取消测试出错: {str(e)}")
        return False


def main():
    """主函数"""
    print("file_transcription_stream_service.run_task 测试")
    print("=" * 60)
    
    # 检查目录
    if not os.path.exists('test/test_audio'):
        print("创建 test_audio 目录...")
        os.makedirs('test/test_audio', exist_ok=True)
    
    results = []
    
    # 测试1: 基础功能
    print("测试1: 基础 run_task 功能")
    result1 = quick_test_run_task()
    results.append(("基础功能", result1))
    
    # 测试2: 取消功能
    print("\n测试2: run_task 取消功能")
    result2 = test_with_cancellation()
    results.append(("取消功能", result2))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("🎉 所有测试都通过了！run_task 方法工作正常")
    else:
        print("⚠️  部分测试失败，请检查 run_task 方法")


if __name__ == '__main__':
    main()
