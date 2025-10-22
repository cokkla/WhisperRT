"""
会议纪要生成功能测试脚本

功能说明：
- 测试会议纪要生成服务的完整流程
- 模拟会议转录文本，测试流式处理会议内容
- 验证文本润色、主题识别、要点提炼、决策提取、行动事项等各个步骤
- 测试 MeetingAssistantAgent 的 process_meeting_stream 方法

使用方法：
python test/test_meeting_minutes.py

依赖：
- app.services.meeting_assistant.MeetingAssistantAgent
- app.services.llm.ChatLLM
"""

import asyncio
import json
from app.services.meeting_assistant import MeetingAssistantAgent
from app.services.llm import ChatLLM


async def test_meeting_minutes():
    """测试会议纪要生成功能"""
    
    # 初始化服务
    chat_llm = ChatLLM()
    meeting_assistant = MeetingAssistantAgent(chat_llm)
    
    # 模拟会议转录文本
    transcription_text = """
    大家好，今天我们开个会讨论一下新产品的开发计划。
    首先，我想了解一下目前项目的进展情况。
    张三：目前我们已经完成了需求分析，正在进行技术选型。
    李四：是的，我们初步选择了React作为前端框架，Node.js作为后端。
    王五：关于数据库，我建议使用MongoDB，因为我们的数据结构比较灵活。
    好的，那我们就确定使用这个技术栈。接下来讨论一下时间安排。
    张三：我预计前端开发需要4周时间。
    李四：后端开发也需要4周，我们可以并行进行。
    王五：测试和部署大概需要2周时间。
    那整个项目预计10周完成。大家有什么问题吗？
    李四：我建议我们每周开一次进度会议。
    王五：同意，这样可以及时发现问题。
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
    
    print("开始测试会议纪要生成...")
    print("=" * 50)
    
    try:
        # 流式处理会议内容
        full_content = ""
        async for result in meeting_assistant.process_meeting_stream(transcription_text, meeting_info):
            if result.get("step") == "refining":
                print(f"文本润色: {result.get('status')} - {result.get('message')}")
            elif result.get("step") == "topic_identification":
                print(f"主题识别: {result.get('status')} - {result.get('message')}")
            elif result.get("step") == "key_points":
                print(f"要点提炼: {result.get('status')} - {result.get('message')}")
            elif result.get("step") == "decisions":
                print(f"决策提取: {result.get('status')} - {result.get('message')}")
            elif result.get("step") == "action_items":
                print(f"行动事项: {result.get('status')} - {result.get('message')}")
            elif result.get("step") == "generating":
                if result.get("status") == "streaming":
                    print(result.get("content", ""), end="", flush=True)
                elif result.get("status") == "completed":
                    full_content = result.get("content", "")
                    print(f"\n\n会议纪要生成完成: {result.get('message')}")
                    print(f"✓ 生成的内容长度: {len(full_content)} 字符")
        
        # 验证修复结果
        print("\n" + "=" * 50)
        if full_content and len(full_content.strip()) > 0:
            print("✓ 修复成功！会议纪要内容已正确保存")
            print(f"✓ 内容长度: {len(full_content)} 字符")
            print("\n生成的会议纪要预览:")
            print("-" * 30)
            print(full_content[:300] + "..." if len(full_content) > 300 else full_content)
        else:
            print("❌ 修复失败！内容为空")
        print("=" * 50)
    
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_meeting_minutes())
