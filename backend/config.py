"""
配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """应用配置"""
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # 代理配置
    HTTP_PROXY: str = os.getenv("HTTP_PROXY", "http://127.0.0.1:7890")
    HTTPS_PROXY: str = os.getenv("HTTPS_PROXY", "http://127.0.0.1:7890")
    USE_PROXY: bool = os.getenv("USE_PROXY", "true").lower() == "true"
    
    # Gemini 模型配置
    GEMINI_LIVE_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_GENERATION_MODEL: str = "gemini-2.5-flash-lite"
    
    # WebSocket 配置
    WS_HEARTBEAT_INTERVAL: int = 30  # 秒
    WS_MAX_MESSAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # API 配置
    API_TIMEOUT: int = 30  # 秒

settings = Settings()

