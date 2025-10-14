/**
 * 主布局组件 - 双栏布局
 */
import type { ReactNode } from 'react';

interface MainLayoutProps {
  leftPanel: ReactNode;
  rightPanel: ReactNode;
  bottomControls: ReactNode;
}

export const MainLayout = ({ leftPanel, rightPanel, bottomControls }: MainLayoutProps) => {
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 顶部标题栏 */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-800">
          Class Recorder - 课堂录音转录助手
        </h1>
      </header>

      {/* 主内容区 - 双栏布局 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧面板 - 60% */}
        <div className="w-3/5 border-r border-gray-200 bg-white overflow-hidden">
          {leftPanel}
        </div>

        {/* 右侧面板 - 40% */}
        <div className="w-2/5 bg-white overflow-hidden">
          {rightPanel}
        </div>
      </div>

      {/* 底部控制条 */}
      <div className="bg-white border-t border-gray-200">
        {bottomControls}
      </div>
    </div>
  );
};

