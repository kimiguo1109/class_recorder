import { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { MainLayout } from './components/Layout/MainLayout';
import { TranscriptPanel } from './components/Transcript/TranscriptPanel';
import { TabsPanel } from './components/AITools/TabsPanel';
import { BottomControls } from './components/Layout/BottomControls';
import { VoiceRegistration } from './components/Speaker/VoiceRegistration';

function App() {
  const { connectionStatus, connect, disconnect, sendAudioChunk, transcripts } = useWebSocket();
  const { isRecording, startRecording, stopRecording, error } = useAudioRecorder();
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [duration, setDuration] = useState(0);
  const [notes, setNotes] = useState('');
  const [showVoiceRegistration, setShowVoiceRegistration] = useState(false);
  const [savedRecordingUrl, setSavedRecordingUrl] = useState<string | null>(null);

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

  const handleStopRecording = async () => {
    const audioBlob = stopRecording();
    disconnect();
    
    // 如果有录音，上传到后端
    if (audioBlob) {
      try {
        const formData = new FormData();
        formData.append('audio', audioBlob, `recording_${sessionId}.wav`);
        formData.append('sessionId', sessionId);
        
        const response = await fetch('http://localhost:8000/api/recording/upload', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
          setSavedRecordingUrl(data.downloadUrl);
          console.log('✅ Recording uploaded:', data.downloadUrl);
        }
      } catch (err) {
        console.error('❌ Failed to upload recording:', err);
      }
    }
  };

  const handleExport = async (format: 'markdown' | 'text') => {
    try {
      const response = await fetch(`http://localhost:8000/api/export/${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcripts, notes })
      });
      
      const data = await response.json();
      
      // 下载文件
      const blob = new Blob([data.content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  return (
    <>
      <MainLayout
        leftPanel={
          <TranscriptPanel 
            transcripts={transcripts}
            onOpenVoiceSettings={() => setShowVoiceRegistration(true)}
          />
        }
        rightPanel={<TabsPanel notes={notes} onNotesChange={setNotes} />}
        bottomControls={
          <BottomControls
            isRecording={isRecording}
            connectionStatus={connectionStatus}
            onStartRecording={handleStartRecording}
            onStopRecording={handleStopRecording}
            duration={duration}
            onExport={handleExport}
            recordingUrl={savedRecordingUrl}
          />
        }
      />

      {/* 声音注册对话框 */}
      {showVoiceRegistration && (
        <VoiceRegistration onClose={() => setShowVoiceRegistration(false)} />
      )}

      {/* 错误提示 Toast */}
      {error && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50">
          ❌ {error}
        </div>
      )}
    </>
  );
}

export default App;
