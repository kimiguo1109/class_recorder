/**
 * AI Tools Tabs Panel - 包含笔记、聊天、闪卡等功能
 */
import { useState } from 'react';

type TabType = 'notes' | 'chat' | 'flashcard' | 'quiz' | 'mindmap';

interface TabsPanelProps {
  notes: string;
  onNotesChange: (notes: string) => void;
}

export const TabsPanel = ({ notes, onNotesChange }: TabsPanelProps) => {
  const [activeTab, setActiveTab] = useState<TabType>('notes');

  const tabs = [
    { id: 'notes' as TabType, label: '📝 Lecture Notes', icon: '📝' },
    { id: 'chat' as TabType, label: '💬 Chat', icon: '💬' },
    { id: 'flashcard' as TabType, label: '🎴 Flashcard', icon: '🎴' },
    { id: 'quiz' as TabType, label: '❓ Quiz', icon: '❓' },
    { id: 'mindmap' as TabType, label: '🗺️ Mind Map', icon: '🗺️' }
  ];

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Tabs Header */}
      <div className="border-b border-gray-200 px-4 bg-gradient-to-r from-purple-50 to-pink-50">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-white text-blue-600 shadow-sm border-t-2 border-blue-500'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'notes' && (
          <div className="h-full flex flex-col">
            <div className="mb-3">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">📝 课堂笔记</h3>
              <p className="text-xs text-gray-500">记录重点内容、想法和总结</p>
            </div>
            <textarea
              value={notes}
              onChange={(e) => onNotesChange(e.target.value)}
              placeholder="在这里记录课堂笔记...&#10;&#10;可以记录：&#10;• 重要概念&#10;• 课堂总结&#10;• 疑问和想法&#10;• 待复习内容"
              className="flex-1 w-full p-4 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:outline-none resize-none font-sans text-sm leading-relaxed"
              style={{ minHeight: '400px' }}
            />
            <div className="mt-3 text-xs text-gray-400">
              {notes.length} 字符
            </div>
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="text-gray-600">
            <div className="flex flex-col items-center justify-center h-64">
              <div className="text-6xl mb-4">💬</div>
              <p className="text-lg font-semibold text-gray-700">Chat 功能</p>
              <p className="text-sm text-gray-400 mt-2">Phase 5 - 即将上线</p>
            </div>
          </div>
        )}

        {activeTab === 'flashcard' && (
          <div className="text-gray-600">
            <div className="flex flex-col items-center justify-center h-64">
              <div className="text-6xl mb-4">🎴</div>
              <p className="text-lg font-semibold text-gray-700">闪卡生成</p>
              <p className="text-sm text-gray-400 mt-2">Phase 4 - 即将上线</p>
            </div>
          </div>
        )}

        {activeTab === 'quiz' && (
          <div className="text-gray-600">
            <div className="flex flex-col items-center justify-center h-64">
              <div className="text-6xl mb-4">❓</div>
              <p className="text-lg font-semibold text-gray-700">测验生成</p>
              <p className="text-sm text-gray-400 mt-2">Phase 4 - 即将上线</p>
            </div>
          </div>
        )}

        {activeTab === 'mindmap' && (
          <div className="text-gray-600">
            <div className="flex flex-col items-center justify-center h-64">
              <div className="text-6xl mb-4">🗺️</div>
              <p className="text-lg font-semibold text-gray-700">思维导图</p>
              <p className="text-sm text-gray-400 mt-2">Phase 4 - 即将上线</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
