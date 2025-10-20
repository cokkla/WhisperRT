"""
文件流式转录 WebSocket 端点
支持：start（绑定 task）、接收订阅、progress/transcription 实时推送、stop 取消
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from pydantic import BaseModel
import os

from app.config import FILE_TRANSCRIPTION_CONFIG

from app.core.logging import logger
from app.services.file_transcription_stream import file_transcription_stream_service


router = APIRouter()


class StartFileStreamRequest(BaseModel):
    filename: str
    language: str | None = None
    temp_file_path: str | None = None  # 已上传到服务器的临时文件路径


@router.post("/init_file_stream")
def init_file_stream(request: StartFileStreamRequest):
    """
    初始化一个文件流式转录任务，返回 task_id；前端随后通过 WS 订阅并开始接收流式结果。
    """
    if not request.temp_file_path:
        raise HTTPException(status_code=400, detail="temp_file_path 必填，指向已上传的服务器文件路径")
    state = file_transcription_stream_service.create_task(
        filename=request.filename,
        language=request.language,
        temp_file_path=request.temp_file_path,
    )
    logger.info(f"创建文件流式转录任务: {state.task_id} -> {state.temp_file_path}")
    return {"status": "success", "task_id": state.task_id}


@router.post("/upload_file_temp")
async def upload_file_temp(file: UploadFile = File(...)):
    """
    上传音频文件到服务器临时目录，返回可用于流式任务的 temp_file_path。
    """
    try:
        temp_dir = FILE_TRANSCRIPTION_CONFIG["temp_dir"]
        os.makedirs(temp_dir, exist_ok=True)
        save_path = os.path.join(temp_dir, file.filename)
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)
        return {"status": "success", "temp_file_path": save_path, "filename": file.filename, "size": len(content)}
    except Exception as e:
        logger.error(f"上传临时文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.websocket("/ws/file_transcribe")
async def ws_file_transcribe(websocket: WebSocket):
    """
    WebSocket 文件流式转录：
    - 客户端连接后发送 JSON：{"event":"start","data":{"task_id":"..."}}
    - 服务端将该连接加入任务订阅，并启动后台解码+推理（仅首次）
    - 客户端可发送 {"event":"stop","data":{"task_id":"..."}} 取消
    """
    await websocket.accept()

    task_id = None
    try:
        while True:
            msg = await websocket.receive_json()
            event = msg.get("event")
            data = msg.get("data") or {}

            if event == "start":
                task_id = data.get("task_id")
                if not task_id:
                    await websocket.send_json({"event": "error", "data": {"message": "缺少 task_id"}})
                    continue
                state = file_transcription_stream_service.tasks.get(task_id)
                if not state:
                    await websocket.send_json({"event": "error", "data": {"message": "任务不存在"}})
                    continue
                # 订阅
                state.subscribers.add(websocket)
                await websocket.send_json({"event": "status", "data": {"status": "connected", "task_id": task_id}})

                # 若任务未运行（首次订阅），启动后台线程
                if state.status == "running" and state.processed_seconds == 0 and state.temp_file_path:
                    def _runner():
                        logger.debug("开始文件转录")
                        file_transcription_stream_service.run_task(state, state.temp_file_path)
                    import threading
                    t = threading.Thread(target=_runner, daemon=True)
                    t.start()

            elif event == "stop":
                task_id = data.get("task_id")
                if not task_id:
                    await websocket.send_json({"event": "error", "data": {"message": "缺少 task_id"}})
                    continue
                result = file_transcription_stream_service.stop_task(task_id)
                await websocket.send_json({"event": "status", "data": {**result, "task_id": task_id}})

            else:
                await websocket.send_json({"event": "error", "data": {"message": f"未知事件: {event}"}})

    except WebSocketDisconnect:
        logger.info("文件流式转录 WS 客户端断开")
    except Exception as e:
        logger.error(f"文件流式转录 WS 错误: {e}")
        try:
            await websocket.send_json({"event": "error", "data": {"message": str(e)}})
        except Exception:
            pass
    finally:
        # 从所有任务的订阅集合中移除此连接
        try:
            for state in list(file_transcription_stream_service.tasks.values()):
                if websocket in state.subscribers:
                    state.subscribers.discard(websocket)
        except Exception:
            pass


class StopTaskRequest(BaseModel):
    task_id: str


@router.post("/stop_file_stream")
def stop_file_stream(request: StopTaskRequest):
    """HTTP 停止指定 task 的文件流式转录"""
    return file_transcription_stream_service.stop_task(request.task_id)


