"""
文件转录相关的API端点
"""
import uvicorn
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from app.models.schemas import (
    FileTranscriptionRequest, 
    FileTranscriptionResponse
)
from app.services.file_transcription import file_transcription_service
from app.config import FILE_TRANSCRIPTION_CONFIG
from app.core.logging import logger

router = APIRouter()


@router.post("/transcribe_file", response_model=FileTranscriptionResponse)
async def transcribe_audio_file(
    file: UploadFile = File(..., description="音频文件")
):
    """
    上传音频文件并进行转录
    
    Args:
        file: 上传的音频文件
    
    Returns:
        FileTranscriptionResponse: 转录结果
    """
    try:
        logger.info(f"收到文件转录请求: {file.filename}")
        logger.debug(f"文件类型: {file.content_type}")
        logger.debug(f"文件大小: {file.size if hasattr(file, 'size') else '未知'}")
        
        # 检查文件是否为空
        if not file.filename:
            logger.warning("收到空文件名")
            raise HTTPException(status_code=400, detail="未选择文件")
        
        # 读取文件内容
        logger.debug("开始读取文件内容")
        file_content = await file.read()
        logger.debug(f"文件内容读取完成，大小: {len(file_content)} 字节")
        
        # 处理文件
        logger.debug("开始处理文件")
        result = file_transcription_service.process_uploaded_file(
            file_content=file_content,
            filename=file.filename
        )
        
        logger.info(f"文件转录完成: {file.filename}, 状态: {result.status}")
        logger.debug(f"转录结果: {result}")
        return result
        
    except HTTPException as he:
        logger.error(f"HTTP异常: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"文件转录API错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/get_file_transcription_config")
async def get_file_transcription_config():
    """
    获取文件转录配置
    
    Returns:
        dict: 文件转录配置信息
    """
    try:
        config = {
            "max_file_size_mb": FILE_TRANSCRIPTION_CONFIG["max_file_size"] / (1024 * 1024),
            "allowed_formats": FILE_TRANSCRIPTION_CONFIG["allowed_formats"],
            "output_format": FILE_TRANSCRIPTION_CONFIG["output_format"]
        }
        
        return {
            "status": "success",
            "message": "获取配置成功",
            "config": config
        }
        
    except Exception as e:
        logger.error(f"获取文件转录配置失败: {str(e)}")
        return {
            "status": "error",
            "message": f"获取配置失败: {str(e)}"
        }

