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
        
        # 初始化 Whisper 模型（使用 small 模型，准确度更高）
        logger.info("🔄 Loading Whisper model (small)...")
        self.whisper_model = whisper.load_model("small")  # small 模型，准确度更高
        logger.info("✅ Whisper model loaded successfully")
        
        # 课程相关术语词汇表（用于 Whisper 提示）
        self.academic_terms = [
            # 数学
            "微积分", "calculus", "导数", "积分", "极限", "函数",
            "代数", "algebra", "几何", "geometry", "统计", "statistics",
            "概率", "probability", "线性代数", "linear algebra",
            "微分方程", "differential equations",
            
            # 物理
            "物理", "physics", "力学", "mechanics", "电磁学", "electromagnetism",
            "热力学", "thermodynamics", "量子力学", "quantum mechanics",
            
            # 计算机
            "算法", "algorithm", "数据结构", "data structure",
            "编程", "programming", "人工智能", "artificial intelligence",
            "机器学习", "machine learning", "深度学习", "deep learning",
            
            # 化学
            "化学", "chemistry", "有机化学", "organic chemistry",
            "无机化学", "inorganic chemistry",
            
            # 生物
            "生物", "biology", "细胞", "cell", "基因", "gene",
            "DNA", "蛋白质", "protein"
        ]
        
        logger.info(f"✅ TranscriptionService initialized with {len(self.academic_terms)} academic terms")

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

    def is_silence(self, audio_bytes: bytes) -> bool:
        """
        检测音频是否为静音
        """
        try:
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 计算音频能量（RMS）
            energy = np.sqrt(np.mean(audio_float ** 2))
            
            # 静音阈值（可调整）
            silence_threshold = 0.01
            
            is_silent = energy < silence_threshold
            if is_silent:
                logger.debug(f"🔇 Silence detected (energy: {energy:.4f})")
            
            return is_silent
            
        except Exception as e:
            logger.error(f"Silence detection failed: {e}")
            return False

    async def transcribe_audio_with_whisper(self, audio_bytes: bytes) -> str:
        """
        使用 Whisper 转录音频（带专业术语提示）
        """
        try:
            # 将 PCM 字节转换为 numpy 数组
            # 音频格式：16-bit PCM, 16kHz, mono
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # 转换为 float32 并归一化到 [-1, 1]
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 构建初始提示（包含常用学术术语）
            # Whisper 会参考这些词汇来提高准确度
            initial_prompt = "这是一节课程。包含：" + "、".join(self.academic_terms[:20])
            
            # Whisper 需要 16kHz 采样率（我们已经是 16kHz）
            # 在线程池中运行 Whisper（避免阻塞事件循环）
            result = await asyncio.to_thread(
                self.whisper_model.transcribe,
                audio_float,
                language=None,  # 自动检测语言（中英文）
                task="transcribe",
                fp16=False,  # 在 CPU 上运行
                initial_prompt=initial_prompt,  # 提供专业术语提示
                temperature=0.0  # 降低温度，减少随机性
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

    async def transcribe_audio(self, audio_base64: str, session_id: str = None, ws_manager = None) -> Dict[str, Any]:
        """
        使用 Whisper 进行真实的音频转录
        """
        try:
            # 解码 Base64 音频数据
            audio_bytes = base64.b64decode(audio_base64)
            
            # 先检测是否为静音，跳过静音块
            if self.is_silence(audio_bytes):
                logger.debug(f"⏭️ Skipping silence ({len(audio_bytes)} bytes)")
                return {
                    "id": str(uuid.uuid4()),
                    "timestamp": int(time.time() * 1000),
                    "originalText": "",
                    "translatedText": "",
                    "detectedLanguage": "unknown",
                    "startTime": self._format_time(time.time()),
                    "isFinal": False
                }
            
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

            # 先返回原文（不等待翻译）
            result = {
                "id": str(uuid.uuid4()),
                "timestamp": int(time.time() * 1000),
                "originalText": transcript_text,
                "translatedText": transcript_text if detected_lang == 'en' else "",  # 英文不翻译
                "detectedLanguage": detected_lang,
                "startTime": self._format_time(time.time()),
                "isFinal": True
            }
            
            # 如果是中文，后台翻译（不阻塞）
            if detected_lang == 'zh' and session_id and ws_manager:
                logger.info(f"🔄 Starting background translation...")
                # 启动后台翻译任务，翻译完成后推送更新
                asyncio.create_task(
                    self._translate_in_background(
                        transcript_text, 
                        result["id"], 
                        session_id, 
                        ws_manager
                    )
                )
            
            return result

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

    async def _translate_in_background(self, text: str, block_id: str, session_id: str, ws_manager):
        """
        后台翻译（不阻塞主流程），完成后推送更新
        """
        try:
            translation = await self.translate_to_english(text, 'zh')
            logger.info(f"✅ Background translation complete for {block_id}: {translation}")
            
            # 通过 WebSocket 推送翻译更新
            await ws_manager.send_message(session_id, {
                "type": "translation_update",
                "data": {
                    "id": block_id,
                    "translatedText": translation
                }
            })
            logger.info(f"📤 Translation update sent to client: {block_id}")
            
        except Exception as e:
            logger.error(f"❌ Background translation failed: {e}")

    def _format_time(self, timestamp: float) -> str:
        """
        格式化时间戳为 HH:MM:SS
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S")


# 全局实例
transcription_service = TranscriptionService()
