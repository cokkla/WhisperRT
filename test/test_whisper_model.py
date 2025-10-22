"""
Whisper 模型直接测试脚本

功能说明：
- 直接测试 faster-whisper 模型的基本功能
- 验证模型加载、音频转录、语言检测等核心功能
- 测试不同音频文件的转录效果
- 验证模型配置参数是否正确

使用方法：
python test/test_whisper_model.py

依赖：
- faster_whisper.WhisperModel
- 需要测试音频文件：test_audio/市民专线.mp3

模型配置：
- 模型：large-v3-turbo
- 设备：CPU
- 计算类型：int8
- CPU线程数：8
- 工作进程数：1

输出信息：
- 检测到的语言和概率
- 每个片段的开始时间、结束时间和文本内容
- 总片段数量
"""

from faster_whisper import WhisperModel

# 初始化 Whisper 模型
model = WhisperModel(
    "large-v3-turbo",
    device="cpu",
    compute_type="int8",
    cpu_threads=8,
    num_workers=1
)

# 测试音频文件路径
audio = "../test_audio/市民专线.mp3"

if __name__ == '__main__':
    print("开始测试 Whisper 模型...")
    print("=" * 50)
    
    # 执行转录
    segments, info = model.transcribe(audio)
    
    # 输出语言检测结果
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    
    # 生成器对象只能安全遍历一次，若需要多次遍历需要转为列表
    segments = list(segments)
    
    print(f"\n转录结果 (共 {len(segments)} 个片段):")
    print("-" * 50)
    
    # 输出每个片段的详细信息
    for segment in segments:
        # [0.00s -> 7.00s]  That added traffic means rising streams of dimes and quarters at tall games.
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    
    print(f"\n总片段数量: {len(segments)}")
    print("Whisper 模型测试完成！")
