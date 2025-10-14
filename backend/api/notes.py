"""
笔记 API - 保存和导出笔记
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter()


class TranscriptItem(BaseModel):
    id: str
    timestamp: int
    originalText: str
    translatedText: str
    detectedLanguage: str
    startTime: str


class NotesData(BaseModel):
    transcripts: List[TranscriptItem]
    notes: str = ""


@router.post("/api/export/markdown")
async def export_markdown(data: NotesData):
    """
    导出为 Markdown 格式
    """
    try:
        # 构建 Markdown 内容
        md_content = "# 课堂录音笔记\n\n"
        
        # 添加笔记内容
        if data.notes:
            md_content += "## 📝 我的笔记\n\n"
            md_content += data.notes + "\n\n"
        
        # 添加转录内容
        md_content += "## 🎤 转录记录\n\n"
        for item in data.transcripts:
            md_content += f"### {item.startTime}\n\n"
            md_content += f"**原文** ({item.detectedLanguage}):\n{item.originalText}\n\n"
            if item.translatedText:
                md_content += f"**English**:\n{item.translatedText}\n\n"
            md_content += "---\n\n"
        
        return {
            "content": md_content,
            "filename": "lecture_notes.md"
        }
        
    except Exception as e:
        logger.error(f"Export markdown failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/export/text")
async def export_text(data: NotesData):
    """
    导出为纯文本格式
    """
    try:
        # 构建文本内容
        text_content = "课堂录音笔记\n"
        text_content += "=" * 50 + "\n\n"
        
        # 添加笔记内容
        if data.notes:
            text_content += "我的笔记\n"
            text_content += "-" * 50 + "\n"
            text_content += data.notes + "\n\n"
        
        # 添加转录内容
        text_content += "转录记录\n"
        text_content += "-" * 50 + "\n\n"
        for item in data.transcripts:
            text_content += f"[{item.startTime}]\n"
            text_content += f"原文: {item.originalText}\n"
            if item.translatedText:
                text_content += f"翻译: {item.translatedText}\n"
            text_content += "\n"
        
        return {
            "content": text_content,
            "filename": "lecture_notes.txt"
        }
        
    except Exception as e:
        logger.error(f"Export text failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

