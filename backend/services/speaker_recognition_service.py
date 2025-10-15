"""
说话人识别服务 - 使用声纹特征识别教授和学生
"""
import os
import json
import logging
import numpy as np
import torch
from typing import Dict, Optional, List, Tuple
import io
import wave

logger = logging.getLogger(__name__)

class SpeakerRecognitionService:
    """
    说话人识别服务
    功能：
    1. 声纹注册（录制教授声音样本）
    2. 实时声纹识别（判断是否是教授）
    3. 多说话人区分
    """
    
    def __init__(self):
        self.embeddings_cache: Dict[str, np.ndarray] = {}  # 缓存声纹特征
        self.professor_embedding: Optional[np.ndarray] = None
        self.similarity_threshold = 0.7  # 相似度阈值（0-1）
        
        # 声纹特征提取模型（使用 pyannote.audio）
        try:
            from pyannote.audio import Model
            from pyannote.audio.pipelines import SpeakerDiarization
            from pyannote.audio import Inference
            
            logger.info("🔄 Loading speaker embedding model...")
            
            # 使用预训练的声纹特征提取模型
            # 这个模型可以提取说话人的声纹特征向量
            self.embedding_model = Inference(
                "pyannote/embedding",
                window="whole"  # 处理整个音频片段
            )
            
            logger.info("✅ Speaker embedding model loaded")
            self.model_available = True
            
        except Exception as e:
            logger.warning(f"⚠️ Speaker recognition model not available: {e}")
            logger.info("💡 Falling back to simple energy-based detection")
            self.model_available = False
            self.embedding_model = None
        
        # 加载已保存的教授声纹
        self._load_professor_embedding()
    
    def _load_professor_embedding(self):
        """从文件加载教授的声纹特征"""
        embedding_file = "professor_embedding.npy"
        if os.path.exists(embedding_file):
            try:
                self.professor_embedding = np.load(embedding_file)
                logger.info(f"✅ Loaded professor voice profile (shape: {self.professor_embedding.shape})")
            except Exception as e:
                logger.error(f"❌ Failed to load professor embedding: {e}")
    
    def _save_professor_embedding(self):
        """保存教授的声纹特征到文件"""
        if self.professor_embedding is not None:
            try:
                np.save("professor_embedding.npy", self.professor_embedding)
                logger.info("✅ Professor voice profile saved")
            except Exception as e:
                logger.error(f"❌ Failed to save professor embedding: {e}")
    
    def extract_embedding(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[np.ndarray]:
        """
        提取音频的声纹特征向量
        
        参数:
            audio_data: 音频数据（numpy array，float32，[-1, 1]）
            sample_rate: 采样率（默认 16000Hz）
        
        返回:
            声纹特征向量（512维）
        """
        if not self.model_available or self.embedding_model is None:
            # 使用简单的音频特征（能量、过零率等）
            return self._extract_simple_features(audio_data)
        
        try:
            # 确保音频长度至少 1 秒
            min_samples = sample_rate * 1  # 1秒
            if len(audio_data) < min_samples:
                # 填充到 1 秒
                audio_data = np.pad(audio_data, (0, min_samples - len(audio_data)), 'constant')
            
            # pyannote 需要的格式：{"waveform": tensor, "sample_rate": int}
            audio_tensor = torch.from_numpy(audio_data).unsqueeze(0)  # 添加 batch 维度
            
            # 提取声纹特征
            embedding = self.embedding_model({
                "waveform": audio_tensor,
                "sample_rate": sample_rate
            })
            
            # 转换为 numpy 数组
            if isinstance(embedding, torch.Tensor):
                embedding = embedding.detach().cpu().numpy()
            
            # 归一化（方便后续计算余弦相似度）
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            logger.debug(f"📊 Extracted embedding shape: {embedding.shape}")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Embedding extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_simple_features(self, audio_data: np.ndarray) -> np.ndarray:
        """
        提取简单的音频特征（后备方案）
        包括：能量、过零率、频谱质心等
        """
        try:
            # 1. 能量（RMS）
            energy = np.sqrt(np.mean(audio_data ** 2))
            
            # 2. 过零率（Zero Crossing Rate）
            zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_data)))) / (2 * len(audio_data))
            
            # 3. 频谱质心（需要 FFT）
            fft = np.fft.rfft(audio_data)
            magnitude = np.abs(fft)
            freqs = np.fft.rfftfreq(len(audio_data), 1/16000)
            spectral_centroid = np.sum(freqs * magnitude) / (np.sum(magnitude) + 1e-8)
            
            # 4. 频谱带宽
            spectral_bandwidth = np.sqrt(
                np.sum(((freqs - spectral_centroid) ** 2) * magnitude) / (np.sum(magnitude) + 1e-8)
            )
            
            # 组合成特征向量（4维，需要扩展到更高维度）
            simple_features = np.array([
                energy,
                zero_crossings,
                spectral_centroid / 8000,  # 归一化
                spectral_bandwidth / 8000   # 归一化
            ])
            
            # 扩展到 512 维（重复特征）
            simple_features = np.tile(simple_features, 128)
            
            return simple_features
            
        except Exception as e:
            logger.error(f"❌ Simple feature extraction failed: {e}")
            return np.random.rand(512)  # 返回随机向量作为后备
    
    def register_professor_voice(self, audio_bytes: bytes) -> bool:
        """
        注册教授的声音（录制样本）
        
        参数:
            audio_bytes: 音频数据（PCM，16-bit，16kHz，mono）
        
        返回:
            是否成功注册
        """
        try:
            # 转换为 numpy 数组
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 提取声纹特征
            embedding = self.extract_embedding(audio_float)
            
            if embedding is None:
                logger.error("❌ Failed to extract embedding for professor voice")
                return False
            
            # 保存声纹特征
            self.professor_embedding = embedding
            self._save_professor_embedding()
            
            logger.info(f"✅ Professor voice registered (embedding shape: {embedding.shape})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Professor voice registration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        计算两个声纹特征的相似度（余弦相似度）
        
        返回:
            相似度（0-1），1表示完全相同
        """
        try:
            # 余弦相似度
            similarity = np.dot(embedding1.flatten(), embedding2.flatten())
            # 确保在 [0, 1] 范围内
            similarity = max(0, min(1, (similarity + 1) / 2))
            return float(similarity)
        except Exception as e:
            logger.error(f"❌ Similarity calculation failed: {e}")
            return 0.0
    
    def identify_speaker(self, audio_bytes: bytes) -> Tuple[str, float]:
        """
        识别说话人（教授 or 学生）
        
        参数:
            audio_bytes: 音频数据（PCM，16-bit，16kHz，mono）
        
        返回:
            (说话人类型, 置信度)
            - 说话人类型: "professor" 或 "student" 或 "unknown"
            - 置信度: 0-1
        """
        try:
            # 如果没有注册教授声音，返回 unknown
            if self.professor_embedding is None:
                logger.debug("ℹ️ No professor voice profile registered")
                return "unknown", 0.0
            
            # 转换音频为 numpy 数组
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # 检查音频能量（过滤静音）
            energy = np.sqrt(np.mean(audio_float ** 2))
            if energy < 0.01:
                logger.debug(f"🔇 Silence detected (energy: {energy:.4f})")
                return "unknown", 0.0
            
            # 提取当前音频的声纹特征
            current_embedding = self.extract_embedding(audio_float)
            
            if current_embedding is None:
                logger.error("❌ Failed to extract embedding for current audio")
                return "unknown", 0.0
            
            # 计算与教授声音的相似度
            similarity = self.calculate_similarity(current_embedding, self.professor_embedding)
            
            logger.debug(f"📊 Speaker similarity: {similarity:.4f} (threshold: {self.similarity_threshold})")
            
            # 判断是否是教授
            if similarity >= self.similarity_threshold:
                return "professor", similarity
            else:
                return "student", 1.0 - similarity
            
        except Exception as e:
            logger.error(f"❌ Speaker identification failed: {e}")
            import traceback
            traceback.print_exc()
            return "unknown", 0.0
    
    def has_professor_profile(self) -> bool:
        """检查是否已注册教授声音"""
        return self.professor_embedding is not None
    
    def clear_professor_profile(self):
        """清除教授声音配置"""
        self.professor_embedding = None
        if os.path.exists("professor_embedding.npy"):
            os.remove("professor_embedding.npy")
        logger.info("✅ Professor voice profile cleared")


# 全局实例
speaker_recognition_service = SpeakerRecognitionService()

