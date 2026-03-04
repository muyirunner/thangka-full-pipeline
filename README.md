<div align="center">
  <img src="frontend/public/favicon.ico" alt="Logo" width="80" height="80">
  <h1 align="center">📜 时空修复图鉴 (Thangka Restoration Scroll)</h1>
  <p align="center">
    <b>唐卡数字化全流程体验系统（去噪、超分辨率、元素识别）</b>
  </p>
</div>

---

## 📸 界面预览 (Preview)
<!-- 占位图：请在上传到 GitHub 后，在这里贴上系统界面的截图 -->
| 核心数字展厅 | 修复全流程体验 | 后台管理中台 |
| :---: | :---: | :---: |
| ![数字展厅](https://placehold.co/600x400?text=Digital+Gallery) | ![工作台](https://placehold.co/600x400?text=Restoration+Workspace) | ![管理后台](https://placehold.co/600x400?text=Admin+Panel) |

---

## 📖 项目简介 (Introduction)
《时空修复图鉴》是一款深度结合**计算机视觉大模型**与**顶级 Web 前端交互艺术**的文化遗产修复体验型系统。
本项目以西藏非物质文化遗产“唐卡”为核心，旨在让用户（普通访客、学生、数字艺术爱好者）通过第一人称的“修复师”视角，沉浸式体验从**【残卷鉴定】→【智能算法去噪】→【AI 细节超分还原】**的完整文物修复科研闭环。

本项目不仅仅是一个软件系统，更是一件**数字交互艺术品**。通过空灵暗黑史诗级的 Awwwards 级 UI/UX 视觉重塑（Ethereal Dark Mode & Glassmorphism 2.0），我们致力于在冰冷的算法之外，传递文化遗产跨越时空的厚重与庄严。

### ✨ 核心体验特色 (Key Features)
- **🪐 时空神坛 (Immersive Worktable)**：纯 CSS 渲染的悬浮金粉粒子（Ambient Dust）、带有物理弹性阻尼的法器控制面板（Spring Physics），以及极简琉璃材质（Glassmorphism 2.0）。
- **🔍 三层修复法阵 (The Restoration Pipeline)**：
  - **慧眼洞察 (Scanning)**：基于 **YOLOv8** 目标检测大模型的动态残损点病灶识别与锚点（Bounding Box）高亮。
  - **净水拂尘 (Purifying)**：模拟洗涤降噪过程，平滑古卷噪点。
  - **时光重塑 (Restoring)**：基于 **Real-ESRGAN** (Super-Resolution) 的古画细节超变态清晰还原。
- **🎛️ 双擎驱动模式 (Dual-Engine Mode)**：
  - **预设展厅模式 (Preset Mode)**：为 C 端无缝体验打造。后台一键自动处理低配画质/降噪画质，实现 0 等待、纯享丝滑动画的前台数字展厅效果。
  - **极客全真模式 (Real Compute Mode)**：调用本地 GPU 显存，实时加载 YOLOv8 和 ESRGAN 检查点，对上传的真实损坏唐卡进行即刻物理推理。
- **🛡️ 琉璃秘境管理中台 (Admin Panel)**：内置密码级（`123456`）后台中控。支持引擎健康度实时探测（RAM/CPU）、画廊 100% 动态 CRUD、全状态双向数据绑定及“一键降维打击（自动生成预设文件池）”。

---

## 🛠️ 技术架构 (Technology Stack)
本项目采用前后端绝对分离（Headless）架构构建。

### 🎨 前端 (Frontend: The Digital Canvas)
- **框架**: `Vue 3` (Composition API) + `Vite` 构建工具。
- **状态管理**: `Pinia` (单向数据流动与状态持久化 `localStorage`)。
- **视觉系统**: 纯 Vanilla CSS 驱动的 Awwwards 顶级视觉方案。
  - `Cinzel` & `Noto Serif SC` 史诗/古典双语排版。
  - 自定义 `cubic-bezier` 贝塞尔物理弹簧动画体系。
- **路由方案**: `Vue Router 4` (平滑淡入无缝转场)。

### 🧠 后端 (Backend: The AI Forge)
- **服务器框架**: `FastAPI` + `Uvicorn` (高性能异步网络 IO)。
- **AI 大模型矩阵**:
  - `ultralytics` (YOLOv8 / 计算机视觉检测)
  - `Pillow` (PIL / 基础图像重采样)
  - `TK_CBM3D` 自研噪声去除推理引擎（已集成）
  - `Real-ESRGAN` (Super-Resolution 超分辨率重建 / 已集成)
- **数据持久层**: 轻量级无库架构，核心状态路由至 `config.json` 及文件系统哈希映射。
- **系统探针**: `psutil` 轮询物理机载荷状态。

---

## 📂 目录结构 (Project Structure)
```text
thangka-full-pipeline/
├── backend/                  # FastAPI 后端核心
│   ├── core/                 # AI 推理核心逻辑 (YOLO, TK_CBM3D, Real-ESRGAN)
│   ├── models/               # 模型权重存放处
│   ├── app.py                # 主服务端入口
│   ├── config.example.json   # 系统配置模板
│   └── requirements.txt      # Python 依赖清单
├── frontend/                 # Vue3 前端展厅
│   ├── public/               # 静态资源与画廊图库
│   ├── src/                  # 前端源码 (组件、路由、状态管理)
│   ├── package.json          # Node.js 依赖清单
│   └── vite.config.js        # Vite 打包配置
├── .gitignore                # Git 忽略配置
├── LICENSE                   # 开源许可证
└── README.md                 # 项目说明文档
```

---

## 🚀 部署与运行指南 (Getting Started)

### 📌 前置要求 (Prerequisites)
- **Node.js** (>= 16.x)
- **Python** (>= 3.9) 加 Conda 虚拟环境（推荐）
- **GPU**（可选）：拥有 NVIDIA 独显可加速 YOLO 检测与超分辨率推理

### ⚙️ 后端 AI 引擎启动 (Backend Setup)
1. 进入后端目录：
   ```bash
   cd backend
   ```
2. 安装大模型及运行依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 下载 Real-ESRGAN 预训练模型权重（约 330MB，仅首次需要）：
   > 由于模型体积过大，未包含在 Git 仓库中，请手动下载并放入 `backend/models/esrgan_pretrained/` 目录。
   - 📥 从 [Real-ESRGAN 官方 Release](https://github.com/xinntao/Real-ESRGAN/releases) 下载以下文件：
     - `RealESRGAN_x4plus.pth`（必需）
     - `RealESRGAN_x2plus.pth`（可选）
   - 或从百度网盘一键下载全部权重：`（请替换为您的网盘链接）`
4. 首次运行前，请复制配置文件模板：
   ```bash
   cp config.example.json config.json
   ```
5. 启动 FastAPI 核心枢纽：
   ```bash
   python app.py
   # 服务将运行在 http://127.0.0.1:8000
   ```
*(注：按 `Ctrl + C` 可安全静默退出服务器)*

### 🔮 前端数字展厅启动 (Frontend Setup)
1. 进入前端目录：
   ```bash
   cd frontend
   ```
2. 安装 Vue 依赖：
   ```bash
   npm install
   ```
3. 启动 Vite 本地魔法服务器：
   ```bash
   npm run dev
   # 展厅默认开启于 http://localhost:5173
   ```

---

## 🗝️ 后台入径指南 (Admin Operations)
中台管理面板允许你随时调控这套庞大的数字资产系统。
- **管理入口 url**: `http://localhost:5173/admin`
- **最高权限密匙**: `123456`
- **主要能力**:
  - **模式切换**: 强制覆盖前端体验为“流媒体预设”或“GPU硬核演算”。
  - **画廊治理**: 一键点亮/熄灭全站唐卡。
  - **图鉴补完计划**: 点击 `[添加新画作]`，上传一张 4K 原图，后端会自动下渗（Downscale + Add Noise）为您洗出前台“未修复”与“降噪中”的虚拟物料，实现上货即用。

---

## 📄 许可证 (License)
本项目基于 [MIT License](./LICENSE) 开源。

---
<p align="center">
  <i>"在代码的微粒与像素的交响中，时间倒流，文明永存。"</i>
</p>
