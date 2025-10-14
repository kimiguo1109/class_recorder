/**
 * 转录面板组件
 */
import { useState } from 'react';
import type { TranscriptBlock, ViewMode } from '../../types';

interface TranscriptPanelProps {
  transcripts: TranscriptBlock[];
}

export const TranscriptPanel = ({ transcripts }: TranscriptPanelProps) => {
  const [viewMode, setViewMode] = useState<ViewMode>('bilingual');

  return (
    <div className="h-full flex flex-col">
      {/* 标题栏 */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">
            📝 Live Transcripts
          </h2>
          
          {/* 语言切换按钮 */}
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('original')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                viewMode === 'original'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              原文
            </button>
            <button
              onClick={() => setViewMode('translated')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                viewMode === 'translated'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              英文翻译
            </button>
            <button
              onClick={() => setViewMode('bilingual')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                viewMode === 'bilingual'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              双语对照
            </button>
          </div>
        </div>
      </div>

      {/* 转录内容区 */}
      <div className="flex-1 overflow-y-auto p-6">
        {transcripts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="text-6xl mb-4">🎤</div>
            <p className="text-lg">No transcript yet.</p>
            <p className="text-sm mt-2">Try speaking louder or closer to the microphone.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {transcripts.map((transcript) => (
              <TranscriptBlock 
                key={transcript.id} 
                transcript={transcript} 
                viewMode={viewMode} 
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// 单个转录块组件
const TranscriptBlock = ({ 
  transcript, 
  viewMode 
}: { 
  transcript: TranscriptBlock; 
  viewMode: ViewMode;
}) => {
  return (
    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
      {/* 时间戳和语言标签 */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-500 font-mono">{transcript.startTime}</span>
        <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full">
          {getLanguageName(transcript.detectedLanguage)}
        </span>
      </div>

      {/* 文本内容 */}
      {viewMode === 'original' && (
        <p className="text-gray-800 leading-relaxed">
          {transcript.originalText}
        </p>
      )}

      {viewMode === 'translated' && (
        <p className="text-gray-800 leading-relaxed">
          {transcript.translatedText}
        </p>
      )}

      {viewMode === 'bilingual' && (
        <div className="space-y-2">
          <div>
            <span className="text-xs text-gray-500 font-semibold">原文:</span>
            <p className="text-gray-800 mt-1 leading-relaxed">
              {transcript.originalText}
            </p>
          </div>
          {transcript.detectedLanguage !== 'en' && (
            <div className="pt-2 border-t border-gray-200">
              <span className="text-xs text-gray-500 font-semibold">English:</span>
              <p className="text-gray-600 mt-1 leading-relaxed">
                {transcript.translatedText}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// 语言代码转换为语言名称
const getLanguageName = (code: string): string => {
  const languageMap: Record<string, string> = {
    en: 'English',
    zh: '中文',
    ja: '日本語',
    ko: '한국어',
    es: 'Español',
    fr: 'Français',
    de: 'Deutsch',
    ru: 'Русский',
    ar: 'العربية'
  };
  return languageMap[code] || code;
};

