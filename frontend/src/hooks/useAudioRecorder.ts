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
  const audioBufferRef = useRef<Int16Array[]>([]);
  const lastSendTimeRef = useRef<number>(0);

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

        // 累积音频数据
        audioBufferRef.current.push(int16Data);

        // 每3秒发送一次（避免频繁调用 API）
        const now = Date.now();
        if (now - lastSendTimeRef.current >= 3000) {
          // 合并所有缓冲的音频数据
          const totalLength = audioBufferRef.current.reduce((sum, arr) => sum + arr.length, 0);
          const mergedData = new Int16Array(totalLength);
          let offset = 0;
          for (const chunk of audioBufferRef.current) {
            mergedData.set(chunk, offset);
            offset += chunk.length;
          }

          // 转换为 Base64
          const uint8Data = new Uint8Array(mergedData.buffer);
          const base64 = btoa(String.fromCharCode(...uint8Data));

          // 发送音频数据
          onAudioData(base64, now);

          // 清空缓冲区
          audioBufferRef.current = [];
          lastSendTimeRef.current = now;
        }
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
    console.log('🛑 Stopping recording...');
    
    // 清空音频缓冲区
    audioBufferRef.current = [];
    lastSendTimeRef.current = 0;

    // 断开音频处理器（必须先断开，再停止轨道）
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current.onaudioprocess = null;
      processorRef.current = null;
    }

    // 关闭 AudioContext
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(err => {
        console.warn('Failed to close AudioContext:', err);
      });
      audioContextRef.current = null;
    }

    // 停止所有音频轨道
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => {
        track.stop();
        console.log('Track stopped:', track.kind);
      });
      mediaStreamRef.current = null;
    }

    setIsRecording(false);
    console.log('✅ Recording stopped successfully');
  }, []);

  return {
    isRecording,
    startRecording,
    stopRecording,
    error
  };
};

