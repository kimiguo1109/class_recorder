"""
Class Recorder Backend - FastAPI Application
实时课堂录音转录与 AI 学习助手
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Class Recorder API",
    description="实时课堂录音转录与 AI 学习助手",
    version="1.0.0"
)

# CORS 配置
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/")
async def root():
    """根路径 - 健康检查"""
    return {
        "status": "ok",
        "message": "Class Recorder API is running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "gemini_api_key_configured": bool(os.getenv("GEMINI_API_KEY"))
    }

# 导入路由
from api import websocket, notes, speaker_api, recording
app.include_router(websocket.router)
app.include_router(notes.router)
app.include_router(speaker_api.router)
app.include_router(recording.router)

if __name__ == "__main__":
    import uvicorn
    
    # 清理旧日志文件
    log_file = "app.log"
    if os.path.exists(log_file):
        os.remove(log_file)
        print(f"✅ 已清理旧日志: {log_file}")
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)

