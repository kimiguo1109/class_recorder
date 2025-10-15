import React, { useState, useEffect, useRef } from 'react';

interface VoiceRegistrationProps {
  onClose: () => void;
}

export const VoiceRegistration: React.FC<VoiceRegistrationProps> = ({ onClose }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [status, setStatus] = useState<'idle' | 'recording' | 'processing' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [hasProfessorProfile, setHasProfessorProfile] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const intervalRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  useEffect(() => {
    // 检查是否已经注册了教授声音
    checkSpeakerStatus();
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const checkSpeakerStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/speaker/status');
      const data = await response.json();
      setHasProfessorProfile(data.hasProfessorProfile);
      if (data.hasProfessorProfile) {
        setMessage(data.message);
      }
    } catch (error) {
      console.error('Failed to check speaker status:', error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      });

      // 创建音频上下文
      audioContextRef.current = new AudioContext({ sampleRate: 16000 });
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      // 创建处理器节点（用于收集音频数据）
      processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      audioChunksRef.current = [];
      
      processorRef.current.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        const pcmData = new Int16Array(inputData.length);
        
        // 转换为 16-bit PCM
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // 保存音频块
        audioChunksRef.current.push(new Blob([pcmData.buffer]));
      };

      source.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);

      setIsRecording(true);
      setStatus('recording');
      setDuration(0);
      setMessage('正在录制教授的声音... 请教授说话（至少 5 秒）');

      // 计时器
      intervalRef.current = window.setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Failed to start recording:', error);
      setStatus('error');
      setMessage('无法访问麦克风，请检查权限设置');
    }
  };

  const stopRecording = async () => {
    if (!audioContextRef.current || !processorRef.current) return;

    // 停止录音
    if (processorRef.current) {
      processorRef.current.disconnect();
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    setIsRecording(false);
    setStatus('processing');
    setMessage('正在处理声音样本...');

    try {
      // 合并所有音频块
      const audioBlob = new Blob(audioChunksRef.current, { type: 'application/octet-stream' });
      const arrayBuffer = await audioBlob.arrayBuffer();
      const base64Audio = btoa(
        new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
      );

      // 发送到后端
      const response = await fetch('http://localhost:8000/api/speaker/register-professor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audioData: base64Audio })
      });

      const data = await response.json();

      if (data.success) {
        setStatus('success');
        setMessage(data.message);
        setHasProfessorProfile(true);
      } else {
        setStatus('error');
        setMessage(data.message);
      }
    } catch (error) {
      console.error('Failed to register voice:', error);
      setStatus('error');
      setMessage('声音注册失败，请重试');
    }
  };

  const clearProfile = async () => {
    if (!confirm('确定要清除教授声音配置吗？')) return;

    try {
      const response = await fetch('http://localhost:8000/api/speaker/clear-professor', {
        method: 'DELETE'
      });

      const data = await response.json();
      if (data.success) {
        setHasProfessorProfile(false);
        setStatus('idle');
        setMessage('');
      }
    } catch (error) {
      console.error('Failed to clear profile:', error);
      setMessage('清除失败，请重试');
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">👨‍🏫 教授声音注册</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ✕
          </button>
        </div>

        {/* 状态显示 */}
        <div className="mb-6">
          {hasProfessorProfile && status !== 'recording' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <p className="text-green-800 font-medium">✅ 已注册教授声音</p>
              <p className="text-green-600 text-sm mt-1">系统将自动识别教授和学生的发言</p>
            </div>
          )}

          {!hasProfessorProfile && status === 'idle' && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-yellow-800 font-medium">⚠️ 未注册教授声音</p>
              <p className="text-yellow-600 text-sm mt-1">请录制教授的声音样本以启用自动识别</p>
            </div>
          )}
        </div>

        {/* 说明 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-blue-800 mb-2">📝 使用说明</h3>
          <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
            <li>点击"开始录制"按钮</li>
            <li>让教授说话至少 5-10 秒</li>
            <li>点击"停止录制"完成注册</li>
            <li>系统将自动学习教授的声音特征</li>
          </ol>
        </div>

        {/* 录制控制 */}
        <div className="space-y-4">
          {/* 计时器 */}
          {isRecording && (
            <div className="text-center">
              <div className="text-4xl font-mono font-bold text-red-600">
                {formatDuration(duration)}
              </div>
              <p className="text-sm text-gray-600 mt-2">录制中...</p>
            </div>
          )}

          {/* 状态消息 */}
          {message && (
            <div className={`p-4 rounded-lg ${
              status === 'success' ? 'bg-green-50 text-green-800' :
              status === 'error' ? 'bg-red-50 text-red-800' :
              status === 'recording' ? 'bg-blue-50 text-blue-800' :
              'bg-gray-50 text-gray-800'
            }`}>
              {message}
            </div>
          )}

          {/* 按钮 */}
          <div className="flex gap-3">
            {!isRecording && (
              <>
                <button
                  onClick={startRecording}
                  disabled={status === 'processing'}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {hasProfessorProfile ? '🔄 重新录制' : '🎤 开始录制'}
                </button>
                
                {hasProfessorProfile && (
                  <button
                    onClick={clearProfile}
                    className="px-6 py-3 bg-red-100 text-red-700 rounded-xl font-semibold hover:bg-red-200 transition-all"
                  >
                    🗑️ 清除
                  </button>
                )}
              </>
            )}

            {isRecording && (
              <button
                onClick={stopRecording}
                className="flex-1 bg-red-500 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg transition-all"
              >
                ⏹️ 停止录制
              </button>
            )}
          </div>

          {/* 最小时长提示 */}
          {isRecording && duration < 5 && (
            <p className="text-sm text-orange-600 text-center">
              ⏱️ 建议录制至少 5 秒（当前 {duration} 秒）
            </p>
          )}
        </div>

        {/* 技术说明 */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            💡 使用 AI 声纹识别技术，保护隐私，数据仅存储在本地
          </p>
        </div>
      </div>
    </div>
  );
};

