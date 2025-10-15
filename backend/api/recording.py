"""
录音文件 API - 上传和下载录音文件（支持本地存储和 S3）
"""
import os
import logging
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 录音文件存储目录（本地存储）
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "../recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# 初始化 S3 客户端（如果启用）
s3_client = None
if settings.USE_S3_STORAGE and settings.AWS_ACCESS_KEY_ID:
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        logger.info(f"✅ S3 client initialized (bucket: {settings.AWS_S3_BUCKET})")
    except Exception as e:
        logger.error(f"❌ Failed to initialize S3 client: {e}")
        s3_client = None


class UploadResponse(BaseModel):
    """上传响应"""
    success: bool
    message: str
    filename: str
    downloadUrl: str
    size: int


@router.post("/api/recording/upload", response_model=UploadResponse)
async def upload_recording(
    audio: UploadFile = File(...),
    sessionId: str = Form(...)
):
    """
    上传录音文件（支持本地存储和 S3）
    
    参数:
        audio: 音频文件（WAV格式）
        sessionId: 会话ID
    """
    try:
        logger.info(f"📤 Uploading recording for session: {sessionId}")
        
        # 生成文件名（带时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{sessionId}_{timestamp}.wav"
        
        # 读取文件内容
        contents = await audio.read()
        file_size = len(contents)
        
        download_url = ""
        
        # 如果启用 S3，上传到 S3
        if settings.USE_S3_STORAGE and s3_client:
            try:
                # 上传到 S3
                s3_client.put_object(
                    Bucket=settings.AWS_S3_BUCKET,
                    Key=f"recordings/{filename}",
                    Body=contents,
                    ContentType='audio/wav',
                    Metadata={
                        'session-id': sessionId,
                        'upload-time': timestamp
                    }
                )
                
                # 生成预签名 URL（有效期 7 天）
                download_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_S3_BUCKET,
                        'Key': f"recordings/{filename}"
                    },
                    ExpiresIn=7 * 24 * 3600  # 7 天
                )
                
                logger.info(f"✅ Recording uploaded to S3: {filename} ({file_size / 1024 / 1024:.2f} MB)")
                
                # 同时保存本地备份（可选）
                filepath = os.path.join(RECORDINGS_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(contents)
                logger.info(f"💾 Local backup saved: {filename}")
                
            except ClientError as e:
                logger.error(f"❌ S3 upload failed: {e}")
                # 回退到本地存储
                settings.USE_S3_STORAGE = False
        
        # 本地存储
        if not settings.USE_S3_STORAGE or not s3_client:
            filepath = os.path.join(RECORDINGS_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(contents)
            
            download_url = f"/api/recording/download/{filename}"
            logger.info(f"✅ Recording saved locally: {filename} ({file_size / 1024 / 1024:.2f} MB)")
        
        return UploadResponse(
            success=True,
            message="录音上传成功" + (" (S3)" if settings.USE_S3_STORAGE else " (本地)"),
            filename=filename,
            downloadUrl=download_url,
            size=file_size
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to upload recording: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/recording/download/{filename}")
async def download_recording(filename: str):
    """
    下载录音文件（优先本地，备选 S3）
    
    参数:
        filename: 文件名
    """
    try:
        # 优先检查本地文件
        filepath = os.path.join(RECORDINGS_DIR, filename)
        
        if os.path.exists(filepath):
            # 本地文件存在，直接返回
            logger.info(f"📥 Downloading recording from local: {filename}")
            return FileResponse(
                filepath,
                media_type="audio/wav",
                filename=filename
            )
        
        # 本地文件不存在，尝试从 S3 下载
        if settings.USE_S3_STORAGE and s3_client:
            try:
                # 检查 S3 上是否有文件
                s3_client.head_object(
                    Bucket=settings.AWS_S3_BUCKET,
                    Key=f"recordings/{filename}"
                )
                
                # 生成预签名 URL
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_S3_BUCKET,
                        'Key': f"recordings/{filename}"
                    },
                    ExpiresIn=3600  # 1 小时
                )
                logger.info(f"📥 Redirecting to S3: {filename}")
                return RedirectResponse(url=url)
                
            except ClientError as e:
                logger.error(f"❌ S3 download failed: {e}")
                # S3 也没有，返回 404
        
        # 本地和 S3 都没有
        raise HTTPException(status_code=404, detail="录音文件不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to download recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/recording/list")
async def list_recordings():
    """
    列出所有录音文件
    """
    try:
        files = []
        
        for filename in os.listdir(RECORDINGS_DIR):
            if filename.endswith('.wav'):
                filepath = os.path.join(RECORDINGS_DIR, filename)
                stat = os.stat(filepath)
                
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "downloadUrl": f"/api/recording/download/{filename}"
                })
        
        # 按创建时间倒序排列
        files.sort(key=lambda x: x['created'], reverse=True)
        
        logger.info(f"📋 Listed {len(files)} recordings")
        
        return {
            "success": True,
            "count": len(files),
            "files": files
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to list recordings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/recording/delete/{filename}")
async def delete_recording(filename: str):
    """
    删除录音文件
    
    参数:
        filename: 文件名
    """
    try:
        filepath = os.path.join(RECORDINGS_DIR, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="录音文件不存在")
        
        os.remove(filepath)
        logger.info(f"🗑️ Recording deleted: {filename}")
        
        return {
            "success": True,
            "message": "录音文件已删除"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to delete recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))

