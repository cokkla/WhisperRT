"""
Pydantic 模型定义
"""
from typing import List, Optional
from pydantic import BaseModel


class ModelRequest(BaseModel):
    """模型选择请求"""
    model: str


class LanguageRequest(BaseModel):
    """语言选择请求"""
    language: str


class TimestampRequest(BaseModel):
    """时间戳显示设置请求"""
    show_timestamp: bool


class DeviceRequest(BaseModel):
    """音频设备选择请求"""
    device_id: str


class FileTranscriptionRequest(BaseModel):
    """文件转录请求"""
    pass


class TranscriptionSegment(BaseModel):
    """转录片段"""
    speaker: str
    start_time: float
    end_time: float
    text: str


class FileTranscriptionResponse(BaseModel):
    """文件转录响应"""
    status: str
    message: str
    segments: Optional[List[TranscriptionSegment]] = None
    formatted_text: Optional[str] = None
    processing_time: Optional[float] = None




class GlobalSettingsRequest(BaseModel):
    """全局设置请求"""
    show_timestamp: Optional[bool] = None
    language: Optional[str] = None
    model: Optional[str] = None


class GlobalSettingsResponse(BaseModel):
    """全局设置响应"""
    status: str
    message: str
    settings: Optional[dict] = None


class MeetingInfo(BaseModel):
    """会议基本信息"""
    topic: str
    date: str  # yyyy-mm-dd格式
    location: str
    attendees: List[str]
    host: str
    recorder: str


class MeetingMinutesRequest(BaseModel):
    """会议纪要生成请求"""
    transcription_text: str
    meeting_info: MeetingInfo


class MeetingMinutesResponse(BaseModel):
    """会议纪要生成响应"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    created_at: str
    result_length: int


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskStatusResponse]