/**
 * Audio Recorder Hook - 捕获麦克风音频
 */
import { useState, useCallback, useRef } from 'react';

interface UseAudioRecorderReturn {
  isRecording: boolean;
  startRecording: (onAudioData: (base64Data: string, timestamp: number) => void) => Promise<void>;
  stopRecording: () => void;
  error: string | null;
}

export const useAudioRecorder = (): UseAudioRecorderReturn => {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  const startRecording = useCallback(async (
    onAudioData: (base64Data: string, timestamp: number) => void
  ) => {
    try {
      setError(null);

      // 1. 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      mediaStreamRef.current = stream;

      // 2. 创建 AudioContext
      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);

      // 3. 创建 ScriptProcessorNode 处理音频数据
      // 4096 采样帧 = 约 256ms @ 16kHz
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        // 获取 PCM 数据（Float32Array，范围 -1.0 到 1.0）
        const float32Data = e.inputBuffer.getChannelData(0);

        // 转换为 16-bit PCM (Int16Array)
        const int16Data = new Int16Array(float32Data.length);
        for (let i = 0; i < float32Data.length; i++) {
          // 钳位到 [-1, 1] 并转换为 Int16
          const s = Math.max(-1, Math.min(1, float32Data[i]));
          int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // 转换为 Base64
        const uint8Data = new Uint8Array(int16Data.buffer);
        const base64 = btoa(String.fromCharCode(...uint8Data));

        // 发送音频数据
        onAudioData(base64, Date.now());
      };

      // 连接音频节点
      source.connect(processor);
      processor.connect(audioContext.destination);

      setIsRecording(true);
      console.log('🎤 Recording started');

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '无法访问麦克风';
      setError(errorMessage);
      console.error('录音错误:', err);
    }
  }, []);

  const stopRecording = useCallback(() => {
    // 停止所有音频轨道
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    // 断开音频处理器
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    // 关闭 AudioContext
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    setIsRecording(false);
    console.log('⏹️ Recording stopped');
  }, []);

  return {
    isRecording,
    startRecording,
    stopRecording,
    error
  };
};

