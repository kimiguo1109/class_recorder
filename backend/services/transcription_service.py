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

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    实时转录服务
    使用 Gemini 2.5 Flash Lite 进行音频转录和翻译
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_LIVE_MODEL
        # 使用 AI Vertex API endpoint
        self.api_base_url = "https://aiplatform.googleapis.com/v1/publishers/google/models"

    async def call_gemini_api(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        调用 Gemini API（使用 AI Vertex endpoint + 代理）
        """
        url = f"{self.api_base_url}/{self.model}:streamGenerateContent?key={self.api_key}"

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
                logger.info(f"Using proxy: {settings.HTTP_PROXY}")
                connector = aiohttp.TCPConnector()
            
            async with aiohttp.ClientSession(connector=connector) as session:
                # 设置代理
                proxy = settings.HTTP_PROXY if settings.USE_PROXY else None
                
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30),
                    proxy=proxy
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API error: {response.status} - {error_text}")
                        raise Exception(f"API error: {response.status}")

                    # streamGenerateContent 返回数组格式（流式响应）
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
                        # 兼容非流式响应
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
        转录音频（模拟实现，实际应使用 Gemini Live API）
        由于 Gemini Live API 需要 WebSocket 连接，这里先提供模拟实现
        """
        try:
            # TODO: 实际实现应该使用 Gemini Live API 的 WebSocket 连接
            # 这里先返回模拟数据用于测试
            logger.info("Transcribing audio chunk...")

            # 模拟转录结果
            transcript_text = "这是一段模拟的转录文本"  # 实际应从 Gemini API 获取

            # 检测语言
            detected_lang = self.detect_language(transcript_text)

            # 翻译成英文
            translated_text = transcript_text
            if detected_lang != 'en':
                translated_text = await self.translate_to_english(transcript_text, detected_lang)

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
            logger.error(f"Transcription error: {e}")
            raise

    def _format_time(self, timestamp: float) -> str:
        """
        格式化时间戳为 HH:MM:SS
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S")


# 全局实例
transcription_service = TranscriptionService()

