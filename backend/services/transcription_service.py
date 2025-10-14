"""
转录服务 - 使用 Gemini Live API 进行实时音频转录和翻译
"""
import asyncio
import base64
import json
import time
import uuid
import logging
from typing import Optional, Dict, Any
import aiohttp
from config import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    实时转录服务
    使用 Gemini Live API 进行音频转录和翻译
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.live_model = "gemini-live-2.5-flash-preview"  # Gemini Live API 模型
        self.generation_model = settings.GEMINI_GENERATION_MODEL  # 用于翻译
        self.api_base_url = "https://aiplatform.googleapis.com/v1/publishers/google/models"
        
        # 初始化 Gemini Client
        self.client = genai.Client(api_key=self.api_key)
        self.live_session: Optional[Any] = None
        
        logger.info(f"✅ TranscriptionService initialized with Live model: {self.live_model}")

    async def start_live_session(self):
        """
        启动 Gemini Live API 会话
        """
        try:
            config = {
                "response_modalities": ["TEXT"],  # 只需要文本响应
                "input_audio_transcription": {}   # 启用音频转录
            }
            
            logger.info(f"🚀 Starting Gemini Live API session...")
            
            # 使用 aio.live.connect 建立异步连接
            self.live_session = await self.client.aio.live.connect(
                model=self.live_model,
                config=config
            )
            
            logger.info(f"✅ Gemini Live API session started successfully")
            return self.live_session
            
        except Exception as e:
            logger.error(f"❌ Failed to start Gemini Live API session: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def stop_live_session(self):
        """
        停止 Gemini Live API 会话
        """
        if self.live_session:
            try:
                await self.live_session.close()
                self.live_session = None
                logger.info("✅ Gemini Live API session stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping live session: {e}")

    async def call_gemini_api(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        调用 Gemini API（用于翻译等非转录任务）
        """
        url = f"{self.api_base_url}/{self.generation_model}:streamGenerateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        try:
            # 配置代理
            connector = None
            if settings.USE_PROXY:
                connector = aiohttp.TCPConnector()
            
            async with aiohttp.ClientSession(connector=connector) as session:
                proxy = settings.HTTP_PROXY if settings.USE_PROXY else None
                
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=settings.API_TIMEOUT),
                    proxy=proxy
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API error: {response.status} - {error_text}")
                        raise Exception(f"API error: {response.status}")

                    data = await response.json()
                    
                    # 合并所有流式块的文本
                    full_text = ""
                    if isinstance(data, list):
                        for chunk in data:
                            if "candidates" in chunk and len(chunk["candidates"]) > 0:
                                content = chunk["candidates"][0].get("content", {})
                                parts = content.get("parts", [])
                                if parts and len(parts) > 0:
                                    full_text += parts[0].get("text", "")
                    else:
                        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        full_text = text

                    if not full_text:
                        raise Exception("API 返回空响应")

                    return full_text.strip()

        except asyncio.TimeoutError:
            logger.error("Gemini API timeout")
            raise Exception("API 调用超时")
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

    def detect_language(self, text: str) -> str:
        """
        简单的语言检测（基于 Unicode 字符范围）
        """
        if not text:
            return 'en'

        # 中文检测
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return 'zh'
        # 日语检测（平假名、片假名）
        elif any(('\u3040' <= char <= '\u309f') or ('\u30a0' <= char <= '\u30ff') for char in text):
            return 'ja'
        # 韩语检测（谚文）
        elif any('\uac00' <= char <= '\ud7af' for char in text):
            return 'ko'
        # 西里尔字母（俄语等）
        elif any('\u0400' <= char <= '\u04ff' for char in text):
            return 'ru'
        # 阿拉伯语
        elif any('\u0600' <= char <= '\u06ff' for char in text):
            return 'ar'
        # 默认为英语
        else:
            return 'en'

    async def translate_to_english(self, text: str, source_lang: str) -> str:
        """
        将文本翻译成英文
        """
        if source_lang == 'en':
            return text

        prompt = f"""Translate the following {source_lang} text to English. 
Only output the English translation, no explanations or additional text.

Text to translate:
{text}

English translation:"""

        try:
            translation = await self.call_gemini_api(prompt, temperature=0.2)
            return translation
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return f"[Translation failed: {str(e)}]"

    async def transcribe_audio(self, audio_base64: str) -> Dict[str, Any]:
        """
        使用 Gemini Live API 转录音频（真实实现）
        """
        try:
            if not self.live_session:
                logger.warning("⚠️ Live session not started, starting now...")
                await self.start_live_session()

            # 将 Base64 解码为字节流
            audio_bytes = base64.b64decode(audio_base64)
            
            logger.info(f"📤 Sending {len(audio_bytes)} bytes to Gemini Live API...")

            # 发送音频数据到 Gemini Live API
            await self.live_session.send_realtime_input(
                audio=types.Blob(
                    data=audio_bytes,
                    mime_type="audio/pcm;rate=16000"
                )
            )

            # 接收转录结果
            transcript_text = ""
            timeout_counter = 0
            max_timeout = 50  # 最多等待 5 秒（50 * 100ms）
            
            async for response in self.live_session.receive():
                # 检查是否有输入转录
                if response.server_content and response.server_content.input_transcription:
                    transcript_text = response.server_content.input_transcription.text
                    logger.info(f"📝 Transcription: {transcript_text}")
                    break  # 收到转录后立即返回
                
                # 检查对话是否完成
                if response.server_content and response.server_content.turn_complete:
                    logger.debug("Turn complete without transcription")
                    break
                
                # 超时保护
                timeout_counter += 1
                if timeout_counter >= max_timeout:
                    logger.warning("⚠️ Transcription timeout")
                    break
                
                await asyncio.sleep(0.1)

            # 如果没有获取到转录文本，返回空结果
            if not transcript_text:
                logger.info("ℹ️ No transcription (silence or noise)")
                return {
                    "id": str(uuid.uuid4()),
                    "timestamp": int(time.time() * 1000),
                    "originalText": "",
                    "translatedText": "",
                    "detectedLanguage": "unknown",
                    "startTime": self._format_time(time.time()),
                    "isFinal": False
                }

            # 检测语言
            detected_lang = self.detect_language(transcript_text)
            logger.info(f"🌍 Detected language: {detected_lang}")

            # 翻译成英文
            translated_text = transcript_text
            if detected_lang != 'en':
                logger.info(f"🔄 Translating {detected_lang} -> en...")
                translated_text = await self.translate_to_english(transcript_text, detected_lang)
                logger.info(f"✅ Translation: {translated_text}")

            return {
                "id": str(uuid.uuid4()),
                "timestamp": int(time.time() * 1000),
                "originalText": transcript_text,
                "translatedText": translated_text,
                "detectedLanguage": detected_lang,
                "startTime": self._format_time(time.time()),
                "isFinal": True
            }

        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "id": str(uuid.uuid4()),
                "timestamp": int(time.time() * 1000),
                "originalText": f"[转录错误: {str(e)}]",
                "translatedText": f"[Transcription Error: {str(e)}]",
                "detectedLanguage": "unknown",
                "startTime": self._format_time(time.time()),
                "isFinal": False
            }

    def _format_time(self, timestamp: float) -> str:
        """
        格式化时间戳为 HH:MM:SS
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S")


# 全局实例
transcription_service = TranscriptionService()
