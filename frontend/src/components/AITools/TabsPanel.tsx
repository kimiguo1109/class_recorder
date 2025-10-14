/**
 * AI 工具标签页面板
 */
import { useState } from 'react';

type TabType = 'chat' | 'notes' | 'flashcard' | 'quiz' | 'mindmap';

export const TabsPanel = () => {
  const [activeTab, setActiveTab] = useState<TabType>('notes');

  const tabs = [
    { id: 'chat' as TabType, label: '💬 Chat', icon: '💬' },
    { id: 'notes' as TabType, label: '📝 Lecture Notes', icon: '📝' },
    { id: 'flashcard' as TabType, label: '🎴 Flashcard', icon: '🎴' },
    { id: 'quiz' as TabType, label: '❓ Quiz', icon: '❓' },
    { id: 'mindmap' as TabType, label: '🗺️ Mind Map', icon: '🗺️' }
  ];

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 标签页导航 */}
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

      {/* 标签页内容 */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'chat' && <ChatTab />}
        {activeTab === 'notes' && <NotesTab />}
        {activeTab === 'flashcard' && <FlashcardTab />}
        {activeTab === 'quiz' && <QuizTab />}
        {activeTab === 'mindmap' && <MindMapTab />}
      </div>
    </div>
  );
};

// Chat 标签页
const ChatTab = () => (
  <div className="space-y-4">
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <p className="text-sm text-blue-800">
        💡 <strong>Learn with Ask SAI</strong> - Hit record and I'll capture every word. 
        While I transcribe, jot down your own notes. After class, ask me anything from 
        the transcript or your notes — and turn them into clear study notes and flashcards for review.
      </p>
    </div>
    <div className="flex-1 flex items-center justify-center text-gray-400">
      <p className="text-sm">聊天功能即将上线...</p>
    </div>
  </div>
);

// Lecture Notes 标签页
const NotesTab = () => (
  <div className="space-y-4">
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <p className="text-sm text-yellow-800">
        📝 <strong>提示：</strong>在这里添加你的课堂笔记，支持 Markdown 格式
      </p>
    </div>
    <textarea
      placeholder="开始输入笔记..."
      className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
    />
  </div>
);

// Flashcard 标签页
const FlashcardTab = () => (
  <div className="flex flex-col items-center justify-center h-full text-gray-400">
    <div className="text-6xl mb-4">🎴</div>
    <p className="text-lg">暂无闪卡</p>
    <p className="text-sm mt-2">停止录音后点击"生成闪卡"按钮</p>
  </div>
);

// Quiz 标签页
const QuizTab = () => (
  <div className="flex flex-col items-center justify-center h-full text-gray-400">
    <div className="text-6xl mb-4">❓</div>
    <p className="text-lg">暂无测验题</p>
    <p className="text-sm mt-2">停止录音后点击"生成测验"按钮</p>
  </div>
);

// Mind Map 标签页
const MindMapTab = () => (
  <div className="flex flex-col items-center justify-center h-full text-gray-400">
    <div className="text-6xl mb-4">🗺️</div>
    <p className="text-lg">暂无思维导图</p>
    <p className="text-sm mt-2">停止录音后点击"生成思维导图"按钮</p>
  </div>
);

