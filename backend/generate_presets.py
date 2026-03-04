"""
唐卡图片降级脚本
将原始清晰唐卡图片生成两个降级版本：
1. _damaged.jpg — 加噪点 + 降分辨率 + 去饱和（模拟损坏古画）
2. _purified.jpg — 无噪点但低分辨率（模拟降噪后但未超分的状态）

原始图片保留为最终修复结果。
"""
import os
import sys
from pathlib import Path
import numpy as np

try:
    from PIL import Image, ImageFilter, ImageEnhance
except ImportError:
    print("需要安装 Pillow: pip install Pillow")
    sys.exit(1)

GALLERY_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "gallery"

# 降级参数
DOWNSCALE_FACTOR = 0.35      # 缩小到原始的 35%
NOISE_STRENGTH = 35          # 高斯噪声标准差
SATURATION_FACTOR = 0.25     # 饱和度（0=灰度, 1=原色）
BRIGHTNESS_FACTOR = 0.7      # 亮度
CONTRAST_FACTOR = 0.85       # 对比度
JPEG_QUALITY_DAMAGED = 60    # 压缩质量（模拟陈旧质感）
JPEG_QUALITY_PURIFIED = 80   # 稍好一些的质量


def add_gaussian_noise(img_array, sigma=NOISE_STRENGTH):
    """为图像添加高斯噪声"""
    noise = np.random.normal(0, sigma, img_array.shape).astype(np.float32)
    noisy = img_array.astype(np.float32) + noise
    return np.clip(noisy, 0, 255).astype(np.uint8)


def create_damaged_version(original_path, output_path):
    """
    创建受损版本：噪点 + 低分辨率 + 轻微去饱和 + 降低亮度/对比度
    模拟一幅蒙尘褪色的古老唐卡
    """
    img = Image.open(original_path).convert('RGB')
    orig_w, orig_h = img.size
    
    # Step 1: 缩小分辨率
    new_w = int(orig_w * DOWNSCALE_FACTOR)
    new_h = int(orig_h * DOWNSCALE_FACTOR)
    img_small = img.resize((new_w, new_h), Image.LANCZOS)
    
    # Step 2: 降低饱和度（模拟褪色）
    enhancer = ImageEnhance.Color(img_small)
    img_desaturated = enhancer.enhance(SATURATION_FACTOR)
    
    # Step 3: 降低亮度（模拟蒙尘）
    enhancer = ImageEnhance.Brightness(img_desaturated)
    img_dark = enhancer.enhance(BRIGHTNESS_FACTOR)
    
    # Step 4: 降低对比度
    enhancer = ImageEnhance.Contrast(img_dark)
    img_low_contrast = enhancer.enhance(CONTRAST_FACTOR)
    
    # Step 5: 添加高斯噪声
    img_array = np.array(img_low_contrast)
    noisy_array = add_gaussian_noise(img_array, NOISE_STRENGTH)
    img_noisy = Image.fromarray(noisy_array)
    
    # Step 6: 轻微模糊（模拟镜头退化）
    img_blurred = img_noisy.filter(ImageFilter.GaussianBlur(radius=0.8))
    
    # 放回原始尺寸（保留低分辨率感，但尺寸匹配）
    img_final = img_blurred.resize((orig_w, orig_h), Image.LANCZOS)
    
    img_final.save(output_path, format='JPEG', quality=JPEG_QUALITY_DAMAGED)
    print(f"  ✅ damaged: {new_w}x{new_h} → {orig_w}x{orig_h} | noise={NOISE_STRENGTH} | sat={SATURATION_FACTOR}")


def create_purified_version(original_path, output_path):
    """
    创建降噪版本：低分辨率但无噪点,颜色恢复一些
    模拟降噪算法处理后的状态 — 更清晰但细节仍有缺失
    """
    img = Image.open(original_path).convert('RGB')
    orig_w, orig_h = img.size
    
    # Step 1: 缩小分辨率（比 damaged 版本略大一点，模拟降噪恢复了一些质量）
    purified_scale = DOWNSCALE_FACTOR * 1.3  # 略高于 damaged
    new_w = int(orig_w * purified_scale)
    new_h = int(orig_h * purified_scale)
    img_small = img.resize((new_w, new_h), Image.LANCZOS)
    
    # Step 2: 轻微降低饱和度（比 damaged 保留更多颜色）
    enhancer = ImageEnhance.Color(img_small)
    img_color = enhancer.enhance(0.65)  # 比 damaged 的 0.25 好很多
    
    # Step 3: 轻微降低亮度
    enhancer = ImageEnhance.Brightness(img_color)
    img_bright = enhancer.enhance(0.88)
    
    # Step 4: 轻微模糊（模拟低分辨率缺失细节）
    img_blurred = img_bright.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # 放回原始尺寸
    img_final = img_blurred.resize((orig_w, orig_h), Image.LANCZOS)
    
    img_final.save(output_path, format='JPEG', quality=JPEG_QUALITY_PURIFIED)
    print(f"  ✅ purified: {new_w}x{new_h} → {orig_w}x{orig_h} | sat=0.65 | brightness=0.88")


def main():
    if not GALLERY_DIR.exists():
        print(f"❌ 画廊目录不存在: {GALLERY_DIR}")
        sys.exit(1)
    
    # 找到所有原始图片（排除已生成的 _damaged 和 _purified 版本）
    image_files = [
        f for f in GALLERY_DIR.iterdir()
        if f.suffix.lower() in ('.jpg', '.jpeg', '.png')
        and '_damaged' not in f.stem
        and '_purified' not in f.stem
    ]
    
    print(f"\n{'='*60}")
    print(f"🎨 唐卡图片降级处理器")
    print(f"{'='*60}")
    print(f"📁 画廊目录: {GALLERY_DIR}")
    print(f"📸 发现 {len(image_files)} 张原始图片")
    print(f"{'='*60}\n")
    
    for i, img_path in enumerate(sorted(image_files), 1):
        damaged_path = GALLERY_DIR / f"{img_path.stem}_damaged{img_path.suffix}"
        purified_path = GALLERY_DIR / f"{img_path.stem}_purified{img_path.suffix}"
        
        print(f"[{i}/{len(image_files)}] 处理: {img_path.name}")
        
        try:
            create_damaged_version(img_path, damaged_path)
            create_purified_version(img_path, purified_path)
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
        
        print()
    
    print(f"{'='*60}")
    print(f"🎉 全部处理完成！共生成 {len(image_files) * 2} 张降级图片")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
