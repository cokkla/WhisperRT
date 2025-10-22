"""
会议纪要生成系统演示启动脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.meeting_assistant import MeetingAssistantAgent
from app.services.llm import ChatLLM


async def demo_meeting_minutes():
    """演示会议纪要生成功能"""
    
    print("=" * 60)
    print("会议纪要生成系统演示")
    print("=" * 60)
    
    # 初始化服务
    print("正在初始化服务...")
    chat_llm = ChatLLM()
    meeting_assistant = MeetingAssistantAgent(chat_llm)
    print("✓ 服务初始化完成")
    
    # 模拟会议转录文本
    transcription_text = """
    大家好，今天我们开个会讨论一下新产品的开发计划。
    首先，我想了解一下目前项目的进展情况。
    目前我们已经完成了需求分析，正在进行技术选。
    是的，我们初步选择了React作为前端框架，Node.js作为后端。
    关于数据库，我建议使用MongoDB，因为我们的数据结构比较灵活。
    好的，那我们就确定使用这个技术栈。接下来讨论一下时间安排。
    我预计前端开发需要4周时间。
    后端开发也需要4周，我们可以并行进行。
    测试和部署大概需要2周时间。
    那整个项目预计10周完成。大家有什么问题吗？
    我建议我们每周开一次进度会议。
    同意，这样可以及时发现问题。
    好的，那就这样定了。下次会议时间定在下周二下午2点。
    会议结束，大家辛苦了。
    """
    
    # 模拟会议信息
    meeting_info = {
        "meeting_topic": "新产品开发计划讨论",
        "meeting_date": "2024-01-15",
        "meeting_location": "会议室A",
        "attendees": "张三, 李四, 王五",
        "meeting_host": "项目经理",
        "recorder": "会议记录员"
    }
    
    print(f"\n会议主题: {meeting_info['meeting_topic']}")
    print(f"会议时间: {meeting_info['meeting_date']}")
    print(f"参会人员: {meeting_info['attendees']}")
    print("\n开始生成会议纪要...")
    print("-" * 60)
    
    try:
        # 流式处理会议内容
        step_count = 0
        async for result in meeting_assistant.process_meeting_stream(transcription_text, meeting_info):
            step_count += 1
            
            if result.get("step") == "refining":
                print(f"[{step_count}] 文本润色: {result.get('status')} - {result.get('message')}")
            elif result.get("step") == "topic_identification":
                print(f"[{step_count}] 主题识别: {result.get('status')} - {result.get('message')}")
            elif result.get("step") == "key_points":
                print(f"[{step_count}] 要点提炼: {result.get('status')} - {result.get('message')}")
            elif result.get("step") == "decisions":
                print(f"[{step_count}] 决策提取: {result.get('status')} - {result.get('message')}")
            elif result.get("step") == "action_items":
                print(f"[{step_count}] 行动事项: {result.get('status')} - {result.get('message')}")
            elif result.get("step") == "generating":
                if result.get("status") == "streaming":
                    print(result.get("content", ""), end="", flush=True)
                elif result.get("status") == "completed":
                    print(f"\n\n[{step_count}] 会议纪要生成完成: {result.get('message')}")
        
        print("\n" + "=" * 60)
        print("✓ 会议纪要生成完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("启动会议纪要生成系统演示...")
    asyncio.run(demo_meeting_minutes())
