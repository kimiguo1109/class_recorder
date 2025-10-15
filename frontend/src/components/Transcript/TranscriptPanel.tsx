/**
 * 转录面板组件
 */
import { useState } from 'react';
import type { TranscriptBlock, ViewMode } from '../../types';

interface TranscriptPanelProps {
  transcripts: TranscriptBlock[];
  onOpenVoiceSettings?: () => void;
}

export const TranscriptPanel = ({ transcripts, onOpenVoiceSettings }: TranscriptPanelProps) => {
  const [viewMode, setViewMode] = useState<ViewMode>('bilingual');

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 标题栏 */}
      <div className="px-6 py-3 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-base font-bold text-gray-800 flex items-center gap-2">
              <span className="text-xl">📝</span>
              Live Transcripts
            </h2>
            
            {/* 声音设置按钮 */}
            {onOpenVoiceSettings && (
              <button
                onClick={onOpenVoiceSettings}
                className="px-3 py-1.5 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-xs font-semibold rounded-lg hover:shadow-lg transition-all flex items-center gap-1"
              >
                👨‍🏫 教授声音设置
              </button>
            )}
          </div>
          
          {/* 语言切换按钮 */}
          <div className="flex gap-1 bg-white rounded-lg p-1 shadow-sm border border-gray-200">
            <button
              onClick={() => setViewMode('original')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                viewMode === 'original'
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              原文
            </button>
            <button
              onClick={() => setViewMode('translated')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                viewMode === 'translated'
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              English
            </button>
            <button
              onClick={() => setViewMode('bilingual')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                viewMode === 'bilingual'
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              双语
            </button>
          </div>
        </div>
      </div>

      {/* 转录内容区 */}
      <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
        {transcripts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="bg-gradient-to-br from-blue-100 to-purple-100 rounded-full p-8 mb-4">
              <div className="text-6xl">🎤</div>
            </div>
            <p className="text-lg font-semibold text-gray-700">No transcript yet.</p>
            <p className="text-sm text-gray-500 mt-2">Try speaking louder or closer to the microphone.</p>
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
  // 获取说话人图标和样式
  const getSpeakerInfo = (speaker?: string) => {
    switch (speaker) {
      case 'professor':
        return {
          icon: '👨‍🏫',
          label: '教授',
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-800',
          borderColor: 'border-blue-300'
        };
      case 'student':
        return {
          icon: '🧑‍🎓',
          label: '学生',
          bgColor: 'bg-green-100',
          textColor: 'text-green-800',
          borderColor: 'border-green-300'
        };
      default:
        return {
          icon: '🎤',
          label: '未知',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-600',
          borderColor: 'border-gray-300'
        };
    }
  };

  const speakerInfo = getSpeakerInfo(transcript.speaker);
  const confidencePercent = transcript.speakerConfidence 
    ? Math.round(transcript.speakerConfidence * 100) 
    : 0;

  return (
    <div className={`p-4 bg-white rounded-xl border-2 ${speakerInfo.borderColor} hover:shadow-md transition-all`}>
      {/* 时间戳、说话人和语言标签 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded">
            {transcript.startTime}
          </span>
          {/* 说话人标签 */}
          {transcript.speaker && (
            <span className={`text-xs px-2 py-1 ${speakerInfo.bgColor} ${speakerInfo.textColor} rounded-full font-medium flex items-center gap-1`}>
              <span>{speakerInfo.icon}</span>
              <span>{speakerInfo.label}</span>
              {confidencePercent > 0 && (
                <span className="text-[10px] opacity-70">
                  ({confidencePercent}%)
                </span>
              )}
            </span>
          )}
        </div>
        <span className="text-xs px-2 py-1 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-full font-medium">
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

