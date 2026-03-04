# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from app.models.tk_cbm3d import TK_CBM3D
import cv2

router = APIRouter()

# 配置目录
TEMP_DIR = Path("denoise_temp")
RESULT_DIR = Path("denoise_results")

# 创建必要的目录
for dir_path in [TEMP_DIR, RESULT_DIR]:
    dir_path.mkdir(exist_ok=True)

# 任务状态存储
task_status = {}



# 使用共享的任务管理器
from app.utils.task_manager import global_task_manager as task_manager

async def process_denoise_task(task_id: str, input_path: str, strength: int):
    """异步处理降噪任务"""
    try:
        # 更新任务状态
        task_manager.update_task(task_id, status="processing", progress=10, message="开始处理图片")

        # 验证输入文件
        if not os.path.exists(input_path):
            raise Exception("输入文件不存在")

        input_img = cv2.imread(input_path)
        if input_img is None:
            raise Exception("无法读取图像文件")

        if len(input_img.shape) != 3 or input_img.shape[2] != 3:
            raise Exception("仅支持3通道RGB/BGR图像")

        task_manager.update_task(task_id, progress=20, message="图像验证通过")

        # 生成输出文件名
        input_file = Path(input_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{input_file.stem}_denoised_{timestamp}{input_file.suffix}"
        output_path = RESULT_DIR / output_filename

        task_manager.update_task(task_id, progress=30, message="准备降噪算法")

        # 处理图片
        denoiser = TK_CBM3D()
        result_path = denoiser.denoise(
            input_path,
            str(output_path),
            strength=strength
        )

        task_manager.update_task(task_id, progress=90, message="降噪处理完成")

        # 验证输出文件
        if not os.path.exists(result_path):
            raise Exception("降噪处理失败，未生成输出文件")

        # 构建结果URL
        result_filename = Path(result_path).name
        result_url = f"/results/{result_filename}"

        task_manager.update_task(
            task_id,
            status="completed",
            progress=100,
            message="处理完成",
            result_url=result_url
        )

    except Exception as e:
        error_msg = str(e)
        task_manager.update_task(
            task_id,
            status="failed",
            progress=0,
            message="处理失败",
            error=error_msg
        )

    finally:
        # 清理临时文件
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except:
            pass

@router.post("/process/{task_id}")
async def start_processing(
    task_id: str,
    background_tasks: BackgroundTasks
):
    """开始处理已上传的图片"""

    # 检查任务是否存在
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查任务状态
    if task["status"] not in ["uploaded", "failed"]:
        raise HTTPException(status_code=400, detail=f"任务状态不允许处理: {task['status']}")

    try:
        # 构建文件路径
        temp_filename = f"{task_id}{Path(task['filename']).suffix}"
        temp_path = TEMP_DIR / temp_filename

        # 检查文件是否存在
        if not temp_path.exists():
            raise HTTPException(status_code=404, detail="上传的文件不存在")

        # 更新任务状态为处理中
        task_manager.update_task(task_id, status="processing", message="开始处理图片")

        # 添加后台处理任务
        background_tasks.add_task(process_denoise_task, task_id, str(temp_path), task["strength"])

        return {
            "task_id": task_id,
            "message": "开始处理图片",
            "status": "processing"
        }

    except HTTPException:
        raise
    except Exception as e:
        task_manager.update_task(task_id, status="failed", message=f"开始处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"开始处理失败: {str(e)}")

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task

@router.get("/download/{task_id}")
async def download_result(task_id: str):
    """下载处理结果"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务未完成")

    if not task.get("result_url"):
        raise HTTPException(status_code=404, detail="结果文件不存在")

    result_path = RESULT_DIR / Path(task["result_url"]).name
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="结果文件不存在")

    return FileResponse(
        path=str(result_path),
        filename=f"denoised_{task['filename']}",
        media_type='application/octet-stream'
    )
