/**
 * TypeScript 类型定义
 */

export interface TranscriptBlock {
  id: string;
  timestamp: number;
  originalText: string;
  translatedText: string;
  detectedLanguage: string;
  speaker?: string;  // 说话人类型 (professor/student/unknown)
  speakerConfidence?: number;  // 识别置信度 (0-1)
  startTime: string;
  isFinal: boolean;
}

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

export type ViewMode = 'original' | 'translated' | 'bilingual';

export interface WebSocketMessage {
  type: 'transcript' | 'error' | 'ping' | 'pong';
  data?: TranscriptBlock;
  message?: string;
  timestamp?: number;
}

