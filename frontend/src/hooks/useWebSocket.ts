/**
 * WebSocket Hook - 管理 WebSocket 连接
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import type { ConnectionStatus, TranscriptBlock } from '../types';

const WS_URL = 'ws://localhost:8000/ws/transcribe';

interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus;
  connect: (sessionId: string) => void;
  disconnect: () => void;
  sendAudioChunk: (audioData: string, timestamp: number) => void;
  transcripts: TranscriptBlock[];
}

export const useWebSocket = (): UseWebSocketReturn => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [transcripts, setTranscripts] = useState<TranscriptBlock[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback((sessionId: string = 'default') => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    setConnectionStatus('connecting');
    const ws = new WebSocket(`${WS_URL}?session_id=${sessionId}`);

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      setConnectionStatus('connected');
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('Received message:', message);

        if (message.type === 'transcript' && message.data) {
          setTranscripts((prev) => [...prev, message.data]);
        } else if (message.type === 'error') {
          console.error('Server error:', message.message);
        } else if (message.type === 'ping') {
          // 响应心跳
          ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
        }
      } catch (error) {
        console.error('Failed to parse message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setConnectionStatus('disconnected');
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      setConnectionStatus('disconnected');

      // 自动重连
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current - 1), 30000);
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`);
        setTimeout(() => connect(sessionId), delay);
      } else {
        console.error('Max reconnection attempts reached');
      }
    };

    wsRef.current = ws;
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      reconnectAttempts.current = maxReconnectAttempts; // 阻止自动重连
      
      // 发送停止信号给后端
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'stop' }));
        console.log('📤 Sent stop signal to server');
      }
      
      // 延迟关闭，确保停止信号发送成功
      setTimeout(() => {
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
      }, 100);
      
      setConnectionStatus('disconnected');
    }
  }, []);

  const sendAudioChunk = useCallback((audioData: string, timestamp: number) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'audio_chunk',
        data: audioData,
        timestamp
      }));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // 清理函数
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connectionStatus,
    connect,
    disconnect,
    sendAudioChunk,
    transcripts
  };
};

