"""
LLM (大语言模型) 服务测试脚本

功能说明：
- 测试 ChatLLM 类的基本功能
- 验证与阿里云通义千问 API 的连接
- 测试普通对话和流式输出功能
- 验证 API 密钥和基础 URL 配置是否正确

使用方法：
python test/test_llm.py

依赖：
- openai 库（用于与通义千问 API 通信）
- 需要有效的 API 密钥

注意：
- 此文件包含硬编码的 API 密钥，仅用于测试
- 生产环境中应使用环境变量或配置文件管理密钥
"""

from random import choices
from app.config import LLM_MODEL

from openai import OpenAI

model_name = LLM_MODEL["model_name"]
api_key = LLM_MODEL["api_key"]
base_url = LLM_MODEL["base_url"]

class ChatLLM:
    def __init__(self, model_name=model_name):
        self.client= OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model_name = model_name

    def chat(self, messages):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.8,
            top_p=3
        )

        return response.choices[0].message.content

    def chat_stream(self, messages):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True
        )

        for chunk in response:
            if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                    # print(choice.delta.content, end='', flush=True)
                    yield choice.delta.content


if __name__ == "__main__":
    prompt = "请用一句话介绍自己"
    messages = [{"role": "user", "content": prompt}]
    # chat_lmm(prompt)

    chatLLM = ChatLLM()
    # print('直接输出')
    # print(chatLLM.chat(messages))

    print('-'*50)
    print('流式输出')
    for res in chatLLM.chat_stream(messages):
        print(res, end='', flush=True)



