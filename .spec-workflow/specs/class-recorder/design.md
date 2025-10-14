# Design: 课堂录音转录与 AI 学习助手

## 1. 系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  Audio Capture │→ │  WebSocket   │→ │  UI Components     │  │
│  │  (MediaRecorder)│  │  Client      │  │  - Transcript View │  │
│  └────────────────┘  └──────────────┘  │  - Notes Editor    │  │
│                                         │  - AI Tools Tabs   │  │
│                                         └────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket + HTTP
┌──────────────────────────┴──────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌──────────────┐  ┌────────────────┐  ┌───────────────────┐  │
│  │  WebSocket   │→ │  Audio Buffer  │→ │  Gemini Live API  │  │
│  │  Handler     │  │  & Processor   │  │  - Transcription  │  │
│  └──────────────┘  └────────────────┘  │  - Translation    │  │
│                                         └───────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AI Content Generation APIs                   │  │
│  │  - /api/generate/flashcards                              │  │
│  │  - /api/generate/quiz                                    │  │
│  │  - /api/generate/mindmap                                 │  │
│  │  - /api/chat                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

#### 后端
- **框架：** FastAPI 0.110+
- **WebSocket：** fastapi.WebSocket
- **异步支持：** asyncio, aiohttp
- **AI API：** google-generativeai (Gemini SDK)
- **音频处理：** 无需额外库（接收 PCM 格式）
- **环境管理：** python-dotenv

#### 前端
- **框架：** React 18.2+
- **类型支持：** TypeScript 5.0+
- **UI 框架：** TailwindCSS 3.4+
- **富文本编辑器：** Tiptap 或 Quill
- **音频可视化：** Web Audio API + Canvas
- **状态管理：** React Context + Hooks
- **HTTP 客户端：** fetch API
- **WebSocket 客户端：** 原生 WebSocket API

## 2. 数据模型

### 2.1 转录文本块（TranscriptBlock）

```typescript
interface TranscriptBlock {
  id: string;                    // 唯一标识符
  timestamp: number;              // Unix 时间戳（毫秒）
  originalText: string;           // 原始语言文本
  translatedText: string;         // 英文翻译
  detectedLanguage: string;       // 检测到的语言代码（如 'zh', 'ja', 'es'）
  startTime: string;              // 格式化时间 "HH:MM:SS"
  isFinal: boolean;               // 是否为最终转录结果
}
```

### 2.2 会话状态（SessionState）

```typescript
interface SessionState {
  sessionId: string;              // 会话 ID
  isRecording: boolean;           // 是否正在录音
  startTime: number | null;       // 录音开始时间
  duration: number;               // 录音时长（秒）
  transcriptBlocks: TranscriptBlock[];  // 转录块列表
  connectionStatus: 'connected' | 'connecting' | 'disconnected';
}
```

### 2.3 AI 生成内容

```typescript
// 闪卡
interface Flashcard {
  id: string;
  front: string;      // 问题
  back: string;       // 答案
}

// 测验题
interface QuizQuestion {
  id: string;
  question: string;
  options: string[];  // 4 个选项
  correctAnswer: number;  // 正确答案索引 (0-3)
  explanation: string;
}

// 思维导图节点
interface MindMapNode {
  id: string;
  label: string;
  children: MindMapNode[];
  level: number;
}
```

## 3. API 设计

### 3.1 WebSocket 端点

#### `/ws/transcribe`

**连接参数：**
- `session_id`: 会话 ID（客户端生成）

**客户端 → 服务器消息：**

```json
{
  "type": "audio_chunk",
  "data": "base64_encoded_pcm_audio",
  "timestamp": 1234567890
}
```

**服务器 → 客户端消息：**

```json
{
  "type": "transcript",
  "data": {
    "id": "block_123",
    "timestamp": 1234567890,
    "originalText": "今天我们讲解机器学习",
    "translatedText": "Today we will explain machine learning",
    "detectedLanguage": "zh",
    "startTime": "00:05:23",
    "isFinal": true
  }
}
```

**错误消息：**

```json
{
  "type": "error",
  "message": "API rate limit exceeded"
}
```

### 3.2 HTTP REST API

#### POST `/api/generate/flashcards`

**请求体：**
```json
{
  "transcript": "完整的转录文本（原文或翻译）",
  "count": 15
}
```

**响应：**
```json
{
  "flashcards": [
    {
      "id": "fc_1",
      "front": "What is machine learning?",
      "back": "A subset of AI that enables systems to learn from data..."
    }
  ]
}
```

#### POST `/api/generate/quiz`

**请求体：**
```json
{
  "transcript": "完整的转录文本",
  "questionCount": 10
}
```

**响应：**
```json
{
  "questions": [
    {
      "id": "q_1",
      "question": "What is supervised learning?",
      "options": ["A", "B", "C", "D"],
      "correctAnswer": 0,
      "explanation": "..."
    }
  ]
}
```

#### POST `/api/generate/mindmap`

**请求体：**
```json
{
  "transcript": "完整的转录文本"
}
```

**响应：**
```json
{
  "mindmap": {
    "id": "root",
    "label": "Machine Learning Basics",
    "children": [
      {
        "id": "node_1",
        "label": "Supervised Learning",
        "children": [...]
      }
    ]
  }
}
```

#### POST `/api/chat`

**请求体：**
```json
{
  "message": "用户问题",
  "transcript": "课程转录文本",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**响应：**
```json
{
  "response": "AI 回答内容"
}
```

## 4. 核心功能设计

### 4.1 实时音频转录与翻译

#### 4.1.1 音频捕获（前端）

```typescript
class AudioCapture {
  private mediaStream: MediaStream | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioContext: AudioContext;
  private websocket: WebSocket;
  
  async startRecording() {
    // 1. 请求麦克风权限
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true
      }
    });
    
    // 2. 创建 AudioContext 进行音频处理
    this.audioContext = new AudioContext({ sampleRate: 16000 });
    const source = this.audioContext.createMediaStreamSource(this.mediaStream);
    
    // 3. 使用 ScriptProcessorNode 或 AudioWorklet 获取 PCM 数据
    const processor = this.audioContext.createScriptProcessor(4096, 1, 1);
    source.connect(processor);
    processor.connect(this.audioContext.destination);
    
    processor.onaudioprocess = (e) => {
      const pcmData = e.inputBuffer.getChannelData(0);
      this.sendAudioChunk(pcmData);
    };
  }
  
  private sendAudioChunk(pcmData: Float32Array) {
    // 转换为 Int16Array (16-bit PCM)
    const int16Data = new Int16Array(pcmData.length);
    for (let i = 0; i < pcmData.length; i++) {
      int16Data[i] = Math.max(-32768, Math.min(32767, pcmData[i] * 32768));
    }
    
    // Base64 编码并通过 WebSocket 发送
    const base64 = btoa(String.fromCharCode(...new Uint8Array(int16Data.buffer)));
    this.websocket.send(JSON.stringify({
      type: 'audio_chunk',
      data: base64,
      timestamp: Date.now()
    }));
  }
}
```

#### 4.1.2 后端 WebSocket 处理

```python
# backend/services/transcription_service.py
import asyncio
import base64
from google import genai
from google.genai import types

class TranscriptionService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-live-2.5-flash-preview"
        
    async def start_session(self, websocket):
        """启动转录会话"""
        config = {
            "response_modalities": ["TEXT"],
            "input_audio_transcription": {},  # 启用输入音频转录
        }
        
        async with self.client.aio.live.connect(
            model=self.model, 
            config=config
        ) as session:
            # 并发处理：接收客户端音频 + 接收 Gemini 响应
            await asyncio.gather(
                self._receive_from_client(websocket, session),
                self._send_to_client(websocket, session)
            )
    
    async def _receive_from_client(self, websocket, gemini_session):
        """接收客户端音频并转发给 Gemini"""
        async for message in websocket.iter_text():
            data = json.loads(message)
            if data['type'] == 'audio_chunk':
                # 解码 Base64 音频
                audio_bytes = base64.b64decode(data['data'])
                
                # 发送到 Gemini Live API
                await gemini_session.send_realtime_input(
                    audio=types.Blob(
                        data=audio_bytes,
                        mime_type="audio/pcm;rate=16000"
                    )
                )
    
    async def _send_to_client(self, websocket, gemini_session):
        """接收 Gemini 转录结果并发送给客户端"""
        async for response in gemini_session.receive():
            if response.server_content.input_transcription:
                transcript = response.server_content.input_transcription.text
                detected_lang = self._detect_language(transcript)
                
                # 如果不是英文，进行翻译
                translated = transcript
                if detected_lang != 'en':
                    translated = await self._translate_to_english(transcript)
                
                # 发送给客户端
                await websocket.send_json({
                    "type": "transcript",
                    "data": {
                        "id": str(uuid.uuid4()),
                        "timestamp": int(time.time() * 1000),
                        "originalText": transcript,
                        "translatedText": translated,
                        "detectedLanguage": detected_lang,
                        "startTime": self._format_time(time.time()),
                        "isFinal": True
                    }
                })
    
    async def _translate_to_english(self, text: str) -> str:
        """使用 Gemini API 翻译文本为英文"""
        response = await self.client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Translate the following text to English. Only output the translation, no explanations:\n\n{text}"
        )
        return response.text.strip()
    
    def _detect_language(self, text: str) -> str:
        """简单语言检测（可用 langdetect 库优化）"""
        # 简化实现：检测字符范围
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return 'zh'
        elif any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
            return 'ja'
        elif any('\uac00' <= char <= '\ud7af' for char in text):
            return 'ko'
        else:
            return 'en'
```

### 4.2 AI 内容生成

#### 4.2.1 闪卡生成 Prompt

```python
FLASHCARD_PROMPT = """
Based on the following lecture transcript, generate {count} flashcards for studying.

Transcript:
{transcript}

Requirements:
- Extract key concepts, definitions, and important facts
- Each flashcard should have a clear question (front) and a concise answer (back)
- Cover diverse topics from the transcript
- Format as JSON array

Output format:
[
  {{"front": "Question", "back": "Answer"}},
  ...
]
"""
```

#### 4.2.2 测验生成 Prompt

```python
QUIZ_PROMPT = """
Based on the following lecture transcript, generate {count} multiple-choice quiz questions.

Transcript:
{transcript}

Requirements:
- Create challenging questions that test understanding
- Each question should have 4 options (A, B, C, D)
- Include explanations for correct answers
- Format as JSON array

Output format:
[
  {{
    "question": "Question text",
    "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
    "correctAnswer": 0,
    "explanation": "Why this answer is correct"
  }},
  ...
]
"""
```

#### 4.2.3 思维导图生成 Prompt

```python
MINDMAP_PROMPT = """
Based on the following lecture transcript, create a hierarchical mind map structure.

Transcript:
{transcript}

Requirements:
- Identify the main topic (root node)
- Extract 3-5 major subtopics (level 1)
- For each subtopic, identify 2-4 key points (level 2)
- Format as nested JSON structure

Output format:
{{
  "label": "Main Topic",
  "children": [
    {{
      "label": "Subtopic 1",
      "children": [
        {{"label": "Key point 1", "children": []}},
        {{"label": "Key point 2", "children": []}}
      ]
    }},
    ...
  ]
}}
"""
```

### 4.3 前端 UI 组件结构

```
src/
├── components/
│   ├── Layout/
│   │   ├── MainLayout.tsx          # 双栏布局容器
│   │   └── BottomControls.tsx      # 底部控制条
│   ├── Transcript/
│   │   ├── TranscriptPanel.tsx     # 左侧转录面板
│   │   ├── TranscriptBlock.tsx     # 单个转录块
│   │   ├── LanguageToggle.tsx      # 原文/翻译切换
│   │   └── Waveform.tsx            # 音频波形可视化
│   ├── Notes/
│   │   ├── NotesEditor.tsx         # 富文本编辑器
│   │   └── NotesToolbar.tsx        # 编辑器工具栏
│   ├── AITools/
│   │   ├── FlashcardsView.tsx      # 闪卡展示
│   │   ├── QuizView.tsx            # 测验界面
│   │   ├── MindMapView.tsx         # 思维导图
│   │   └── ChatView.tsx            # 聊天机器人
│   └── Common/
│       ├── Button.tsx
│       ├── Tabs.tsx
│       └── LoadingSpinner.tsx
├── hooks/
│   ├── useWebSocket.ts             # WebSocket 连接管理
│   ├── useAudioRecorder.ts         # 音频录制逻辑
│   └── useTranscript.ts            # 转录状态管理
├── services/
│   ├── websocket.service.ts        # WebSocket 服务
│   └── api.service.ts              # HTTP API 调用
├── context/
│   └── SessionContext.tsx          # 全局会话状态
└── utils/
    ├── audio.utils.ts              # 音频处理工具
    └── format.utils.ts             # 格式化工具
```

## 5. 状态管理

### 5.1 Session Context

```typescript
interface SessionContextType {
  // 状态
  sessionId: string;
  isRecording: boolean;
  transcriptBlocks: TranscriptBlock[];
  connectionStatus: ConnectionStatus;
  
  // 操作
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  clearTranscript: () => void;
  downloadTranscript: () => void;
  downloadAudio: () => void;
}
```

## 6. 错误处理

### 6.1 WebSocket 错误

```typescript
class WebSocketService {
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  handleError(error: Event) {
    console.error('WebSocket error:', error);
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnect();
        this.reconnectAttempts++;
      }, 2000 * this.reconnectAttempts);
    } else {
      // 通知用户连接失败
      this.emit('fatal_error', 'Failed to connect after multiple attempts');
    }
  }
}
```

### 6.2 API 错误

```python
# backend/main.py
from fastapi import HTTPException

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if isinstance(exc, RateLimitError):
        return JSONResponse(
            status_code=429,
            content={"error": "API rate limit exceeded. Please try again later."}
        )
    elif isinstance(exc, AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid API key"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
```

## 7. 性能优化

### 7.1 前端优化

1. **虚拟化列表：** 使用 `react-window` 渲染大量转录块
2. **音频缓冲：** 客户端缓存最近 10 秒音频，防止网络抖动丢失数据
3. **防抖与节流：** 用户输入事件使用 debounce/throttle
4. **懒加载：** AI 工具标签页按需加载组件

### 7.2 后端优化

1. **异步处理：** 所有 I/O 操作使用 `asyncio`
2. **连接池：** 复用 Gemini API 连接
3. **超时控制：** 所有 API 调用设置超时（30 秒）
4. **流式响应：** AI 生成内容使用流式输出

## 8. 安全性设计

1. **API Key 保护：** 使用环境变量，不在前端暴露
2. **CORS 配置：** 仅允许指定域名访问
3. **速率限制：** 限制每个 IP 的请求频率
4. **输入验证：** 所有用户输入进行验证和清理
5. **HTTPS：** 生产环境强制使用 HTTPS

## 9. 部署架构

### 9.1 开发环境

```
Backend: http://localhost:8000
Frontend: http://localhost:5173 (Vite dev server)
WebSocket: ws://localhost:8000/ws/transcribe
```

### 9.2 生产环境（可选）

```
Backend: Deployed on Railway/Render/Fly.io
Frontend: Deployed on Vercel/Netlify
Database: Not required for MVP
```

## 10. 测试策略

### 10.1 单元测试
- 音频处理函数
- API endpoint 逻辑
- Prompt 生成函数

### 10.2 集成测试
- WebSocket 连接流程
- 完整转录和翻译流程
- AI 内容生成 API

### 10.3 端到端测试
- 45 分钟长时程录音测试
- 网络断线重连测试
- 多语言转录测试

## 11. 监控与日志

```python
# 日志配置
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 记录关键事件
logger.info(f"WebSocket connected: {session_id}")
logger.error(f"Transcription failed: {error}")
logger.warning(f"API rate limit approaching: {usage}")
```

## 12. 技术决策记录

| 决策 | 原因 |
|------|------|
| 使用 Gemini Live API | 支持实时音频转录和多语言翻译 |
| FastAPI + WebSocket | 高性能异步支持，简洁的 API 设计 |
| React + TypeScript | 类型安全，丰富的生态系统 |
| TailwindCSS | 快速 UI 开发，灵活的样式系统 |
| 不使用数据库 | MVP 阶段简化架构，数据保存在客户端 |
| 客户端音频处理 | 减轻服务器负担，实时性更好 |

