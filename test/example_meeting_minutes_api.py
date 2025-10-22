"""
会议纪要API使用示例
演示如何使用会议纪要生成API
"""

import requests
import json
import time


def test_meeting_minutes_api():
    """测试会议纪要API"""
    
    base_url = "http://localhost:5444/api/meeting/minutes"
    
    # 1. 创建会议纪要生成任务
    print("1. 创建会议纪要生成任务...")
    
    request_data = {
        "transcription_text": """
        大家好，今天我们开个会讨论一下新产品的开发计划划。
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
        """,
        "meeting_info": {
            "topic": "新产品开发计划讨论",
            "date": "2024-01-15",
            "location": "会议室A",
            "attendees": ["张三", "李四", "王五"],
            "host": "项目经理",
            "recorder": "会议记录员"
        }
    }
    
    response = requests.post(f"{base_url}/generate", json=request_data)
    if response.status_code == 200:
        result = response.json()
        task_id = result["task_id"]
        print(f"任务创建成功，任务ID: {task_id}")
    else:
        print(f"任务创建失败: {response.text}")
        return
    
    # 2. 流式获取生成进度
    print("\n2. 流式获取生成进度...")
    
    stream_response = requests.get(f"{base_url}/stream/{task_id}", stream=True)
    
    if stream_response.status_code == 200:
        print("开始流式接收数据...")
        print("-" * 50)
        
        for line in stream_response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # 去掉 'data: ' 前缀
                    try:
                        result = json.loads(data)
                        
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
                                print(f"\n\n会议纪要生成完成: {result.get('message')}")
                        
                    except json.JSONDecodeError:
                        print(f"解析JSON失败: {data}")
    else:
        print(f"流式获取失败: {stream_response.text}")
        return
    
    # 3. 检查任务状态
    print("\n3. 检查任务状态...")
    
    status_response = requests.get(f"{base_url}/status/{task_id}")
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"任务状态: {status['status']}")
        print(f"创建时间: {status['created_at']}")
        print(f"结果长度: {status['result_length']} 字符")
    
    # 4. 下载Markdown格式文档
    print("\n4. 下载Markdown格式文档...")
    
    download_response = requests.get(f"{base_url}/download/{task_id}?format=markdown")
    if download_response.status_code == 200:
        with open("meeting_minutes.md", "wb") as f:
            f.write(download_response.content)
        print("Markdown文档下载成功: meeting_minutes.md")
    else:
        print(f"Markdown下载失败: {download_response.text}")
    
    # 5. 下载Word格式文档
    print("\n5. 下载Word格式文档...")
    
    word_response = requests.get(f"{base_url}/download/{task_id}?format=word")
    if word_response.status_code == 200:
        with open("meeting_minutes.docx", "wb") as f:
            f.write(word_response.content)
        print("Word文档下载成功: meeting_minutes.docx")
    else:
        print(f"Word下载失败: {word_response.text}")
    
    # 6. 列出所有任务
    print("\n6. 列出所有任务...")
    
    tasks_response = requests.get(f"{base_url}/tasks")
    if tasks_response.status_code == 200:
        tasks = tasks_response.json()
        print(f"总共有 {len(tasks['tasks'])} 个任务:")
        for task in tasks['tasks']:
            print(f"  - {task['task_id'][:8]}... : {task['status']} (创建于 {task['created_at']})")
    
    print("\n测试完成！")


if __name__ == "__main__":
    test_meeting_minutes_api()
