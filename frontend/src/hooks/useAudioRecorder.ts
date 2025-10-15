/**
 * Audio Recorder Hook - 捕获麦克风音频
 */
import { useState, useCallback, useRef } from 'react';

interface UseAudioRecorderReturn {
  isRecording: boolean;
  startRecording: (onAudioData: (base64Data: string, timestamp: number) => void) => Promise<void>;
  stopRecording: () => Blob | null;
  error: string | null;
  recordingBlob: Blob | null;
}

export const useAudioRecorder = (): UseAudioRecorderReturn => {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recordingBlob, setRecordingBlob] = useState<Blob | null>(null);
  
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const audioBufferRef = useRef<Int16Array[]>([]);
  const allAudioDataRef = useRef<Int16Array[]>([]); // 保存完整录音
  const lastSendTimeRef = useRef<number>(0);
  const silenceCountRef = useRef<number>(0); // 连续静音帧计数

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
        allAudioDataRef.current.push(int16Data); // 同时保存到完整录音

        // 计算当前帧的音频能量（用于静音检测）
        let sumSquare = 0;
        for (let i = 0; i < float32Data.length; i++) {
          sumSquare += float32Data[i] * float32Data[i];
        }
        const rms = Math.sqrt(sumSquare / float32Data.length);
        const isSilent = rms < 0.01; // 静音阈值

        // 更新静音计数
        if (isSilent) {
          silenceCountRef.current++;
        } else {
          silenceCountRef.current = 0;
        }

        const now = Date.now();
        
        // 初始化 lastSendTimeRef（第一次）
        if (lastSendTimeRef.current === 0) {
          lastSendTimeRef.current = now;
        }
        
        const timeSinceLastSend = now - lastSendTimeRef.current;
        const bufferDuration = audioBufferRef.current.length * 4096 / 16000; // 秒

        // 智能发送策略：
        // 1. 至少累积 5 秒音频（给 Whisper 更多上下文）
        // 2. 检测到连续 10 帧（约 2.5 秒）静音后发送（自然停顿点）
        // 3. 最多累积 10 秒（避免过长）
        const shouldSend = (
          (timeSinceLastSend >= 5000 && silenceCountRef.current >= 10) || // 5秒后遇到停顿
          timeSinceLastSend >= 10000 // 最长10秒
        );

        if (shouldSend && audioBufferRef.current.length > 0) {
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
          console.log(`📤 Sending ${bufferDuration.toFixed(1)}s audio (silence: ${isSilent})`);
          onAudioData(base64, now);

          // 清空缓冲区和静音计数
          audioBufferRef.current = [];
          silenceCountRef.current = 0;
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
    
    // 生成完整的录音文件（WAV格式）
    let audioBlob: Blob | null = null;
    
    if (allAudioDataRef.current.length > 0) {
      // 合并所有音频数据
      const totalLength = allAudioDataRef.current.reduce((sum, arr) => sum + arr.length, 0);
      const mergedData = new Int16Array(totalLength);
      let offset = 0;
      for (const chunk of allAudioDataRef.current) {
        mergedData.set(chunk, offset);
        offset += chunk.length;
      }
      
      // 创建 WAV 文件
      audioBlob = createWavBlob(mergedData, 16000, 1);
      setRecordingBlob(audioBlob);
      console.log(`📼 Recording saved: ${(audioBlob.size / 1024 / 1024).toFixed(2)} MB`);
    }
    
    // 清空音频缓冲区
    audioBufferRef.current = [];
    allAudioDataRef.current = [];
    lastSendTimeRef.current = 0;
    silenceCountRef.current = 0;

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
    
    return audioBlob;
  }, []);

  return {
    isRecording,
    startRecording,
    stopRecording,
    error,
    recordingBlob
  };
};

// 创建 WAV 文件的辅助函数
function createWavBlob(pcmData: Int16Array, sampleRate: number, numChannels: number): Blob {
  const dataLength = pcmData.length * 2; // 16-bit = 2 bytes per sample
  const buffer = new ArrayBuffer(44 + dataLength);
  const view = new DataView(buffer);

  // WAV 文件头
  // "RIFF" chunk descriptor
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + dataLength, true); // File size - 8
  writeString(view, 8, 'WAVE');

  // "fmt " sub-chunk
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
  view.setUint16(20, 1, true); // AudioFormat (1 for PCM)
  view.setUint16(22, numChannels, true); // NumChannels
  view.setUint32(24, sampleRate, true); // SampleRate
  view.setUint32(28, sampleRate * numChannels * 2, true); // ByteRate
  view.setUint16(32, numChannels * 2, true); // BlockAlign
  view.setUint16(34, 16, true); // BitsPerSample

  // "data" sub-chunk
  writeString(view, 36, 'data');
  view.setUint32(40, dataLength, true); // Subchunk2Size

  // 写入 PCM 数据
  const offset = 44;
  for (let i = 0; i < pcmData.length; i++) {
    view.setInt16(offset + i * 2, pcmData[i], true);
  }

  return new Blob([buffer], { type: 'audio/wav' });
}

function writeString(view: DataView, offset: number, string: string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}
