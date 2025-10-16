"""
文件转录服务模块
处理音频文件上传和转录
"""
import os
import time
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from pydub import AudioSegment
from app.core.logging import logger
from app.config import FILE_TRANSCRIPTION_CONFIG, GLOBAL_SETTINGS
from app.services.whisper import whisper_service
from app.models.schemas import TranscriptionSegment, FileTranscriptionResponse


class FileTranscriptionService:
    """文件转录服务类"""
    
    def __init__(self):
        """初始化文件转录服务"""
        self.temp_dir = FILE_TRANSCRIPTION_CONFIG["temp_dir"]
        self.max_file_size = FILE_TRANSCRIPTION_CONFIG["max_file_size"]
        self.allowed_formats = FILE_TRANSCRIPTION_CONFIG["allowed_formats"]
        self.ensure_temp_dir()
    
    def ensure_temp_dir(self):
        """确保临时目录存在"""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            logger.info(f"创建临时目录: {self.temp_dir}")
    
    def validate_audio_file(self, file_path: str, file_size: int) -> Tuple[bool, str]:
        """
        验证音频文件
        
        Args:
            file_path: 文件路径
            file_size: 文件大小（字节）
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        # 检查文件大小
        if file_size > self.max_file_size:
            return False, f"文件大小超过限制 ({self.max_file_size / (1024*1024):.1f}MB)"
        
        # 检查文件格式
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.allowed_formats:
            return False, f"不支持的文件格式: {file_ext}，支持的格式: {', '.join(self.allowed_formats)}"
        
        # 检查文件是否存在
        # if not os.path.exists(file_path):
        #     return False, "文件不存在"
        
        return True, ""
    
    def convert_audio_format(self, input_path: str, output_path: str) -> bool:
        """
        转换音频格式为WAV
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            
        Returns:
            bool: 转换是否成功
        """
        try:
            logger.info(f"转换音频格式: {input_path} -> {output_path}")
            
            # 使用pydub加载音频
            audio = AudioSegment.from_file(input_path)
            
            # 转换为WAV格式，16kHz采样率，单声道
            audio = audio.set_frame_rate(16000).set_channels(1)
            
            # 导出为WAV
            audio.export(output_path, format="wav")
            
            logger.info("音频格式转换完成")
            return True
            
        except Exception as e:
            logger.error(f"音频格式转换失败: {str(e)}")
            return False
    
    def transcribe_audio_file(self, file_path: str, language: str) -> Tuple[any, any]:
        """
        转录音频文件
        
        Args:
            file_path: 音频文件路径
            language: 语言代码
            
        Returns:
            tuple: (转录结果, 转录信息)
        """
        try:
            logger.info(f"开始转录音频文件: {file_path}")
            
            # 使用whisper服务进行转录
            segments, info = whisper_service.transcribe(file_path, language)

            return segments, info
            
        except Exception as e:
            logger.error(f"音频转录失败: {str(e)}")
            raise
    
    
    def process_audio_file(
        self, 
        file_path: str, 
        language: Optional[str] = None,
        show_timestamp: Optional[bool] = None
    ) -> FileTranscriptionResponse:
        """
        处理音频文件进行转录
        
        Args:
            file_path: 音频文件路径
            language: 语言代码（可选，默认使用全局设置）
            show_timestamp: 是否显示时间戳（可选，默认使用全局设置）
            
        Returns:
            FileTranscriptionResponse: 转录结果
        """
        start_time = time.time()
        
        # 使用全局设置作为默认值
        language = language or GLOBAL_SETTINGS["language"]
        show_timestamp = show_timestamp if show_timestamp is not None else GLOBAL_SETTINGS["show_timestamp"]
        
        try:
            logger.info(f"开始转录音频文件: {file_path}")
            
            # 转录音频
            transcribe_result, transcribe_info = self.transcribe_audio_file(file_path, language)
            
            transcribe_result = list(transcribe_result)
            logger.info(f"音频转录完成: 共{len(transcribe_result)}个片段")

            # 格式化输出
            segments = []
            formatted_lines = []

            for segment in transcribe_result:
                if segment.text.strip():
                    segments.append(TranscriptionSegment(
                        speaker="",
                        start_time=round(segment.start, 2),
                        end_time=round(segment.end, 2),
                        text=segment.text.strip()
                    ))
                    
                    if show_timestamp:
                        line = f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text.strip()}"
                    else:
                        line = f"{segment.text.strip()}"
                    formatted_lines.append(line)
            
            processing_time = time.time() - start_time
            
            return FileTranscriptionResponse(
                status="success",
                message="文件转录完成",
                segments=segments,
                formatted_text="\n".join(formatted_lines),
                processing_time=round(processing_time, 2)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"文件转录失败: {str(e)}")
            
            return FileTranscriptionResponse(
                status="error",
                message=f"文件转录失败: {str(e)}",
                processing_time=round(processing_time, 2)
            )
    
    def process_uploaded_file(
        self, 
        file_content: bytes, 
        filename: str,
        language: Optional[str] = None,
        show_timestamp: Optional[bool] = None
    ) -> FileTranscriptionResponse:
        """
        处理上传的音频文件
        
        Args:
            file_content: 文件内容（字节）
            filename: 文件名
            language: 语言代码（可选，默认使用全局设置）
            show_timestamp: 是否显示时间戳（可选，默认使用全局设置）
            
        Returns:
            FileTranscriptionResponse: 转录结果
        """
        temp_file_path = None
        converted_file_path = None
        
        # 使用全局设置作为默认值
        language = language or GLOBAL_SETTINGS["language"]
        show_timestamp = show_timestamp if show_timestamp is not None else GLOBAL_SETTINGS["show_timestamp"]
        
        logger.debug(f"开始处理上传文件: {filename}")
        logger.debug(f"文件大小: {len(file_content)} 字节")
        logger.debug(f"语言设置: {language}, 时间戳: {show_timestamp}")
        
        try:
            # 1. 验证文件
            logger.debug("开始验证文件")
            file_size = len(file_content)
            is_valid, error_msg = self.validate_audio_file(filename, file_size)
            logger.debug(f"文件验证结果: {is_valid}, 错误信息: {error_msg}")
            
            if not is_valid:
                logger.warning(f"文件验证失败: {error_msg}")
                return FileTranscriptionResponse(
                    status="error",
                    message=error_msg
                )
            
            # 2. 保存临时文件
            logger.debug("开始保存临时文件")
            os.makedirs(self.temp_dir, exist_ok=True)

            temp_file_path = os.path.join(self.temp_dir, filename)
            with open(temp_file_path, "wb") as f:
                f.write(file_content)
            
            logger.info(f"临时文件已保存: {temp_file_path}")
            logger.debug(f"临时文件大小: {os.path.getsize(temp_file_path)} 字节")
            
            # 3. 转换音频格式（如果需要）
            file_ext = Path(filename).suffix.lower()
            logger.debug(f"文件扩展名: {file_ext}")
            
            if file_ext != ".wav":
                logger.debug("需要转换音频格式")
                converted_file_path = os.path.join(self.temp_dir, f"converted_{filename}.wav")
                if not self.convert_audio_format(temp_file_path, converted_file_path):
                    logger.error("音频格式转换失败")
                    return FileTranscriptionResponse(
                        status="error",
                        message="音频格式转换失败"
                    )
                process_file_path = converted_file_path
                logger.debug(f"音频转换完成，处理文件: {process_file_path}")
            else:
                process_file_path = temp_file_path
                logger.debug("文件已是WAV格式，无需转换")
            
            # 4. 处理音频文件
            logger.debug("开始处理音频文件进行转录")
            result = self.process_audio_file(
                process_file_path, language, show_timestamp
            )
            
            logger.debug(f"音频处理完成，结果状态: {result.status}")
            return result
            
        except Exception as e:
            logger.error(f"处理上传文件失败: {str(e)}", exc_info=True)
            return FileTranscriptionResponse(
                status="error",
                message=f"处理上传文件失败: {str(e)}"
            )
        
        finally:
            # 清理临时文件
            logger.debug("开始清理临时文件")
            self.cleanup_temp_files([temp_file_path, converted_file_path])
    
    def cleanup_temp_files(self, file_paths: List[Optional[str]]):
        """
        清理临时文件
        
        Args:
            file_paths: 要清理的文件路径列表
        """
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"已清理临时文件: {file_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {file_path}, 错误: {str(e)}")


# 创建全局文件转录服务实例
file_transcription_service = FileTranscriptionService()
