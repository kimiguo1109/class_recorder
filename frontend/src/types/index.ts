/**
 * TypeScript 类型定义
 */

export interface TranscriptBlock {
  id: string;
  timestamp: number;
  originalText: string;
  translatedText: string;
  detectedLanguage: string;
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

