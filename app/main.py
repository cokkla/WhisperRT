"""
应用入口模块
"""
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from app.api.router import api_router
from app.core.logging import logger
from app.config import HOST, PORT

# 测试时切换到项目根目录，确保静态文件路径正确
# os.chdir(os.path.dirname(os.path.dirname(__file__)))

# 创建FastAPI应用
app = FastAPI(title="实时语音转写")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 设置模板
templates = Jinja2Templates(directory="templates")

# 注册API路由
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或者写成前端地址，比如 "http://127.0.0.1:5500"
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法，包括 OPTIONS、POST、GET
    allow_headers=["*"],  # 允许所有请求头
)

# 主页路由
@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    """
    渲染主页
    
    Args:
        request: 请求对象
    
    Returns:
        HTML响应
    """
    return templates.TemplateResponse("index.html", {"request": request})

# 应用启动入口
if __name__ == '__main__':
    try:
        logger.info("启动应用服务器")
        uvicorn.run(app, host=HOST, port=PORT)
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")