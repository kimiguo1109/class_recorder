import { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { MainLayout } from './components/Layout/MainLayout';
import { TranscriptPanel } from './components/Transcript/TranscriptPanel';
import { TabsPanel } from './components/AITools/TabsPanel';
import { BottomControls } from './components/Layout/BottomControls';

function App() {
  const { connectionStatus, connect, disconnect, sendAudioChunk, transcripts } = useWebSocket();
  const { isRecording, startRecording, stopRecording, error } = useAudioRecorder();
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [duration, setDuration] = useState(0);

  // 录音时长计时器
  useEffect(() => {
    let interval: number | undefined;
    if (isRecording) {
      interval = window.setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);
    } else {
      setDuration(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording]);

  const handleStartRecording = async () => {
    try {
      // 连接 WebSocket
      connect(sessionId);

      // 等待连接建立
      await new Promise(resolve => setTimeout(resolve, 1000));

      // 开始录音
      await startRecording((audioData, timestamp) => {
        sendAudioChunk(audioData, timestamp);
      });
    } catch (err) {
      console.error('Failed to start recording:', err);
    }
  };

  const handleStopRecording = () => {
    stopRecording();
    disconnect();
  };

  return (
    <>
      <MainLayout
        leftPanel={<TranscriptPanel transcripts={transcripts} />}
        rightPanel={<TabsPanel />}
        bottomControls={
          <BottomControls
            isRecording={isRecording}
            connectionStatus={connectionStatus}
            onStartRecording={handleStartRecording}
            onStopRecording={handleStopRecording}
            duration={duration}
          />
        }
      />

      {/* 错误提示 Toast */}
      {error && (
        <div className="fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg">
          ❌ {error}
        </div>
      )}
    </>
  );
}

export default App;
