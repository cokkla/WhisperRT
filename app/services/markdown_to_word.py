"""
Markdown到Word转换服务
整合解析器和构建器，提供完整的转换功能
"""
import os
import logging
from typing import Optional
from docx import Document
from app.services.markdown_parser import MarkdownParser
from app.services.word_builder import WordDocumentBuilder
from app.core.logging import logger


class MarkdownToWordConverter:
    """Markdown到Word转换器"""
    
    def __init__(self):
        self.parser = MarkdownParser()
        self.builder = WordDocumentBuilder()
    
    def convert(self, markdown_content: str) -> Document:
        """
        将Markdown内容转换为Word文档
        
        Args:
            markdown_content: Markdown内容字符串
            
        Returns:
            转换后的Word文档对象
        """
        try:
            logger.info("开始解析Markdown内容")
            
            # 解析Markdown内容
            elements = self.parser.parse(markdown_content)
            logger.info(f"解析完成，共识别到 {len(elements)} 个元素")
            
            # 创建新的Word构建器实例，避免重复内容
            builder = WordDocumentBuilder()
            logger.info("开始构建Word文档")
            document = builder.build_document(elements)
            logger.info("Word文档构建完成")
            
            return document
            
        except Exception as e:
            logger.error(f"Markdown到Word转换失败: {str(e)}")
            raise
    
    def convert_and_save(self, markdown_content: str, output_path: str) -> str:
        """
        转换并保存Word文档
        
        Args:
            markdown_content: Markdown内容字符串
            output_path: 输出文件路径
            
        Returns:
            保存的文件路径
        """
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"创建输出目录: {output_dir}")
            
            # 转换文档
            document = self.convert(markdown_content)
            
            # 保存文档
            document.save(output_path)
            logger.info(f"Word文档已保存到: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"保存Word文档失败: {str(e)}")
            raise
    
    def get_conversion_stats(self, markdown_content: str) -> dict:
        """
        获取转换统计信息
        
        Args:
            markdown_content: Markdown内容字符串
            
        Returns:
            统计信息字典
        """
        try:
            elements = self.parser.parse(markdown_content)
            
            stats = {
                "total_elements": len(elements),
                "headings": 0,
                "paragraphs": 0,
                "tables": 0,
                "lists": 0,
                "code_blocks": 0,
                "empty_lines": 0
            }
            
            for element in elements:
                if element.type.value == "heading":
                    stats["headings"] += 1
                elif element.type.value == "paragraph":
                    stats["paragraphs"] += 1
                elif element.type.value == "table":
                    stats["tables"] += 1
                elif element.type.value == "list":
                    stats["lists"] += 1
                elif element.type.value == "code_block":
                    stats["code_blocks"] += 1
                elif element.type.value == "empty_line":
                    stats["empty_lines"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"获取转换统计信息失败: {str(e)}")
            return {"error": str(e)}
