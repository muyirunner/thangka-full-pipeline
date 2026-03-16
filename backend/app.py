from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import io
import base64
from PIL import Image
import time
import os
from pathlib import Path
import sys
import threading
import uuid
import asyncio
try:
    from ultralytics import YOLO
except ImportError:
    print("Warning: ultralytics is not installed. YOLO detection will fail.")

# Ensure core modules can be imported
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "core"))
# Add Real-ESRGAN-Adaptive to path
sys.path.insert(0, str(PROJECT_ROOT / "core" / "Real-ESRGAN-Adaptive"))

try:
    from tk_noise.app.models.tk_cbm3d import TK_CBM3D
except ImportError as e:
    print(f"Warning: TK_CBM3D could not be imported: {e}")

try:
    from universal_processor import UniversalImageProcessor
except ImportError as e:
    print(f"Warning: UniversalImageProcessor could not be imported: {e}")

app = FastAPI(title="Time Restoration Lab API", version="1.0.0")

# ============================================================
# Model Loading & Warmup (Global Singleton)
# ============================================================
inference_lock = threading.Lock()
yolo_model = None
try:
    # Prioritize the newest custom trained model, then fallback
    model_paths = [
        PROJECT_ROOT / 'models' / 'yolo_best.pt'
    ]
    
    for m_path in model_paths:
        if m_path.exists():
            print(f"Loading YOLOv8 model: {m_path}")
            yolo_model = YOLO(str(m_path))
            # [Performance Obsession] 毫秒级冷启动 (Warmup)
            import numpy as np
            print("Warming up YOLO model with dummy tensor...")
            dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
            yolo_model.predict(source=dummy_img, verbose=False)
            print("YOLO warmup complete. Ready for zero-latency inference.")
            break
            
    if not yolo_model:
        print("Warning: No YOLO model found in the specified paths.")
except Exception as e:
    print(f"Error loading YOLO model: {e}")

# ============================================================
# Class Info (from Legacy)
# ============================================================
CLASS_NAME_ZH = {
    "Buddha": "佛像", "mandala": "曼陀罗", "nine signs and eight diagrams": "九宫八卦",
    "lotus tower": "莲花塔", "treasure": "宝物", "cloud": "云纹",
    "flower and leaf": "花叶", "ivory": "象牙", "water": "水纹",
    "tree": "树木", "mirror": "镜子", "animals": "动物",
    "wrathful deity": "忿怒尊", "umbrella": "宝伞", "vajra wheel": "金刚轮",
    "rock": "岩石", "fire": "火焰", "stick": "棍杖",
    "scepter": "权杖", "bull": "牛", "pagoda": "宝塔",
    "moon": "月亮", "mountain": "山", "bottle": "宝瓶",
    "conch": "法螺", "bowl": "钵", "horse": "马",
    "ribbon": "丝带", "loong": "龙", "bird": "鸟",
    "building": "建筑", "people": "人物", "Pipa": "琵琶",
    "trident": "三叉戟", "deer": "鹿", "sun": "太阳",
    "wheel of life": "法轮", "fruit": "果实", "Kapala skull cup": "嘎巴拉碗",
    "body organ": "身体器官", "vajra bell": "金刚铃", "crane": "仙鹤",
    "victory banner": "胜利幢", "lion": "狮子", "tiger": "虎",
    "sword": "剑", "elephant": "象", "canopy": "华盖",
    "prayer beads": "念珠", "coral": "珊瑚", "rope": "绳索",
    "vajra": "金刚杵", "arrow": "箭", "bow": "弓",
    "axe": "斧", "symbol of ease": "如意", "horsetail whisk": "拂尘",
    "dog": "犬", "monkey": "猴", "rat": "鼠",
    "peafowl": "孔雀", "Shri Chitipati": "尸陀林主", "spear": "矛",
    "lucky knot": "吉祥结", "pig": "猪", "fish": "鱼",
    "vulture": "秃鹫", "shield": "盾", "chook": "鸡",
    "grain": "谷物", "censer": "香炉", "celestial map": "天象图",
    "sheep": "羊", "boat": "船", "dart": "飞镖",
    "flag": "旗帜", "vajra hammer": "金刚锤", "drum": "鼓",
    "vajra knife": "金刚刀",
}
MAX_IMAGE_SIZE = 2048

# CORS setup for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Config Management (config.json)
# ============================================================
import json

CONFIG_PATH = PROJECT_ROOT / "config.json"

def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}", flush=True)
        return {"mode": "preset", "admin_password": "change-this-admin-password", "gallery": []}

def save_config(config):
    """保存配置文件"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# ============================================================
# Admin API Endpoints
# ============================================================
from fastapi import Header, Query
from fastapi.responses import JSONResponse
from typing import Optional

def verify_admin(password: str = Header(None, alias="X-Admin-Password")):
    """管理员密码验证（仅用于本地演示/实验环境）"""
    config = load_config()
    if password != config.get("admin_password", "change-this-admin-password"):
        raise HTTPException(status_code=401, detail="密码错误")

@app.get("/api/v1/admin/settings")
async def get_admin_settings(password: str = Header(None, alias="X-Admin-Password")):
    """获取管理员设置"""
    verify_admin(password)
    config = load_config()
    return {"mode": config.get("mode", "preset"), "gallery_count": len(config.get("gallery", []))}

@app.put("/api/v1/admin/settings")
async def update_admin_settings(password: str = Header(None, alias="X-Admin-Password"), mode: str = Query(...)):
    """切换运行模式 (preset/real)"""
    verify_admin(password)
    if mode not in ("preset", "real"):
        raise HTTPException(status_code=400, detail="模式必须是 'preset' 或 'real'")
    config = load_config()
    config["mode"] = mode
    save_config(config)
    print(f"[Admin] 模式已切换为: {mode}", flush=True)
    return {"success": True, "mode": mode}

@app.get("/api/v1/admin/gallery")
async def get_admin_gallery(password: str = Header(None, alias="X-Admin-Password")):
    """获取完整画廊列表（带实际文件存在性校验，用于管理员视图）"""
    verify_admin(password)
    config = load_config()
    gallery_items = config.get("gallery", [])
    
    # 获取 frontend 目录用于实体校验
    FRONTEND_DIR = PROJECT_ROOT.parent / "frontend" / "public"
    
    enriched_gallery = []
    for item in gallery_items:
        filename = item.get("filename", "")
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        
        orig_path = FRONTEND_DIR / "gallery" / filename
        damaged_path = FRONTEND_DIR / "gallery" / f"{stem}_damaged{suffix}"
        purified_path = FRONTEND_DIR / "gallery" / f"{stem}_purified{suffix}"
        
        item_copy = dict(item)
        item_copy["isRestored"] = item.get("isRestored", False)
        item_copy["variants"] = {
            "original": orig_path.exists() if filename else False,
            "damaged": damaged_path.exists() if filename else False,
            "purified": purified_path.exists() if filename else False
        }
        enriched_gallery.append(item_copy)
        
    return {"gallery": enriched_gallery}

import shutil

from PIL import ImageEnhance, ImageFilter
import numpy as np

def add_gaussian_noise(img_array, sigma=35):
    noise = np.random.normal(0, sigma, img_array.shape).astype(np.float32)
    noisy = img_array.astype(np.float32) + noise
    return np.clip(noisy, 0, 255).astype(np.uint8)

def generate_preset_variants(orig_path: Path, filename: str):
    """自动生成受损版和降噪版预设图"""
    print(f"[Admin] 开始为上传图片 {filename} 生成预设管线...", flush=True)
    img = Image.open(orig_path).convert('RGB')
    orig_w, orig_h = img.size
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    gallery_dir = orig_path.parent
    
    # --- 生成 Damaged 版本 ---
    new_w = int(orig_w * 0.35)
    new_h = int(orig_h * 0.35)
    img_small = img.resize((new_w, new_h), Image.LANCZOS)
    img_desaturated = ImageEnhance.Color(img_small).enhance(0.25)
    img_dark = ImageEnhance.Brightness(img_desaturated).enhance(0.7)
    img_low_contrast = ImageEnhance.Contrast(img_dark).enhance(0.85)
    noisy_array = add_gaussian_noise(np.array(img_low_contrast), 35)
    img_noisy = Image.fromarray(noisy_array)
    img_blurred = img_noisy.filter(ImageFilter.GaussianBlur(radius=0.8))
    img_final = img_blurred.resize((orig_w, orig_h), Image.LANCZOS)
    damaged_path = gallery_dir / f"{stem}_damaged{suffix}"
    img_final.save(damaged_path, format='JPEG', quality=60)
    
    # --- 生成 Purified 版本 ---
    purified_scale = 0.35 * 1.3
    new_w = int(orig_w * purified_scale)
    new_h = int(orig_h * purified_scale)
    img_small = img.resize((new_w, new_h), Image.LANCZOS)
    img_color = ImageEnhance.Color(img_small).enhance(0.65)
    img_bright = ImageEnhance.Brightness(img_color).enhance(0.88)
    img_blurred = img_bright.filter(ImageFilter.GaussianBlur(radius=0.5))
    img_final = img_blurred.resize((orig_w, orig_h), Image.LANCZOS)
    purified_path = gallery_dir / f"{stem}_purified{suffix}"
    img_final.save(purified_path, format='JPEG', quality=80)
    print(f"[Admin] 预设图生成化管线完成！", flush=True)

@app.post("/api/v1/admin/upload")
async def upload_gallery_item(file: UploadFile = File(...), password: str = Header(None, alias="X-Admin-Password")):
    """一键上传唐卡并自动构建预设管线"""
    verify_admin(password)
    config = load_config()
    gallery = config.get("gallery", [])
    
    safe_filename = file.filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
    frontend_dir = PROJECT_ROOT.parent / "frontend" / "public" / "gallery"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    orig_path = frontend_dir / safe_filename
    
    # 保存原始大图
    with open(orig_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 异步执行耗时的降频/加噪处理
    await asyncio.to_thread(generate_preset_variants, orig_path, safe_filename)
        
    new_id = max((item["id"] for item in gallery), default=0) + 1
    new_item = {
        "id": new_id, 
        "title": f"新上传唐卡 {new_id}", 
        "desc": "正在生成预设...", 
        "filename": safe_filename,
        "variants": {
            "original": True,
            "damaged": False,
            "purified": False
        }
    }
    gallery.append({k: v for k, v in new_item.items() if k != "variants"}) # Only save core fields to config.json
    config["gallery"] = gallery
    save_config(config)
    
    return {"success": True, "item": new_item}

@app.delete("/api/v1/admin/gallery/{item_id}")
async def delete_gallery_item(item_id: int, password: str = Header(None, alias="X-Admin-Password")):
    """删除画廊项目"""
    verify_admin(password)
    config = load_config()
    gallery = config.get("gallery", [])
    config["gallery"] = [item for item in gallery if item["id"] != item_id]
    save_config(config)
    return {"success": True}

@app.get("/api/v1/admin/health")
async def get_admin_health(password: str = Header(None, alias="X-Admin-Password")):
    """获取系统算法引擎健康度"""
    verify_admin(password)
    
    health_data = {
        "yolo_loaded": yolo_model is not None,
        "ram_usage_percent": 0,
        "cpu_usage_percent": 0,
        "psutil_available": False
    }
    
    try:
        import psutil
        health_data["psutil_available"] = True
        health_data["ram_usage_percent"] = psutil.virtual_memory().percent
        health_data["cpu_usage_percent"] = psutil.cpu_percent(interval=0.1)
    except ImportError:
        # 降级处理：如果没有 psutil，则返回 0
        pass
        
    return health_data

class GalleryItemUpdate(BaseModel):
    title: str
    desc: str
    isRestored: bool = False

class BatchRestoreUpdate(BaseModel):
    isRestored: bool

@app.put("/api/v1/admin/gallery/batch-restore")
async def batch_update_restore_status(update_data: BatchRestoreUpdate, password: str = Header(None, alias="X-Admin-Password")):
    """一键点亮或熄灭所有画廊项目"""
    verify_admin(password)
    config = load_config()
    gallery = config.get("gallery", [])
    
    for item in gallery:
        item["isRestored"] = update_data.isRestored
        
    config["gallery"] = gallery
    save_config(config)
    return {"success": True, "count": len(gallery)}

@app.put("/api/v1/admin/gallery/{item_id}")
async def update_gallery_item(item_id: int, item_data: GalleryItemUpdate, password: str = Header(None, alias="X-Admin-Password")):
    """更新画廊项目信息"""
    verify_admin(password)
    config = load_config()
    gallery = config.get("gallery", [])
    
    updated = False
    for item in gallery:
        if item["id"] == item_id:
            item["title"] = item_data.title
            item["desc"] = item_data.desc
            item["isRestored"] = item_data.isRestored
            updated = True
            break
            
    if not updated:
        raise HTTPException(status_code=404, detail="图鉴项目未找到")
        
    config["gallery"] = gallery
    save_config(config)
    return {"success": True}

# ============================================================
# Public Gallery API (动态画廊数据，前端通过此接口获取)
# ============================================================
@app.get("/api/v1/gallery")
async def get_public_gallery():
    """返回画廊列表和当前模式设置，供前端使用"""
    config = load_config()
    mode = config.get("mode", "preset")
    gallery = config.get("gallery", [])
    
    # 为每个画廊项目构建完整的 URL 映射
    items = []
    for item in gallery:
        filename = item.get("filename", "")
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        items.append({
            "id": item["id"],
            "title": item["title"],
            "desc": item["desc"],
            "url": f"/gallery/{filename}",                     # 原图（清晰版 = 最终修复结果）
            "damagedUrl": f"/gallery/{stem}_damaged{suffix}",  # 损坏版（展示用）
            "purifiedUrl": f"/gallery/{stem}_purified{suffix}", # 降噪版（中间结果）
            "restoredUrl": f"/gallery/{filename}",             # 修复版 = 原图
            "isRestored": item.get("isRestored", False)        # 是否被点亮
        })
    
    return {"mode": mode, "items": items}


@app.get("/")
def read_root():
    return {"message": "Welcome to the Time Restoration Lab API. Tashi is ready!"}

@app.post("/api/v1/scan")
async def scan_image(file: UploadFile = File(...)):
    """
    Tashi's Stage 2: Scanning the image for Thangka elements using YOLOv8.
    """
    try:
        if not yolo_model:
             raise Exception("YOLO model not loaded.")
             
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # Resize if too large to prevent OOM
        orig_w, orig_h = img.size
        if max(orig_w, orig_h) > MAX_IMAGE_SIZE:
            scale = MAX_IMAGE_SIZE / max(orig_w, orig_h)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        
        # Offload YOLO detection to a thread, but keep the lock since YOLO spikes VRAM heavily
        def run_yolo():
            with inference_lock:
                return yolo_model.predict(source=img, conf=0.10, verbose=False)

        results = await asyncio.to_thread(run_yolo)
        result = results[0]

        detections = []
        boxes = result.boxes
        if boxes is not None and len(boxes) > 0:
            for i in range(len(boxes)):
                box = boxes[i]
                cls_id = int(box.cls[0])
                cls_name = result.names[cls_id]
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detections.append({
                    'class_en': cls_name,
                    'class_zh': CLASS_NAME_ZH.get(cls_name, cls_name),
                    'confidence': round(confidence, 3),
                    'bbox': [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)]
                })
        
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            "success": True,
            "message": "扫描完成！",
            "detections": detections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/purify")
async def purify_image(file: UploadFile = File(...)):
    """
    Tashi's Stage 3 (Part 1): Purifying the image (Denoising).
    """
    try:
        # Create temp dir for tk_noise processing
        temp_dir = PROJECT_ROOT / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Generate a unique token for this request
        task_id = uuid.uuid4().hex[:8]
        safe_filename = file.filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
        
        input_path = temp_dir / f"in_denoise_{task_id}_{safe_filename}"
        output_path = temp_dir / f"out_denoise_{task_id}_{safe_filename}"
        
        contents = await file.read()
        
        # Speed Optimization: TK_CBM3D is O(N * W^2) in pure Python and will freeze on large images.
        # We must resize it to a reasonable maximum (decreased from 600px to 400px for massive speedup) before denoising.
        # The subsequent "Restore" (Super Resolution) step will scale it up 4x anyway, so 400px is perfect.
        img = Image.open(io.BytesIO(contents)).convert('RGB')
        orig_w, orig_h = img.size
        print(f"\n[净水拂尘] 收到上传图像，原始尺寸: {orig_w}x{orig_h}", flush=True)
        MAX_DENOISE_SIZE = 400
        if max(orig_w, orig_h) > MAX_DENOISE_SIZE:
            scale = MAX_DENOISE_SIZE / max(orig_w, orig_h)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            print(f"[净水拂尘] 正在将图像缩放至安全计算尺寸: {new_w}x{new_h} 以加速处理...", flush=True)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        
        # Save the resized (or original) image to the input path
        img.save(input_path, format="JPEG", quality=95)
            
        # Run denoising sequentially in threadpool (removes freezing of the async loop)
        def run_tk_cbm3d():
            print(f"[净水拂尘] 启动 TK_CBM3D 降噪核心算法 (异步线程池/无阻塞)...", flush=True)
            denoiser = TK_CBM3D()
            return denoiser.denoise(
                str(input_path),
                str(output_path),
                strength=50
            )
            
        result_path_str = await asyncio.to_thread(run_tk_cbm3d)
        result_path = Path(result_path_str)
        
        # Read the result and encode to base64
        with open(result_path, "rb") as f:
            result_contents = f.read()
            
        encoded_string = base64.b64encode(result_contents).decode('utf-8')
        result_image = f"data:image/jpeg;base64,{encoded_string}"
        
        # Cleanup
        if input_path.exists(): input_path.unlink()
        if Path(result_path).exists(): Path(result_path).unlink()

        return {
            "success": True,
            "message": "『净水拂尘』施放成功！杂质已清除！",
            "result_image": result_image,
            "technique": "AI 智能降噪算法 (TK_CBM3D)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/restore")
async def restore_image(file: UploadFile = File(...)):
    """
    Tashi's Stage 3 (Part 2): Restoring the image details (Super Resolution).
    """
    try:
        # Create temp dir
        temp_dir = PROJECT_ROOT / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Generate a unique task id to prevent crossover
        task_id = uuid.uuid4().hex[:8]
        safe_filename = file.filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
        input_path = temp_dir / f"in_sr_{task_id}_{safe_filename}"
        
        contents = await file.read()
        with open(input_path, "wb") as f:
            f.write(contents)
            
        # Run processing inside threadpool to prevent freezing event loop
        def run_realesrgan():
            print(f"\n[时光重塑] 启动 Real-ESRGAN 超分复原算法 (异步线程池/无阻塞)...", flush=True)
            # Initialize the processor
            # processor weights are now loaded via absolute paths from inside universal_processor.py modifications
            processor = UniversalImageProcessor(
                model_name='RealESRGAN_x4plus',
                output_dir=str(temp_dir),
                tile_size=256,
                overlap=32,
                size_threshold=600  # Aggressive tiling to prevent OOM
            )
            
            # Snapshot existing files in temp_dir BEFORE processing
            existing_files = set(temp_dir.iterdir())
            
            # Run processing
            success = processor.process_single_image(str(input_path))
            
            if not success:
                raise Exception("Super resolution processing failed — process_single_image returned False.")
            
            # Find the NEW output file(s) created by the processor
            new_files = set(temp_dir.iterdir()) - existing_files
            # Filter to only files that match our input stem
            input_stem = Path(input_path).stem
            matching_outputs = [f for f in new_files if f.is_file() and input_stem in f.stem]
            
            if not matching_outputs:
                raise Exception(f"Super resolution completed but no output file found for stem '{input_stem}'.")
            
            out_path = matching_outputs[0]
            print(f"[时光重塑] ✅ 超分完成，输出文件: {out_path.name}", flush=True)
            return out_path
            
        output_path = await asyncio.to_thread(run_realesrgan)

        # Read the result and encode to base64
        with open(output_path, "rb") as f:
            result_contents = f.read()
            
        encoded_string = base64.b64encode(result_contents).decode('utf-8')
        result_image = f"data:image/jpeg;base64,{encoded_string}"
        
        # Cleanup
        if input_path.exists(): input_path.unlink()
        if output_path.exists(): output_path.unlink()

        return {
            "success": True,
            "message": "奇迹出现！画面的细节生动再现！",
            "result_image": result_image,
            "technique": "AI 超分辨率重建 (Real-ESRGAN)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        pass
