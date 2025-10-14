# Class Recorder - 课堂录音转录与 AI 学习助手

实时课堂录音转录系统，支持多语言自动翻译成英文，并生成 AI 驱动的学习材料。

## ✨ 功能特性

- 🎙️ **实时音频转录**：使用 Gemini Live API 进行实时语音转文字
- 🌍 **多语言支持**：自动检测语言并翻译成英文（支持中文、日语、韩语、西班牙语等）
- 📝 **富文本笔记**：集成富文本编辑器，支持自定义笔记
- 🤖 **AI 学习工具**：
  - 自动生成闪卡
  - 生成测验题
  - 创建思维导图
  - 智能问答聊天
- 💾 **保存与下载**：下载录音文件和转录文本
- 📊 **实时音频波形**：可视化音频输入

## 🏗️ 技术栈

### 后端
- **Python 3.11+**
- **FastAPI**: Web 框架
- **WebSocket**: 实时通信
- **Google Gemini API**: AI 模型（转录、翻译、内容生成）
- **Uvicorn**: ASGI 服务器

### 前端
- **React 18+**
- **TypeScript**
- **TailwindCSS**: UI 样式
- **Web Audio API**: 音频处理
- **WebSocket API**: 实时通信

## 📋 前置要求

- Python 3.11 或更高版本
- Node.js 18+ 和 npm
- Google Gemini API Key（[获取地址](https://aistudio.google.com/apikey)）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/kimiguo1109/class_recorder.git
cd class_recorder
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加你的 GEMINI_API_KEY
```

**环境变量配置** (`.env`):
```env
# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# 服务器配置
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:5173

# 代理配置（如需使用代理）
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
USE_PROXY=true
```

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install
```

### 4. 启动应用

**启动后端**（新终端）:
```bash
cd backend
source venv/bin/activate
python main.py
```

后端将运行在 http://localhost:8000

**启动前端**（新终端）:
```bash
cd frontend
npm run dev
```

前端将运行在 http://localhost:5173

### 5. 访问应用

打开浏览器访问 http://localhost:5173，授权麦克风权限，即可开始使用。

## 📖 使用指南

1. **开始录音**：点击"开始录音"按钮，授权麦克风权限
2. **查看转录**：左侧面板实时显示转录文本和翻译
3. **切换语言**：使用"原文/英文翻译/双语对照"按钮切换显示模式
4. **编辑笔记**：右侧"Lecture Notes"标签页添加自定义笔记
5. **生成 AI 内容**：停止录音后，使用 AI 工具生成闪卡、测验等
6. **下载内容**：保存录音文件和转录文本到本地

## 🗂️ 项目结构

```
class_recorder_demo/
├── backend/
│   ├── main.py                 # FastAPI 主应用
│   ├── config.py               # 配置文件
│   ├── requirements.txt        # Python 依赖
│   ├── api/                    # API 路由
│   │   ├── websocket.py        # WebSocket 端点
│   │   ├── generate.py         # AI 生成 API
│   │   └── chat.py             # 聊天 API
│   └── services/               # 业务逻辑
│       └── transcription_service.py
├── frontend/
│   ├── src/
│   │   ├── components/         # React 组件
│   │   ├── hooks/              # 自定义 Hooks
│   │   ├── services/           # API 服务
│   │   └── types/              # TypeScript 类型
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 🔧 API 文档

启动后端后，访问 http://localhost:8000/docs 查看自动生成的 API 文档（Swagger UI）。

### 主要端点

- `GET /`: 健康检查
- `GET /health`: 服务状态
- `WS /ws/transcribe`: WebSocket 转录端点
- `POST /api/generate/flashcards`: 生成闪卡
- `POST /api/generate/quiz`: 生成测验
- `POST /api/generate/mindmap`: 生成思维导图
- `POST /api/chat`: AI 问答

## 🧪 开发

### 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

### 代码格式化

```bash
# 后端
cd backend
black .
flake8 .

# 前端
cd frontend
npm run lint
npm run format
```

## 📝 开发计划

- [x] Phase 1: 核心转录 MVP
- [x] Phase 2: 多语言翻译
- [x] Phase 3: 笔记功能
- [x] Phase 4: AI 学习工具
- [x] Phase 5: 聊天机器人
- [x] Phase 6: 测试与优化

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License

## 🙏 致谢

- [Google Gemini API](https://ai.google.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [TailwindCSS](https://tailwindcss.com/)

---

## ⚠️ 注意事项

### 1. 代理配置
如果你在中国大陆或需要使用代理访问 Google API：

```bash
# 在 .env 文件中配置代理
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
USE_PROXY=true
```

**测试 API 连接：**
```bash
cd backend
source venv/bin/activate
python -c "
import asyncio
from services.transcription_service import transcription_service

async def test():
    result = await transcription_service.call_gemini_api('Hello')
    print('✅ API 连接成功:', result)

asyncio.run(test())
"
```

### 2. API Key 配置
- 使用 AI Vertex API endpoint
- API Key 格式：`AQ.xxxxx`
- **请勿提交 `.env` 文件到公开仓库**（已在 `.gitignore` 中）

### 3. Gemini Live API
项目使用 **Gemini Live API** (`gemini-live-2.5-flash-preview`) 进行实时音频转录：
- 音频格式：16-bit PCM, 16kHz, mono
- 连接方式：通过 `google-generativeai` SDK 的异步连接
- 功能：实时语音转文字 + 多语言检测 + 自动翻译成英文

### 4. 已测试功能
- ✅ **Gemini Live API 真实音频转录**
- ✅ 语言检测（支持中文、日语、韩语、俄语、阿拉伯语等）
- ✅ 自动翻译成英文（中文 -> 英文测试通过）
- ✅ API 调用成功（带代理支持）
- ✅ 双栏 UI 布局（渐变、阴影、现代设计）
- ✅ WebSocket 实时通信
- ✅ 语言视图切换（原文/翻译/双语）
- ✅ 停止录音功能（自动关闭 Live API 会话）

### 5. 待实现功能
- 📝 笔记编辑器（富文本）
- 💾 保存和下载功能
- 🎴 闪卡生成
- ❓ 测验生成
- 🗺️ 思维导图生成

---

**注意**: 此项目使用 Google Gemini API，请确保遵守其使用条款和配额限制。

启动前端（新终端）：
cd frontend
npm run dev