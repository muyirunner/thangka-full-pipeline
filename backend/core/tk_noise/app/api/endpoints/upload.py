# -*- coding: utf-8 -*-
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import shutil
import base64
from datetime import datetime
import uuid
from pathlib import Path
from app.utils.image_utils import get_image_info
from app.utils.task_manager import global_task_manager

router = APIRouter()

# 配置目录
UPLOAD_DIR = Path("denoise_uploads")
TEMP_DIR = Path("denoise_temp")

# 创建必要的目录
for dir_path in [UPLOAD_DIR, TEMP_DIR]:
    dir_path.mkdir(exist_ok=True)

class UploadResponse(BaseModel):
    task_id: str
    message: str
    status: str
    filename: str
    strength: int

@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    strength: int = 50
):
    """
    上传图片，兼容前端API格式
    参考Real-ESRGAN API的上传接口设计
    """

    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        # 如果content_type为空，通过文件扩展名验证
        if file.filename:
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(status_code=400, detail="只支持图片文件")
        else:
            raise HTTPException(status_code=400, detail="只支持图片文件")

    # 验证降噪强度
    if not 1 <= strength <= 100:
        raise HTTPException(status_code=400, detail="降噪强度必须在1-100之间")

    try:
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())

        # 保存上传的文件
        file_extension = Path(file.filename).suffix
        temp_filename = f"{task_id}{file_extension}"
        temp_path = TEMP_DIR / temp_filename

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 验证图像信息
        try:
            width, height = get_image_info(str(temp_path))
            file_size = os.path.getsize(temp_path)
        except Exception as e:
            # 清理无效文件
            if temp_path.exists():
                temp_path.unlink()
            raise HTTPException(status_code=400, detail=f"无效的图像文件: {str(e)}")

        # 创建任务（但不开始处理）
        global_task_manager.create_task(task_id, file.filename, strength)
        # 设置任务状态为已上传，等待处理
        global_task_manager.update_task(task_id, status="uploaded", message="文件已上传，等待处理指令")

        return {
            "task_id": task_id,
            "message": "文件上传成功，等待处理指令",
            "status": "uploaded",
            "filename": file.filename,
            "strength": strength
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/preview/{filename}")
async def preview_image(filename: str):
    """
    预览上传的图像
    返回base64编码的图像数据
    """
    try:
        # 查找文件在临时目录中
        temp_files = list(TEMP_DIR.glob(f"*{filename}*"))
        if not temp_files:
            # 如果临时目录没有，查找结果目录
            result_files = list(Path("denoise_results").glob(f"*{filename}*"))
            if not result_files:
                raise HTTPException(status_code=404, detail="图像文件不存在")
            file_path = result_files[0]
        else:
            file_path = temp_files[0]

        # 读取图像文件并转换为base64
        with open(file_path, "rb") as image_file:
            image_data = image_file.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')

        # 获取文件信息
        file_size = os.path.getsize(file_path)

        return {
            "filename": filename,
            "base64": f"data:image/jpeg;base64,{base64_data}",
            "file_size": file_size,
            "message": "图像预览成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
