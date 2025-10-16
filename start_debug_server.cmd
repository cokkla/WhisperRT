@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
REM 统一为UTF-8，避免中文提示乱码
chcp 65001 >nul

REM =============================================================
REM 启动 FastAPI 语音转录服务（调试模式）
REM - 启用详细日志记录
REM - 支持热重载
REM - 显示所有调试信息
REM =============================================================

REM 切换到脚本所在目录（项目根目录）
cd /d "%~dp0"

REM 设置 faster-whisper 模型缓存目录
set "WHISPER_CACHE_DIR=%CD%\models\whisper"

REM 确保目录存在
if not exist "%WHISPER_CACHE_DIR%" mkdir "%WHISPER_CACHE_DIR%"

echo [DEBUG] WHISPER_CACHE_DIR=%WHISPER_CACHE_DIR%

REM 设置调试环境变量
set "PYTHONPATH=%CD%"
set "LOG_LEVEL=DEBUG"

REM 检查 conda 是否可用
where conda >nul 2>&1
if errorlevel 1 (
  echo [ERROR] 未检测到 conda，请先安装并将其加入 PATH。
  echo         也可手动在當前窗口執行：
  echo         set WHISPER_CACHE_DIR=%WHISPER_CACHE_DIR%
  echo         set LOG_LEVEL=DEBUG
  echo         uvicorn app.main:app --host 0.0.0.0 --port 5444 --reload --log-level debug
  pause
  exit /b 1
)

REM 激活 llm 环境（优先使用 activate，如果失败则回退 conda run）
call conda activate llm 2>nul
if errorlevel 1 (
  echo [WARN] conda activate 失败，尝试使用 conda run 直接启动。
  echo [DEBUG] Starting debug server at http://localhost:5444/
  conda run -n llm uvicorn app.main:app --host 0.0.0.0 --port 5444 --reload --log-level debug
  goto :end
)

REM 启动 FastAPI 服务（调试模式）
echo [DEBUG] Starting debug server at http://localhost:5444
echo [DEBUG] 日志级别: DEBUG
echo [DEBUG] 热重载: 启用
echo [DEBUG] 详细错误信息: 启用
echo.
uvicorn app.main:app --host 0.0.0.0 --port 5444 --reload --log-level debug

:end
echo.
echo [DEBUG] 调试服务器已退出。
pause
