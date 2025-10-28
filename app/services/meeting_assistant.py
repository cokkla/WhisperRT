"""
会议助手Agent服务
"""
import logging
from typing import Dict, List, Optional, AsyncGenerator
import json
import asyncio
from datetime import datetime

from app.prompts.text_refiner_prompt import TEXT_REFINER_PROMPT
from app.prompts.topic_identifier_prompt import TOPIC_IDENTIFIER_PROMPT
from app.prompts.key_points_extractor_prompt import KEY_POINTS_EXTRACTOR_PROMPT
from app.prompts.decision_extractor_prompt import DECISION_EXTRACTOR_PROMPT
from app.prompts.action_items_extractor_prompt import ACTION_ITEMS_EXTRACTOR_PROMPT
from app.prompts.minutes_generator_prompt import MINUTES_GENERATOR_PROMPT


class MarkdownAgent:
    """处理与AI模型的交互，生成或处理Markdown格式的内容"""
    
    def __init__(
        self,
        chat_llm,
        sys_prompt: str,
        name: str,
        temperature: float = 0.8,
        top_p: float = 0.8,
        use_memory: bool = False,
        first_reply: str = "明白了。",
        is_speak: bool = True,
    ):
        self.chat_llm = chat_llm
        self.sys_prompt = sys_prompt
        self.temperature = temperature
        self.top_p = top_p
        self.use_memory = use_memory
        self.is_speak = is_speak
        self.name = name
        
        self.history = [{"role": "user", "content": self.sys_prompt}]
        
        if first_reply:
            self.history.append({"role": "assistant", "content": first_reply})
        else:
            resp = chat_llm.chat(messages=self.history)
            self.history.append({"role": "assistant", "content": resp})
    
    def query(self, user_input: str) -> str:
        """根据输入查询回复"""
        resp = self.chat_llm.chat(
            messages=self.history + [{"role": "user", "content": user_input}],
            temperature=self.temperature,
            top_p=self.top_p,
        )
        if self.use_memory:
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": resp})
        
        return resp
    
    async def query_stream(self, user_input: str) -> AsyncGenerator[str, None]:
        """流式查询回复"""
        messages = self.history + [{"role": "user", "content": user_input}]
        
        async for chunk in self.chat_llm.chat_stream(messages):
            if self.use_memory:
                # 流式模式下暂不更新记忆，在完成后统一更新
                pass
            yield chunk
    
    def get_output(self, input_content: str, output_keys: List[str]) -> Dict[str, str]:
        """解析类md格式中 # key 的内容"""
        resp = self.query(input_content)
        lines = resp.split("\n")
        sections = {}
        current_section = ""
        
        for line in lines:
            if line.startswith("# ") or line.startswith(" # "):
                current_section = line[2:].strip()
                sections[current_section] = []
            else:
                if current_section:
                    sections[current_section].append(line.strip())
        
        for key in sections.keys():
            sections[key] = "\n".join(sections[key]).strip()

        for k in output_keys:
            # matched_keys = [key for key in sections if k in key]
            # if not matched_keys:
            if k not in sections or len(sections[k]) == 0:
                raise ValueError(f"fail to parse {k} in output:\n{resp}\n\n")
        
        return sections
    
    async def get_output_stream(self, input_content: str, output_keys: List[str]):
        """流式解析输出"""
        full_response = ""
        async for chunk in self.query_stream(input_content):
            full_response += chunk
            yield {"partial": chunk}
        
        # 解析完整响应
        lines = full_response.split("\n")
        sections = {}
        current_section = ""
        
        for line in lines:
            if line.startswith("# ") or line.startswith(" # "):
                current_section = line[2:].strip()
                sections[current_section] = []
            else:
                if current_section:
                    sections[current_section].append(line.strip())
        
        for key in sections.keys():
            sections[key] = "\n".join(sections[key]).strip()
        
        for k in output_keys:
            if (k not in sections) or (len(sections[k]) == 0):
                raise ValueError(f"fail to parse {k} in output:\n{full_response}\n\n")
        
        yield {"complete": sections}
    
    def invoke(self, inputs: Dict[str, str], output_keys: List[str]) -> Dict[str, str]:
        """调用解析后的结果"""
        input_content = ""
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                input_content += f"# {k}\n{v}\n\n"
        
        return self.get_output(input_content, output_keys)
    
    async def invoke_stream(self, inputs: Dict[str, str], output_keys: List[str]) -> AsyncGenerator[Dict[str, str], None]:
        """流式调用"""
        input_content = ""
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                input_content += f"# {k}\n{v}\n\n"

        async for result in self.get_output_stream(input_content, output_keys):
            yield result
    
    def clear_memory(self):
        """清除记忆"""
        if self.use_memory:
            self.history = self.history[:2]


class MemoryManager:
    """记忆管理器，用于处理长文本的分段处理"""
    
    def __init__(self, max_chunk_size: int = 2000):
        self.max_chunk_size = max_chunk_size
        self.processed_chunks = []
        self.summary_memory = ""
    
    def should_split(self, text: str) -> bool:
        """判断是否需要分割文本"""
        return len(text) > self.max_chunk_size
    
    def split_text(self, text: str) -> List[str]:
        """分割文本为多个块"""
        if not self.should_split(text):
            return [text]
        
        chunks = []
        sentences = text.split('。')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # 单个句子太长，强制分割
                    chunks.append(sentence)
            else:
                current_chunk += sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def create_summary(self, chunk: str) -> str:
        """为文本块创建摘要"""
        # 简单的摘要策略：提取前几句和后几句
        sentences = chunk.split('。')
        if len(sentences) <= 4:
            return chunk
        
        summary = sentences[0] + "。" + sentences[1] + "。" + "..." + sentences[-2] + "。" + sentences[-1] + "。"
        return summary
    
    def update_memory(self, new_summary: str):
        """更新记忆库"""
        if self.summary_memory:
            self.summary_memory += "\n\n" + new_summary
        else:
            self.summary_memory = new_summary


class MeetingAssistantAgent:
    """会议助手Agent，整合所有功能模块"""
    
    def __init__(self, chat_llm):
        self.chat_llm = chat_llm
        self.memory_manager = MemoryManager()
        
        # 初始化各个功能模块
        self.text_refiner = MarkdownAgent(
            chat_llm=chat_llm,
            sys_prompt=TEXT_REFINER_PROMPT,
            name="TextRefiner",
            temperature=0.2,  # 低创造性，高准确性
            use_memory=False
        )
        
        self.topic_identifier = MarkdownAgent(
            chat_llm=chat_llm,
            sys_prompt=TOPIC_IDENTIFIER_PROMPT,
            name="TopicIdentifier",
            temperature=0.5,
            use_memory=False
        )
        
        self.key_points_extractor = MarkdownAgent(
            chat_llm=chat_llm,
            sys_prompt=KEY_POINTS_EXTRACTOR_PROMPT,
            name="KeyPointsExtractor",
            temperature=0.6,
            use_memory=False
        )
        
        self.decision_extractor = MarkdownAgent(
            chat_llm=chat_llm,
            sys_prompt=DECISION_EXTRACTOR_PROMPT,
            name="DecisionExtractor",
            temperature=0.4,
            use_memory=False
        )
        
        self.action_items_extractor = MarkdownAgent(
            chat_llm=chat_llm,
            sys_prompt=ACTION_ITEMS_EXTRACTOR_PROMPT,
            name="ActionItemsExtractor",
            temperature=0.4,
            use_memory=False
        )
        
        self.minutes_generator = MarkdownAgent(
            chat_llm=chat_llm,
            sys_prompt=MINUTES_GENERATOR_PROMPT,
            name="MinutesGenerator",
            temperature=0.7,
            use_memory=False
        )
    
    async def refine_text(self, transcription_text: str) -> str:
        """文本润色"""
        result = self.text_refiner.invoke(
            inputs={"原始转录文本": transcription_text},
            output_keys=["润色结果"]
        )
        return result["润色结果"]
    
    async def identify_topic(self, refined_text: str) -> Dict[str, str]:
        """识别会议主题"""
        result = self.topic_identifier.invoke(
            inputs={"会议讨论文本": refined_text},
            output_keys=["会议主题", "会议背景", "主要议题"]
        )
        return result
    
    async def extract_key_points(self, refined_text: str, topics: List[str]) -> Dict[str, str]:
        """提取讨论要点"""
        topics_text = "\n".join([f"- {topic}" for topic in topics])
        result = self.key_points_extractor.invoke(
            inputs={
                "会议讨论文本": refined_text,
                "主要议题": topics_text
            },
            output_keys=["讨论要点"]
        )
        return result
    
    async def extract_decisions(self, refined_text: str) -> Dict[str, str]:
        """提取决策事项"""
        result = self.decision_extractor.invoke(
            inputs={"会议讨论文本": refined_text},
            output_keys=["决策事项"]
        )
        return result
    
    async def extract_action_items(self, refined_text: str) -> Dict[str, str]:
        """提取行动事项"""
        result = self.action_items_extractor.invoke(
            inputs={"会议讨论文本": refined_text},
            output_keys=["行动事项"]
        )
        return result
    
    async def generate_minutes_stream(
        self, 
        refined_text: str, 
        meeting_info: Dict[str, str],
        topic_info: Dict[str, str],
        key_points: Dict[str, str],
        decisions: Dict[str, str],
        action_items: Dict[str, str]
    ):
        """流式生成会议纪要"""
        
        # 准备输入数据
        inputs = {
            "会议基本信息": json.dumps(meeting_info, ensure_ascii=False, indent=2),
            "会议背景": topic_info.get("会议背景", ""),
            "讨论议题": topic_info.get("主要议题", ""),
            "讨论要点": key_points.get("讨论要点", ""),
            "决策事项": decisions.get("决策事项", ""),
            "行动事项": action_items.get("行动事项", "")
        }
        
        # 流式生成
        async for result in self.minutes_generator.invoke_stream(
            inputs=inputs,
            output_keys=["会议纪要"]
        ):
            yield result

    async def process_meeting_stream(
        self, 
        transcription_text: str, 
        meeting_info: Dict[str, str]
    ) -> AsyncGenerator[Dict[str, str], None]:
        """流式处理会议内容，生成会议纪要"""
        
        # 步骤1：文本润色
        yield {"step": "refining", "status": "processing", "message": "正在润色文本..."}
        refined_text = await self.refine_text(transcription_text)
        yield {"step": "refining", "status": "completed", "message": "文本润色完成"}
        logging.debug("文本润色完成")
        # logging.debug(refined_text)

        # 步骤2：主题识别
        yield {"step": "topic_identification", "status": "processing", "message": "正在识别会议主题..."}
        topic_info = await self.identify_topic(refined_text)
        yield {"step": "topic_identification", "status": "completed", "message": "主题识别完成"}
        logging.debug("主题识别完成")
        # logging.debug(topic_info)

        # 步骤3：要点提炼
        yield {"step": "key_points", "status": "processing", "message": "正在提炼讨论要点..."}
        topics = topic_info.get("主要议题", "").split('\n')
        topics = [t.strip('- ').strip() for t in topics if t.strip()]
        key_points = await self.extract_key_points(refined_text, topics)
        yield {"step": "key_points", "status": "completed", "message": "要点提炼完成"}
        logging.debug("要点提炼完成")
        # logging.debug(key_points)

        # 步骤4：决策提取
        yield {"step": "decisions", "status": "processing", "message": "正在提取决策事项..."}
        decisions = await self.extract_decisions(refined_text)
        yield {"step": "decisions", "status": "completed", "message": "决策提取完成"}
        logging.debug("决策提取完成")
        # logging.debug(decisions)

        # 步骤5：行动事项提取
        yield {"step": "action_items", "status": "processing", "message": "正在提取行动事项..."}
        action_items = await self.extract_action_items(refined_text)
        yield {"step": "action_items", "status": "completed", "message": "行动事项提取完成"}
        logging.debug("行动事项提取完成")
        # logging.debug(action_items)

        # 步骤6：生成会议纪要
        yield {"step": "generating", "status": "processing", "message": "正在生成会议纪要..."}

        # 累积生成的会议纪要内容
        async for result in self.generate_minutes_stream(
            refined_text, meeting_info, topic_info, key_points, decisions, action_items
        ):
            if "partial" in result:
                yield {"step": "generating", "status": "streaming", "content": result['partial']}
            elif 'complete' in result:
                yield {"step": "generating", "status": "completed", "message": "会议纪要生成完成", "content": result['complete']}

        logging.debug("会议纪要生成完成")
