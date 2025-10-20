"""
文件流式转录服务
基于 WebSocket 的分段解码、增量推理与可中断任务管理
"""
import contextlib
import os
import time
import uuid
import threading
import asyncio
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

import numpy as np

from app.core.logging import logger
from app.config import SAMPLE_RATE, GLOBAL_SETTINGS, ANTI_HALLUCINATION_CONFIG
from app.services.whisper import whisper_service
from app.services.transcription import TranscriptionService


@dataclass
class FileStreamTaskState:
    """文件流式转录任务状态"""
    task_id: str
    filename: str
    language: Optional[str]
    total_seconds: Optional[float] = None
    processed_seconds: float = 0.0
    status: str = "running"  # running | completed | cancelled | error
    cancel_event: threading.Event = field(default_factory=threading.Event)
    subscribers: Set = field(default_factory=set)  # 订阅此任务的 websocket 连接
    transcript: List[Dict] = field(default_factory=list)
    temp_file_path: Optional[str] = None


class FileTranscriptionStreamService:
    """文件流式转录服务：解码->分段->推理->WS推送，支持随时停止"""

    def __init__(self):
        self.tasks: Dict[str, FileStreamTaskState] = {}
        self.block_seconds = 5.0

    def create_task(self, filename: str, language: Optional[str] = None, temp_file_path: Optional[str] = None) -> FileStreamTaskState:
        task_id = str(uuid.uuid4())
        state = FileStreamTaskState(
            task_id=task_id,
            filename=filename,
            language=language or GLOBAL_SETTINGS["language"],
            temp_file_path=temp_file_path,
        )
        self.tasks[task_id] = state
        return state

    def stop_task(self, task_id: str) -> Dict:
        state = self.tasks.get(task_id)
        if not state:
            return {"status": "error", "message": "task not found"}
        if state.status in ("cancelled", "completed", "error"):
            return {"status": "already_stopped", "task_id": task_id}
        state.cancel_event.set()
        logger.info(f"请求停止文件流式转录任务: {task_id}")
        return {"status": "stopping", "task_id": task_id}

    async def _broadcast(self, state: FileStreamTaskState, event_type: str, data: Dict):
        """向任务订阅者广播事件"""
        payload = {"event": event_type, "data": {**data, "task_id": state.task_id}}
        to_remove = []
        for ws in list(state.subscribers):
            try:
                await ws.send_json(payload)
            except Exception as e:
                logger.error(f"WS 发送失败(task={state.task_id}): {e}")
                to_remove.append(ws)
        for ws in to_remove:
            state.subscribers.discard(ws)

    def _estimate_total_duration(self, input_path: str) -> Optional[float]:
        """估计文件总时长（秒）。简单实现：调用 ffprobe；失败则返回 None。"""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", input_path
                ],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
            )
            return float(result.stdout.strip())
        except Exception:
            return None

    def _decode_stream_iter(self, input_path: str, cancel_event: threading.Event, block_seconds: float = 1.0):
        """
        使用 ffmpeg 将音频以 16kHz mono float32 PCM 解码为流，并按 block_seconds 产出块。
        """
        samples_per_block = int(SAMPLE_RATE * block_seconds)
        bytes_per_sample = 4  # float32
        bytes_per_block = samples_per_block * bytes_per_sample

        cmd = [
            "ffmpeg", "-nostdin", "-i", input_path,
            "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "pipe:1"
        ]
        # 使用 DEVNULL 丢弃 ffmpeg 的 stderr，避免长时间运行或平台差异导致的管道阻塞
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        try:
            while not cancel_event.is_set():
                chunk = proc.stdout.read(bytes_per_block)
                if not chunk:
                    break

                is_tail_block = len(chunk) < bytes_per_block
                if is_tail_block:
                    # 最后一块补齐为相同长度，尾部零填充
                    chunk += b"\x00" * (bytes_per_block - len(chunk))

                audio = np.frombuffer(chunk, dtype=np.float32)
                yield audio

                # 关键：如果这是尾块，则在产出后立即结束循环，避免继续 read 等待 EOF 卡住
                if is_tail_block:
                    break
        finally:
            with contextlib.suppress(Exception):
                proc.terminate()
            with contextlib.suppress(Exception):
                proc.kill()

    def _preprocess(self, audio: np.ndarray) -> np.ndarray:
        # 复用实时服务中的预处理逻辑的精简版（归一化）
        if audio.size == 0:
            return audio.astype(np.float32)
        audio = audio.astype(np.float32)
        max_val = float(np.max(np.abs(audio)))
        if max_val > 0:
            audio = audio / max_val
        return audio.astype(np.float32)

    def _validate(self, text: str, confidence: float, rt_service: TranscriptionService) -> bool:
        return rt_service.validate_transcription_quality(text, confidence)

    def _transcribe_block(self, samples: np.ndarray, language: Optional[str]):
        return whisper_service.transcribe(samples, language)

    def run_task(self, state: FileStreamTaskState, input_path: str):
        """后台线程：解码->推理->WS 广播"""
        rt_service = TranscriptionService()  # 仅复用其质量筛选逻辑
        state.total_seconds = self._estimate_total_duration(input_path)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run():
            try:
                await self._broadcast(state, "status", {
                    "status": "started",
                    "model": whisper_service.model_name,
                    "language": state.language,
                })

                start_ts = time.time()
                for block in self._decode_stream_iter(input_path, state.cancel_event, self.block_seconds):
                    if state.cancel_event.is_set():
                        state.status = "cancelled"
                        break

                    samples = self._preprocess(block)

                    try:
                        segments, _ = self._transcribe_block(samples, state.language)
                        for seg in list(segments):
                            text = seg.text.strip()
                            logger.debug("[%.2fs -> %.2fs] %s" % (seg.start, seg.end, seg.text))
                            confidence = float(np.exp(seg.avg_logprob))
                            if not self._validate(text, confidence, rt_service):
                                continue

                            state.processed_seconds = time.time() - start_ts
                            timestamp = self._format_hms(state.processed_seconds)
                            await self._broadcast(state, "transcription", {
                                "text": text,
                                "timestamp": timestamp,
                                "show_timestamp": GLOBAL_SETTINGS["show_timestamp"],
                                "confidence": confidence,
                                "mode": "segments",
                            })
                            state.transcript.append({
                                "text": text,
                                "timestamp": timestamp,
                                "confidence": confidence,
                            })

                        # 进度广播（可选）
                        if state.total_seconds:
                            percent = min(100.0, 100.0 * state.processed_seconds / max(1e-6, state.total_seconds))
                            await self._broadcast(state, "progress", {
                                "processed_seconds": round(state.processed_seconds, 2),
                                "total_seconds": round(state.total_seconds, 2),
                                "percent": round(percent, 2),
                            })
                    except Exception as e:
                        logger.error(f"文件分块推理失败(task={state.task_id}): {e}")
                        await self._broadcast(state, "error", {"message": f"转写错误: {str(e)}"})

                    # 块处理结束后再次检查取消，避免在块处理中设置取消但未及时生效
                    if state.cancel_event.is_set():
                        state.status = "cancelled"
                        break

                # 循环结束时兜底判定：若已收到取消请求且状态仍为运行中，则标记为取消
                if state.cancel_event.is_set() and state.status == "running":
                    state.status = "cancelled"
                elif state.status != "cancelled":
                    state.status = "completed"
                await self._broadcast(state, "status", {"status": state.status})
            except Exception as e:
                state.status = "error"
                logger.error(f"任务运行失败(task={state.task_id}): {e}")
                await self._broadcast(state, "error", {"message": str(e)})
            finally:
                # 清理
                pass

        loop.run_until_complete(_run())
        loop.close()

    @staticmethod
    def _format_hms(seconds: float) -> str:
        seconds_int = int(seconds)
        h = seconds_int // 3600
        m = (seconds_int % 3600) // 60
        s = seconds_int % 60
        return f"{h:02d}:{m:02d}:{s:02d}"


# 单例
file_transcription_stream_service = FileTranscriptionStreamService()


