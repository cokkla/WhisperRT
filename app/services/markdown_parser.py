"""
Markdown解析器
用于解析Markdown内容，识别各种元素（标题、段落、表格、列表、格式等）
"""
import re
from re import Match
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class ElementType(Enum):
    """Markdown元素类型"""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    CODE_BLOCK = "code_block"
    HORIZONTAL_RULE = "horizontal_rule"
    EMPTY_LINE = "empty_line"


@dataclass
class TextFormat:
    """文本格式信息"""
    bold: bool = False
    italic: bool = False
    text: str = ""


@dataclass
class MarkdownElement:
    """Markdown元素"""
    type: ElementType
    content: str
    level: Optional[int] = None  # 用于标题级别
    table_data: Optional[List[List[str]]] = None  # 用于表格数据
    list_items: Optional[List[str]] = None  # 用于列表项
    formatted_text: Optional[List[TextFormat]] = None  # 用于格式化文本


class MarkdownParser:
    """Markdown解析器"""
    
    def __init__(self):
        # 编译正则表达式以提高性能
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        self.table_separator_pattern = re.compile(r'^\s*\|.*\|\s*$')
        self.table_alignment_pattern = re.compile(r'^\s*\|[\s\-\|:]+\|\s*$')
        self.list_pattern = re.compile(r'^[\s]*[-*+]\s+(.+)$')
        self.numbered_list_pattern = re.compile(r'^[\s]*\d+\.\s+(.+)$')
        self.bold_pattern = re.compile(r'\*\*(.*?)\*\*')
        self.italic_pattern = re.compile(r'\*(.*?)\*')
        self.code_block_pattern = re.compile(r'^```')
        self.horizontal_rule_pattern = re.compile(r'^[-*_]{3,}$')
    
    def parse(self, content: str) -> List[MarkdownElement]:
        """
        解析Markdown内容
        
        Args:
            content: Markdown内容字符串
            
        Returns:
            解析后的元素列表
        """
        lines = content.split('\n')
        elements = []
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip()
            
            # 跳过空行
            if not line.strip():
                elements.append(MarkdownElement(
                    type=ElementType.EMPTY_LINE,
                    content=""
                ))
                i += 1
                continue
            
            # 检测代码块
            if self.code_block_pattern.match(line):
                code_content, end_index = self._parse_code_block(lines, i)
                elements.append(MarkdownElement(
                    type=ElementType.CODE_BLOCK,
                    content=code_content
                ))
                i = end_index
                continue
            
            # 检测表格
            if self._is_table_start(lines, i):
                table_data, end_index = self._parse_table(lines, i)
                elements.append(MarkdownElement(
                    type=ElementType.TABLE,
                    content="",
                    table_data=table_data
                ))
                i = end_index
                continue
            
            # 检测标题
            heading_match = self.heading_pattern.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                formatted_text = self._parse_text_formatting(title)
                elements.append(MarkdownElement(
                    type=ElementType.HEADING,
                    content=title,
                    level=level,
                    formatted_text=formatted_text
                ))
                i += 1
                continue
            
            # 检测列表
            if self._is_list_item(line):
                list_elements, end_index = self._parse_list(lines, i)
                # 将列表项作为独立的段落元素添加
                elements.extend(list_elements)
                i = end_index
                continue
            
            # 检测水平线
            if self.horizontal_rule_pattern.match(line):
                elements.append(MarkdownElement(
                    type=ElementType.HORIZONTAL_RULE,
                    content=""
                ))
                i += 1
                continue
            
            # 普通段落
            paragraph_lines = []
            while i < len(lines) and lines[i].strip() and not self._is_special_line(lines[i]):
                paragraph_lines.append(lines[i].strip())
                i += 1
            
            if paragraph_lines:
                paragraph_text = ' '.join(paragraph_lines)
                formatted_text = self._parse_text_formatting(paragraph_text)
                elements.append(MarkdownElement(
                    type=ElementType.PARAGRAPH,
                    content=paragraph_text,
                    formatted_text=formatted_text
                ))
        
        return elements
    
    def _is_special_line(self, line: str) -> Match[str] | None | bool:
        """检查是否为特殊行（标题、列表、表格等）"""
        line = line.strip()
        if not line:
            return False
        
        return (self.heading_pattern.match(line) or
                self.table_separator_pattern.match(line) or
                self.list_pattern.match(line) or
                self.numbered_list_pattern.match(line) or
                self.horizontal_rule_pattern.match(line) or
                self.code_block_pattern.match(line))
    
    def _is_list_item(self, line: str) -> Match[str] | None | bool:
        """检查是否为列表项"""
        line = line.strip()
        if not line:
            return False
        
        return (self.list_pattern.match(line) or 
                self.numbered_list_pattern.match(line))
    
    def _is_table_start(self, lines: List[str], index: int) -> bool | Match[str] | None:
        """检查是否为表格开始"""
        if index >= len(lines):
            return False
        
        line = lines[index].strip()
        if not self.table_separator_pattern.match(line):
            return False
        
        # 检查下一行是否为表格对齐行
        if index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            return self.table_alignment_pattern.match(next_line)
        
        return False
    
    def _parse_table(self, lines: List[str], start_index: int) -> tuple[List[List[str]], int]:
        """解析表格"""
        table_data = []
        i = start_index
        
        # 解析表头
        header_line = lines[i].strip()
        header_cells = [cell.strip() for cell in header_line.split('|')[1:-1]]
        table_data.append(header_cells)
        i += 1
        
        # 跳过对齐行
        if i < len(lines) and self.table_alignment_pattern.match(lines[i].strip()):
            i += 1
        
        # 解析数据行
        while i < len(lines):
            line = lines[i].strip()
            if not line or not self.table_separator_pattern.match(line):
                break
            
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            table_data.append(cells)
            i += 1
        
        return table_data, i
    
    def _parse_list(self, lines: List[str], start_index: int) -> tuple[List[MarkdownElement], int]:
        """解析列表"""
        list_elements = []
        i = start_index
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # 检查是否为列表项
            list_match = self.list_pattern.match(line) or self.numbered_list_pattern.match(line)
            if list_match:
                item_text = list_match.group(1).strip()
                formatted_text = self._parse_text_formatting(item_text)
                
                # 创建列表项元素
                list_element = MarkdownElement(
                    type=ElementType.PARAGRAPH,  # 列表项作为段落处理
                    content=item_text,
                    formatted_text=formatted_text
                )
                list_elements.append(list_element)
                i += 1
            else:
                break
        
        return list_elements, i
    
    def _parse_code_block(self, lines: List[str], start_index: int) -> tuple[str, int]:
        """解析代码块"""
        code_lines = []
        i = start_index + 1
        
        while i < len(lines):
            if self.code_block_pattern.match(lines[i]):
                break
            code_lines.append(lines[i])
            i += 1
        
        return '\n'.join(code_lines), i + 1
    
    def _parse_text_formatting(self, text: str) -> List[TextFormat]:
        """解析文本格式（粗体、斜体等）"""
        if not text:
            return [TextFormat(text="")]
        
        # 先处理粗体，再处理斜体
        formatted_parts = []
        
        # 分割文本，保留格式标记
        parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
        
        for part in parts:
            if not part:
                continue
            
            if part.startswith('**') and part.endswith('**'):
                # 粗体
                content = part[2:-2]
                formatted_parts.append(TextFormat(bold=True, text=content))
            elif part.startswith('*') and part.endswith('*') and not part.startswith('**'):
                # 斜体
                content = part[1:-1]
                formatted_parts.append(TextFormat(italic=True, text=content))
            else:
                # 普通文本
                formatted_parts.append(TextFormat(text=part))
        
        return formatted_parts
