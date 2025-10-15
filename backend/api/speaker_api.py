"""
说话人识别 API - 注册和管理教授声音
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import base64
import logging

from services.speaker_recognition_service import speaker_recognition_service

logger = logging.getLogger(__name__)

router = APIRouter()


class RegisterVoiceRequest(BaseModel):
    """注册声音请求"""
    audioData: str  # Base64 编码的音频数据


class RegisterVoiceResponse(BaseModel):
    """注册声音响应"""
    success: bool
    message: str


class SpeakerStatusResponse(BaseModel):
    """说话人识别状态响应"""
    hasProfessorProfile: bool
    message: str


@router.post("/api/speaker/register-professor", response_model=RegisterVoiceResponse)
async def register_professor_voice(request: RegisterVoiceRequest):
    """
    注册教授的声音
    
    前端需要发送至少 5-10 秒的教授讲话音频
    """
    try:
        logger.info("📝 Registering professor voice...")
        
        # 解码音频数据
        audio_bytes = base64.b64decode(request.audioData)
        
        # 检查音频长度（至少 3 秒）
        # 16kHz, 16-bit PCM, mono = 32000 bytes/second
        min_bytes = 32000 * 3  # 3 秒
        if len(audio_bytes) < min_bytes:
            return RegisterVoiceResponse(
                success=False,
                message=f"音频太短，请录制至少 3 秒的音频（当前: {len(audio_bytes) / 32000:.1f} 秒）"
            )
        
        # 注册声音
        success = speaker_recognition_service.register_professor_voice(audio_bytes)
        
        if success:
            logger.info("✅ Professor voice registered successfully")
            return RegisterVoiceResponse(
                success=True,
                message="教授声音注册成功！现在可以自动识别教授的发言了。"
            )
        else:
            logger.error("❌ Professor voice registration failed")
            return RegisterVoiceResponse(
                success=False,
                message="声音注册失败，请重试或检查音频质量"
            )
            
    except Exception as e:
        logger.error(f"❌ Error registering professor voice: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/speaker/status", response_model=SpeakerStatusResponse)
async def get_speaker_status():
    """
    获取说话人识别系统状态
    """
    try:
        has_profile = speaker_recognition_service.has_professor_profile()
        
        if has_profile:
            message = "✅ 已注册教授声音，系统将自动识别教授和学生的发言"
        else:
            message = "⚠️ 未注册教授声音，请先录制教授的声音样本"
        
        return SpeakerStatusResponse(
            hasProfessorProfile=has_profile,
            message=message
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting speaker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/speaker/clear-professor")
async def clear_professor_voice():
    """
    清除教授的声音配置
    """
    try:
        speaker_recognition_service.clear_professor_profile()
        logger.info("✅ Professor voice profile cleared")
        
        return {"success": True, "message": "教授声音配置已清除"}
        
    except Exception as e:
        logger.error(f"❌ Error clearing professor voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

