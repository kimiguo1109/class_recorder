"""
转录服务 - 使用 Whisper 进行实时音频转录和 Gemini 翻译
"""
import asyncio
import base64
import io
import time
import uuid
import logging
from typing import Optional, Dict, Any
import aiohttp
import numpy as np
from config import settings
import google.generativeai as genai

# Whisper 导入
import whisper
import torch

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    实时转录服务
    使用 OpenAI Whisper 进行音频转录，Gemini API 进行翻译
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.generation_model = settings.GEMINI_GENERATION_MODEL
        self.api_base_url = "https://aiplatform.googleapis.com/v1/publishers/google/models"
        
        # 配置 Gemini API
        genai.configure(api_key=self.api_key)
        
        # 初始化 Whisper 模型
        logger.info("🔄 Loading Whisper model (base)...")
        self.whisper_model = whisper.load_model("base")  # 使用 base 模型，速度和准确度平衡
        logger.info("✅ Whisper model loaded successfully")
        
        logger.info(f"✅ TranscriptionService initialized")

    async def start_live_session(self):
        """
        启动会话（Whisper 不需要预先建立会话）
        """
        logger.info("✅ Whisper session ready")
        return True

    async def stop_live_session(self):
        """
        停止会话
        """
        logger.info("✅ Session stopped")

    async def call_gemini_api(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        调用 Gemini API（用于翻译）
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
        简单的语言检测（只支持中英文）
        """
        if not text:
            return 'en'

        # 中文检测
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len(text.replace(' ', ''))
        
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return 'zh'
        else:
            return 'en'

    async def translate_to_english(self, text: str, source_lang: str) -> str:
        """
        将文本翻译成英文
        """
        if source_lang == 'en':
            return text

        prompt = f"""Translate the following Chinese text to English. 
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

    async def transcribe_audio_with_whisper(self, audio_bytes: bytes) -> str:
        """
        使用 Whisper 转录音频
        """
        try:
            # 将 PCM 字节转换为 numpy 数组
            # 音频格式：16-bit PCM, 16kHz, mono
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # 转换为 float32 并归一化到 [-1, 1]
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Whisper 需要 16kHz 采样率（我们已经是 16kHz）
            # 在线程池中运行 Whisper（避免阻塞事件循环）
            result = await asyncio.to_thread(
                self.whisper_model.transcribe,
                audio_float,
                language=None,  # 自动检测语言（中英文）
                task="transcribe",
                fp16=False  # 在 CPU 上运行
            )
            
            transcript = result["text"].strip()
            detected_lang = result.get("language", "unknown")
            
            logger.info(f"📝 Whisper transcription: '{transcript}' (lang: {detected_lang})")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            import traceback
            traceback.print_exc()
            return ""

    async def transcribe_audio(self, audio_base64: str) -> Dict[str, Any]:
        """
        使用 Whisper 进行真实的音频转录
        """
        try:
            # 解码 Base64 音频数据
            audio_bytes = base64.b64decode(audio_base64)
            logger.info(f"📤 Processing {len(audio_bytes)} bytes audio with Whisper...")

            # 使用 Whisper 转录
            transcript_text = await self.transcribe_audio_with_whisper(audio_bytes)
            
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

            # 检测语言（中英文）
            detected_lang = self.detect_language(transcript_text)
            logger.info(f"🌍 Detected language: {detected_lang}")

            # 翻译成英文（如果是中文）
            translated_text = transcript_text
            if detected_lang == 'zh':
                logger.info(f"🔄 Translating Chinese to English...")
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
