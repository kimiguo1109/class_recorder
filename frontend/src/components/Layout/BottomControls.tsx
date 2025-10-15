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
  onExport: (format: 'markdown' | 'text') => void;
  recordingUrl?: string | null;
}

export const BottomControls = ({
  isRecording,
  connectionStatus,
  onStartRecording,
  onStopRecording,
  duration,
  onExport,
  recordingUrl
}: BottomControlsProps) => {
  
  const handleDownloadRecording = async () => {
    if (!recordingUrl) return;
    
    try {
      // 确保 URL 是完整的，如果是相对路径则添加域名
      const fullUrl = recordingUrl.startsWith('http') 
        ? recordingUrl 
        : `http://localhost:8000${recordingUrl}`;
      
      // 从 URL 中提取文件名（去掉查询参数）
      const urlObj = new URL(fullUrl);
      const filename = urlObj.pathname.split('/').pop() || 'recording.wav';
      
      // 通过 fetch 获取文件（避免跳转到 S3）
      const response = await fetch(fullUrl);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const blob = await response.blob();
      
      // 创建本地 Blob URL 并下载
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      // 清理 Blob URL
      setTimeout(() => URL.revokeObjectURL(blobUrl), 100);
      console.log('✅ 录音下载成功:', filename);
    } catch (error) {
      console.error('❌ 下载录音失败:', error);
      alert('下载录音失败，请重试');
    }
  };
  return (
    <div className="px-6 py-4 border-t border-gray-200 bg-white">
      <div className="flex items-center justify-between gap-6">
        {/* 左侧：录音按钮 */}
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

        {/* 中间：时长和波形 */}
        <div className="flex-1 flex items-center gap-4">
          {isRecording && (
            <>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">录音时长:</span>
                <span className="text-lg font-mono font-semibold text-gray-800">
                  {formatDuration(duration)}
                </span>
              </div>
              <div className="flex-1 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <WaveformPlaceholder />
              </div>
            </>
          )}
        </div>

        {/* 右侧：导出和连接状态 */}
        <div className="flex items-center gap-4">
          {/* 导出按钮 */}
          <div className="flex gap-2">
            <button
              onClick={() => onExport('markdown')}
              className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              title="导出为 Markdown"
            >
              📄 Markdown
            </button>
            <button
              onClick={() => onExport('text')}
              className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              title="导出为文本"
            >
              📝 Text
            </button>
            {/* 下载录音按钮 */}
            {recordingUrl && (
              <button
                onClick={handleDownloadRecording}
                className="px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg hover:shadow-lg transition-all"
                title="下载录音文件"
              >
                🎵 下载录音
              </button>
            )}
          </div>

          {/* 连接状态 */}
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
