"""
WebSocket API - 实时音频转录
"""
import json
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.transcription_service import transcription_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """连接 WebSocket"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        """断开连接"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_message(self, session_id: str, message: dict):
        """发送消息给客户端"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")


manager = ConnectionManager()


@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket, session_id: str = "default"):
    """
    WebSocket 端点 - 实时音频转录
    
    客户端消息格式：
    {
        "type": "audio_chunk",
        "data": "base64_encoded_audio",
        "timestamp": 1234567890
    }
    
    服务端消息格式：
    {
        "type": "transcript",
        "data": {
            "id": "block_123",
            "timestamp": 1234567890,
            "originalText": "转录文本",
            "translatedText": "Translated text",
            "detectedLanguage": "zh",
            "startTime": "00:05:23",
            "isFinal": true
        }
    }
    """
    await manager.connect(websocket, session_id)

    # 启动 Gemini Live API 会话
    try:
        await transcription_service.start_live_session()
    except Exception as e:
        logger.error(f"Failed to start live session: {e}")
        await manager.send_message(session_id, {
            "type": "error",
            "message": f"无法启动转录服务: {str(e)}"
        })
        manager.disconnect(session_id)
        return

    # 心跳任务
    async def heartbeat():
        """每 30 秒发送心跳"""
        try:
            while True:
                await asyncio.sleep(30)
                await manager.send_message(session_id, {
                    "type": "ping",
                    "timestamp": asyncio.get_event_loop().time()
                })
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")

    # 启动心跳任务
    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "audio_chunk":
                # 处理音频块
                audio_data = message.get("data")  # Base64 编码的音频数据
                timestamp = message.get("timestamp")

                try:
                    # 调用转录服务，传递 session_id 和 manager 用于后台翻译推送
                    transcript_data = await transcription_service.transcribe_audio(
                        audio_data, 
                        session_id=session_id, 
                        ws_manager=manager
                    )

                    # 只有在有转录文本时才发送
                    if transcript_data.get("originalText"):
                        await manager.send_message(session_id, {
                            "type": "transcript",
                            "data": transcript_data
                        })

                except Exception as e:
                    logger.error(f"Transcription error: {e}")
                    await manager.send_message(session_id, {
                        "type": "error",
                        "message": f"转录失败: {str(e)}"
                    })

            elif message_type == "pong":
                # 心跳响应
                logger.debug(f"Received pong from {session_id}")
            
            elif message_type == "stop":
                # 停止录音，关闭 Live API 会话
                logger.info("Received stop signal, closing live session...")
                await transcription_service.stop_live_session()
                await manager.send_message(session_id, {"type": "stopped"})
                break

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 停止 Live API 会话
        await transcription_service.stop_live_session()
        
        # 取消心跳任务
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

        # 断开连接
        manager.disconnect(session_id)

