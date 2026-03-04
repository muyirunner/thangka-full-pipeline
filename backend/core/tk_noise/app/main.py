# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.endpoints import upload, denoise, models

# 导入配置管理
import sys
sys.path.append('../..')
try:
    from config import config
    cors_origins = config.CORS_ALLOWED_ORIGINS
except:
    # 如果配置加载失败，使用默认值
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

# 创建必要的目录
RESULT_DIR = Path("denoise_results")
RESULT_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="唐卡图像降噪API",
    description="基于改进BM3D的唐卡图像去噪处理服务",
    version="1.0.0"
)

# 添加CORS中间件，允许前端跨域访问（使用配置管理）
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # 限制允许的方法
    allow_headers=["*"],
)

# 挂载静态文件服务，用于下载处理结果
app.mount("/results", StaticFiles(directory=str(RESULT_DIR)), name="results")

# 注册路由
app.include_router(upload.router, tags=["文件操作"])
app.include_router(denoise.router, tags=["图像处理"])
app.include_router(models.router, tags=["模型管理"])

@app.get("/")
async def root():
    return {
        "message": "唐卡图像降噪API服务",
        "version": "1.0.0",
        "algorithm": "TK-CBM3D",
        "endpoints": {
            "upload": "/upload",
            "process": "/process/{task_id}",
            "status": "/status/{task_id}",
            "models": "/models",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "denoise", "timestamp": "2024-01-01T00:00:00"}
