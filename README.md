<div align="center">
  <img src="frontend/public/favicon.ico" alt="Logo" width="80" height="80">
  <h1 align="center">📜 时空修复图鉴 (Thangka Restoration Scroll)</h1>
  <p align="center"><b>唐卡数字化全流程体验系统（去噪、超分辨率、元素识别）</b></p>
</div>

---

## 项目简介

`thangka-full-pipeline` 是一个围绕 **唐卡数字化处理流程** 搭建的前后端一体化项目，尝试把图像检测、去噪、超分辨率增强与前端交互体验整合到同一个系统中。

相比只展示单点算法能力，这个项目更关注：

- 如何把图像处理链路组织成完整流程
- 如何让用户直观看到“输入 → 处理 → 结果”的变化
- 如何把文化数字化主题与系统交互体验结合起来

它既是一个图像处理系统原型，也是我在 **计算机视觉 + 前端交互 + 系统设计** 方向上的一次综合实践。

## 核心能力

### 1. 图像处理链路
- **目标检测**：基于 YOLOv8，对图像中的关键元素进行识别与分析
- **去噪处理**：提供图像降噪能力，用于模拟受损画作修复前后的处理过程
- **超分辨率增强**：结合 Real-ESRGAN，对图像细节进行增强

### 2. 前端展厅体验
- 基于 Vue 3 + Vite 构建交互式展厅界面
- 将图像处理过程组织为更易理解的分阶段体验
- 支持预设内容展示与流程化浏览

### 3. 管理侧能力
- 提供后台管理入口用于调节运行模式、管理画廊资源和上传素材
- 支持将新增图片纳入展示流程

> 说明：当前仓库中的管理侧能力主要用于本地演示与实验，不建议把示例配置直接用于公开生产环境。

## 当前仓库包含什么

这个仓库当前主要包含两部分：

### 前端（`frontend/`）
- Vue 3
- Vite
- Vue Router
- Pinia
- 展厅页面与流程交互逻辑

### 后端（`backend/`）
- FastAPI 服务入口
- YOLOv8 推理接入
- 图像去噪模块
- Real-ESRGAN 相关集成目录
- 画廊预设生成脚本

## 项目结构

```text
thangka-full-pipeline/
├── backend/                  # FastAPI 后端核心
│   ├── core/                 # AI 推理核心逻辑（YOLO / 去噪 / 超分）
│   ├── models/               # 模型权重目录
│   ├── app.py                # 主服务端入口
│   ├── config.example.json   # 系统配置模板
│   └── requirements.txt      # Python 依赖
├── frontend/                 # Vue3 前端展厅
│   ├── public/gallery/       # 展示素材与预设图片
│   ├── src/                  # 前端源码
│   ├── package.json          # Node.js 依赖
│   └── vite.config.js        # Vite 配置
├── LICENSE
└── README.md
```

## 技术栈

### Frontend
- Vue 3
- Vite
- Vue Router
- Pinia
- Vanilla CSS

### Backend
- FastAPI
- Uvicorn
- Ultralytics / YOLOv8
- Pillow
- NumPy
- psutil

### AI / 图像处理
- YOLOv8
- TK_CBM3D
- Real-ESRGAN

## 运行方式

### 环境要求
- Node.js 16+
- Python 3.9+
- 如需更完整地运行超分或检测流程，建议具备可用的 CUDA / GPU 环境

### 启动后端

```bash
cd backend
pip install -r requirements.txt
cp config.example.json config.json
python app.py
```

默认情况下，后端服务运行在：

- `http://127.0.0.1:8000`

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认情况下，前端运行在：

- `http://localhost:5173`

## 关于模型与素材

仓库中已经保留了一部分用于展示和实验的素材，但完整运行某些能力时，仍可能依赖：

- 本地模型权重
- GPU 环境
- 额外的图像处理依赖

如果你打算把这个项目作为正式演示系统继续完善，建议后续进一步区分：

- **演示素材**
- **实验素材**
- **模型权重**
- **部署配置**

这样项目结构会更清楚，也更适合长期维护。

## 当前适合如何理解这个项目

我更愿意把它看作一个：

- **系统型作品原型**
- **图像处理流程展示项目**
- **文化数字化方向的综合实践**

它的重点不是把某一个模块吹到最强，而是把多个模块组织成一个能被看懂、被体验、被继续打磨的整体系统。

## 后续最值得继续完善的部分

- 补充真实系统截图或演示 GIF
- 明确前后端的联调方式
- 补充模型权重获取说明
- 梳理管理侧配置，避免示例配置被误用到生产环境
- 收紧 README 中“已实现”和“规划中”的边界

## Related Projects

- [thangka-detection](https://github.com/muyirunner/thangka-detection)：唐卡元素智能识别项目
- [muyirunner-site](https://github.com/muyirunner/muyirunner-site)：个人网站与在线作品集
- [GitHub Profile](https://github.com/muyirunner/muyirunner)：GitHub 个人主页

---

这个项目是我把算法模块、前端展示和系统体验揉在一起的一次尝试。对我来说，它的重要性不只是“做了多少功能”，而是它让我开始更认真地思考：如何把一个技术方向组织成一个真正像作品的系统。
