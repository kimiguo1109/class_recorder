/**
 * 底部控制条组件
 */
import type { ConnectionStatus } from '../../types';

interface BottomControlsProps {
  isRecording: boolean;
  connectionStatus: ConnectionStatus;
  onStartRecording: () => void;
  onStopRecording: () => void;
  duration: number;
}

export const BottomControls = ({
  isRecording,
  connectionStatus,
  onStartRecording,
  onStopRecording,
  duration
}: BottomControlsProps) => {
  return (
    <div className="px-6 py-4">
      <div className="flex items-center gap-6">
        {/* 录音按钮 */}
        <button
          onClick={isRecording ? onStopRecording : onStartRecording}
          disabled={connectionStatus === 'connecting'}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${
            isRecording
              ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg'
              : 'bg-blue-500 hover:bg-blue-600 text-white shadow-md disabled:bg-gray-300 disabled:cursor-not-allowed'
          }`}
        >
          {isRecording ? (
            <>
              <span className="inline-block w-3 h-3 bg-white rounded-full animate-pulse"></span>
              停止录音
            </>
          ) : (
            <>
              <span className="text-xl">🎙️</span>
              开始录音
            </>
          )}
        </button>

        {/* 录音时长 */}
        {isRecording && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">录音时长:</span>
            <span className="text-lg font-mono font-semibold text-gray-800">
              {formatDuration(duration)}
            </span>
          </div>
        )}

        {/* 音频波形占位 */}
        <div className="flex-1 flex items-center">
          {isRecording && (
            <div className="w-full h-12 bg-gray-100 rounded-lg flex items-center justify-center">
              <WaveformPlaceholder />
            </div>
          )}
        </div>

        {/* 连接状态指示器 */}
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            connectionStatus === 'connected' 
              ? 'bg-green-500' 
              : connectionStatus === 'connecting'
              ? 'bg-yellow-500 animate-pulse'
              : 'bg-gray-400'
          }`} />
          <span className="text-sm text-gray-600">
            {connectionStatus === 'connected' ? '已连接' : 
             connectionStatus === 'connecting' ? '连接中...' : '未连接'}
          </span>
        </div>
      </div>
    </div>
  );
};

// 格式化时长 (秒 -> MM:SS)
const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

// 音频波形占位符（简化版）
const WaveformPlaceholder = () => (
  <div className="flex items-center justify-center gap-1 h-full px-4">
    {[...Array(30)].map((_, i) => (
      <div
        key={i}
        className="w-1 bg-blue-400 rounded-full animate-pulse"
        style={{
          height: `${20 + Math.random() * 60}%`,
          animationDelay: `${i * 0.05}s`
        }}
      />
    ))}
  </div>
);

