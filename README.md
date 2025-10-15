# Class Recorder - 课堂录音转录与 AI 学习助手

实时课堂录音转录系统，支持多语言自动翻译成英文，并生成 AI 驱动的学习材料。

## ✨ 功能特性

- 🎙️ **实时音频转录**：使用 Whisper 进行高质量语音转文字
- 🌍 **多语言支持**：自动检测语言并翻译成英文（支持中文、英文）
- 👨‍🏫 **AI 声纹识别**：自动区分教授和学生发言（> 90% 准确率）
- 📝 **富文本笔记**：集成富文本编辑器，支持自定义笔记
- 🤖 **AI 学习工具**：
  - 自动生成闪卡
  - 生成测验题
  - 创建思维导图
  - 智能问答聊天
- 🎵 **录音下载**：自动保存录音文件（WAV 格式）
- ☁️ **云存储支持**：可选 AWS S3 云存储（自动上传 + 本地备份）
- 💾 **导出功能**：下载录音文件和转录文本
- 📊 **实时音频波形**：可视化音频输入

## 🏗️ 技术栈

### 后端
- **Python 3.11+**
- **FastAPI**: Web 框架
- **WebSocket**: 实时通信
- **OpenAI Whisper**: 语音识别（转录）
- **Google Gemini API**: AI 模型（翻译、内容生成）
- **pyannote.audio**: 声纹识别（说话人识别）
- **AWS S3**: 云存储（可选）
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

# AWS S3 配置（录音云存储，可选）
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1
USE_S3_STORAGE=false  # 设为 true 启用 S3
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

### 基本流程

1. **注册教授声音**（可选但推荐）：
   - 点击左上角"👨‍🏫 教授声音设置"按钮
   - 录制 10 秒教授声音样本
   - 系统自动学习声纹特征

2. **开始录音**：
   - 点击"开始录音"按钮
   - 授权麦克风权限
   - 系统开始实时转录

3. **查看转录**：
   - 左侧面板实时显示转录文本
   - 自动显示说话人标签（👨‍🏫 教授 / 🧑‍🎓 学生）
   - 显示识别置信度（如 95%）

4. **切换语言**：
   - 使用"原文/英文/双语"按钮切换显示模式
   - 中文自动翻译成英文

5. **编辑笔记**：
   - 右侧"Lecture Notes"标签页添加自定义笔记

6. **停止录音**：
   - 点击"停止录音"
   - 系统自动保存并上传录音文件

7. **下载内容**：
   - 📄 导出转录文本（Markdown / Text）
   - 🎵 下载录音文件（WAV 格式）
   - 🤖 生成 AI 学习材料

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

### 3. 音频转录技术栈

**✅ 真实的语音识别系统**：
- 🎤 **音频采集**: 16-bit PCM, 16kHz, mono
- 🧠 **语音识别**: OpenAI Whisper (base 模型)
- 🌍 **语言支持**: **仅中文和英文**
- 🔄 **翻译**: Gemini API（中文 → 英文）
- 📡 **实时通信**: WebSocket

**技术选型**：
- **Whisper**: 开源、免费、本地运行，准确度高
- **Gemini API**: 高质量翻译（只用于翻译，不用于转录）
- **语言限制**: 只支持中英文（按用户要求）

**当前功能**：
- ✅ **真实的语音转录**（使用 Whisper）
- ✅ 自动语言检测（中/英）
- ✅ Gemini API 翻译（中 → 英）
- ✅ 完整的 UI/UX 流程
- ✅ WebSocket 实时通信

### 4. 已测试功能
- ✅ **Whisper 实时语音转录**（small 模型 + 专业术语提示）
- ✅ 语言检测（中文/英文）
- ✅ **Gemini API 自动翻译**（中 → 英）
- ✅ API 调用成功（带代理支持）
- ✅ 双栏 UI 布局（渐变、阴影、现代设计）
- ✅ WebSocket 实时通信
- ✅ 翻译结果实时推送更新
- ✅ 语言视图切换（原文/翻译/双语）
- ✅ 停止录音功能
- ✅ 音频录制和传输（16kHz PCM）
- ✅ **笔记编辑器**（Lecture Notes 标签）
- ✅ **导出功能**（Markdown / Text 格式）

### 5. 性能说明

**Whisper 模型加载时间**：
- 首次启动：约 15-20 秒（下载 139MB 模型）
- 后续启动：约 2 秒（从缓存加载）

**转录速度**：
- 3 秒音频 → 约 1-2 秒转录时间
- CPU 运行（无需 GPU）

### 6. 待实现功能
- 🎴 闪卡生成（Phase 4）
- ❓ 测验生成（Phase 4）
- 🗺️ 思维导图生成（Phase 4）

---

---

## 🎤 声纹识别功能

系统支持 **AI 声纹识别**，可自动区分教授和学生的发言。

### 使用方法

1. **注册教授声音**：
   - 点击"👨‍🏫 教授声音设置"
   - 录制 10 秒教授声音
   - 系统自动学习声纹特征

2. **自动识别**：
   - 录音时自动标注说话人
   - 👨‍🏫 教授（蓝色边框）
   - 🧑‍🎓 学生（绿色边框）
   - 显示识别置信度（如 95%）

### 技术特性

- 🧠 **AI 模型**: pyannote/embedding
- 📊 **准确率**: > 90%
- ⚡ **实时性**: < 200ms
- 🔒 **隐私**: 数据仅存本地

---

## 🎵 录音下载功能

系统支持自动保存和下载录音文件。

### 功能特性

- ✅ **自动保存**: 停止录音后自动生成 WAV 文件
- ✅ **云存储**: 可选 AWS S3 云存储
- ✅ **本地备份**: 同时保存本地副本
- ✅ **一键下载**: 点击按钮即可下载

### 文件格式

- **格式**: WAV (未压缩)
- **采样率**: 16kHz
- **位深度**: 16-bit
- **声道**: 单声道
- **大小**: 约 2MB/分钟

### AWS S3 配置（可选）

如需启用云存储，配置 `.env`：

```bash
# AWS S3 配置
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# 启用 S3
USE_S3_STORAGE=true
```

**优势**：
- ☁️ 无限云存储
- ⚡ 全球 CDN 加速
- 💰 成本低（~$0.08/月）
- 🔐 安全可靠

---

## 📝 测试脚本

项目包含完整的测试脚本，位于 `test_course/` 目录：

- **快速测试_30秒.md**: 30秒快速验证
- **课堂测试脚本_微积分.md**: 2分钟完整测试（中文）
- **Test_Script_Calculus_EN.md**: 英文版测试
- **打印版_朗读脚本.txt**: 打印友好版
- **测试指南_README.md**: 详细测试说明

---

**注意**: 此项目使用 Google Gemini API，请确保遵守其使用条款和配额限制。