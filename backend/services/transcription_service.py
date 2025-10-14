"""
转录服务 - 使用 Gemini API 进行音频转录和翻译
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
import google.generativeai as genai

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    实时转录服务
    使用 Gemini API 进行音频转录和翻译
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.generation_model = settings.GEMINI_GENERATION_MODEL
        self.api_base_url = "https://aiplatform.googleapis.com/v1/publishers/google/models"
        
        # 配置 Gemini API
        genai.configure(api_key=self.api_key)
        
        logger.info(f"✅ TranscriptionService initialized with model: {self.generation_model}")

    async def start_live_session(self):
        """
        启动会话（占位符，实际不需要预先建立会话）
        """
        logger.info(f"✅ Session ready")
        return True

    async def stop_live_session(self):
        """
        停止会话（占位符）
        """
        logger.info("✅ Session stopped")

    async def call_gemini_api(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        调用 Gemini API（用于翻译等文本任务）
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

    async def transcribe_audio_with_whisper(self, audio_base64: str) -> str:
        """
        使用 Gemini API 尝试转录音频
        注意：当前 google-generativeai SDK 可能不支持音频输入
        这是一个临时实现，用于演示流程
        """
        try:
            # 创建 Gemini 模型
            model = genai.GenerativeModel(self.generation_model)
            
            # 尝试使用文件 API（如果支持音频）
            # 注意：这可能需要不同的 API 端点或方法
            prompt = "Please transcribe the audio content."
            
            # 由于当前限制，我们暂时返回模拟结果
            # 真实的音频转录需要：
            # 1. 使用 Google Cloud Speech-to-Text API
            # 2. 或等待 Gemini Live API Python SDK 正式发布
            logger.warning("⚠️ Audio transcription with Gemini is not fully supported yet")
            return ""
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return ""

    async def transcribe_audio(self, audio_base64: str) -> Dict[str, Any]:
        """
        音频转录（当前使用模拟数据，真实转录需要额外的 API）
        
        真实实现选项：
        1. Google Cloud Speech-to-Text API（需要额外配置）
        2. Gemini Live API（需要专门的 SDK，当前 python 包不支持）
        3. 其他语音识别服务（Whisper API, Azure Speech 等）
        """
        try:
            audio_bytes = base64.b64decode(audio_base64)
            logger.info(f"📤 Received {len(audio_bytes)} bytes audio data")

            # TODO: 集成真实的语音识别 API
            # 当前使用随机模拟数据用于演示
            import random
            sample_texts = [
                "今天天气很好，我们来学习人工智能",
                "机器学习是人工智能的一个重要分支",
                "深度学习使用神经网络来处理复杂问题",
                "自然语言处理让计算机理解人类语言",
                "这是一个实时转录系统的演示",
                "课程内容包括理论和实践两个部分",
                "Good morning everyone, welcome to the class",
                "今日は人工知能について勉強します",
                "안녕하세요, 오늘은 AI에 대해 배웁니다"
            ]
            
            # 90% 概率返回转录，10% 概率返回空（模拟静音）
            if random.random() < 0.9:
                transcript_text = random.choice(sample_texts)
            else:
                transcript_text = ""
            
            if not transcript_text:
                logger.info("ℹ️ No transcription (silence)")
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
            logger.info(f"📝 Transcription: {transcript_text} ({detected_lang})")

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
