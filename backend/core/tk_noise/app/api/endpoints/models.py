# -*- coding: utf-8 -*-
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ModelInfo(BaseModel):
    name: str
    label: str
    description: str

class ModelsResponse(BaseModel):
    models: List[ModelInfo]

@router.get("/models")
async def get_models():
    """
    获取可用的降噪模型列表
    兼容前端API格式，参考Real-ESRGAN的模型接口
    """
    return {
        "models": [
            {
                "name": "tk_cbm3d",
                "description": "基于改进BM3D的唐卡图像降噪算法",
                "version": "1.0.0"
            }
        ],
        "current": "tk_cbm3d",
        "algorithm_info": {
            "name": "TK-CBM3D",
            "description": "基于改进BM3D的唐卡图像降噪算法",
            "version": "1.0.0",
            "supported_formats": ["jpg", "jpeg", "png", "bmp", "tiff"],
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "max_resolution": 4096,
            "parameters": {
                "strength": {
                    "type": "integer",
                    "min": 1,
                    "max": 100,
                    "default": 50,
                    "description": "降噪强度，值越大降噪效果越强"
                }
            }
        }
    }

# 保持向后兼容的端点
@router.get("/models/denoise", response_model=ModelsResponse)
async def get_denoise_models():
    """向后兼容的降噪模型列表端点"""
    return {
        "models": [
            {
                "name": "tk_cbm3d",
                "label": "TK-CBM3D",
                "description": "基于改进BM3D的唐卡图像降噪算法"
            }
        ]
    }
