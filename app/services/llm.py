"""
LLM服务类
基于现有的ChatLLM，添加流式输出支持
"""

from typing import AsyncGenerator
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionAssistantMessageParam
)
from openai import OpenAI
import asyncio
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from app.config import LLM_MODEL

model_name = LLM_MODEL["model_name"]
api_key = LLM_MODEL["api_key"]
base_url = LLM_MODEL["base_url"]


class ChatLLM:
    """聊天LLM服务，支持流式输出"""

    def __init__(self, model_name: str = model_name):
        self.api_key = api_key
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )
        self.model_name = model_name

    '''
    消息格式：
    messages = [
    ChatCompletionSystemMessageParam(content="You are a helpful assistant."),
    ChatCompletionUserMessageParam(content="Hello!")
    ]'''

    def chat(self, messages, temperature, top_p) -> str:
        """普通接口"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
        )
        return response.choices[0].message.content

    async def chat_stream(self, messages) -> AsyncGenerator[str, None]:
        """流式接口"""

        # 创建队列用于在线程间传递数据
        data_queue = queue.Queue()
        error_occurred = threading.Event()

        def _sync_stream():
            """同步流式生成器，在单独线程中运行"""
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stream=True
                )

                for chunk in response:
                    if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        if hasattr(choice, "delta") and hasattr(choice.delta, "content") and choice.delta.content:
                            data_queue.put(('data', choice.delta.content))

                # 标记完成
                data_queue.put(('done', None))

            except Exception as e:
                print(f"Stream error: {e}")
                data_queue.put(('error', str(e)))
                error_occurred.set()

        # 在单独线程中启动同步流式调用
        stream_thread = threading.Thread(target=_sync_stream)
        stream_thread.daemon = True
        stream_thread.start()

        # 异步消费队列中的数据
        while True:
            try:
                # 非阻塞获取数据
                item_type, item_data = data_queue.get(timeout=0.1)

                if item_type == 'data':
                    yield item_data
                elif item_type == 'done':
                    break
                elif item_type == 'error':
                    yield f"错误: {item_data}"
                    break

            except queue.Empty:
                # 检查是否有错误发生
                if error_occurred.is_set():
                    break
                # 短暂等待后继续
                await asyncio.sleep(0.01)
            except Exception as e:
                yield f"处理错误: {str(e)}"
                break


if __name__ == '__main__':
    msg = [{"role": "user", "content": "讲个笑话"}]
    async def test():
        chat = ChatLLM()
        async for chunk in chat.chat_stream(msg):
            print(chunk, end='')

    asyncio.run(test())