"""
API路由注册
"""
from fastapi import APIRouter
from app.api.endpoints import audio, transcription, websocket, file_transcription
from app.api.endpoints import file_transcription_stream, meeting_minutes

# 创建主路由
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(audio.router, tags=["audio"])
api_router.include_router(transcription.router, tags=["transcription"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(file_transcription.router, tags=["file_transcription"])
api_router.include_router(file_transcription_stream.router, tags=["file_transcription_stream"])
api_router.include_router(meeting_minutes.router, prefix="/meeting/minutes", tags=["meeting_minutes"])