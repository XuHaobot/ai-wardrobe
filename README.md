# AI 智能衣橱 (AI Smart Wardrobe)

> 基于多模态大模型的个性化穿搭推荐 + 虚拟试穿全栈应用  
> FastAPI + Vue3 + ChromaDB + 通义千问 VL + 即梦生图

[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen)](https://vuejs.org)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

---

## 项目概述

**AI 智能衣橱** 是一个完整的全栈 AI 应用，让用户上传自己的衣物图片，系统自动识别衣物属性，
提供**语义搜索**、**天气感知穿搭推荐**、**AI 智能对话**、**虚拟试穿**四大核心能力。

### 效果展示

#### 1. 衣橱管理 + 智能推荐
![衣橱管理](screenshots/wardrobe.png)

#### 2. 虚拟试穿效果
![虚拟试穿](screenshots/tryon.png)

---

## 核心能力

| 能力 | 实现细节 |
|------|----------|
| **多模态衣物识别** | 上传图片后自动用通义千问 VL 识别颜色/类别/材质，存数据库 |
| **向量语义搜索** | DashScope text-embedding-v3 + ChromaDB，支持「找一件适合春天的外套」式查询 |
| **天气感知推荐** | 集成高德天气 API，根据城市天气 + 出行场景推荐穿搭 |
| **AI 智能对话** | Agent + Function Calling，支持多轮对话 + SSE 流式输出 |
| **虚拟试穿** | DashScope aitryon 模型 + 即梦生图，自动加载男/女模特底图 |
| **JWT 用户系统** | 注册/登录/Token 认证，bcrypt 密码加密 |

---

## 技术架构

```
┌────────────────────────────────────────────────────┐
│  前端 (Vue 3 + Vite + Element Plus)                │
│  ├─ 登录/注册 (JWT)                                │
│  ├─ 衣橱管理 (上传/分类/搜索)                       │
│  ├─ 天气组件 (高德 IP 定位)                         │
│  ├─ 虚拟试穿展示                                    │
│  └─ AI 对话面板 (SSE 流式)                          │
└─────────────────┬──────────────────────────────────┘
                  │ Vite Proxy (port 8000)
┌─────────────────▼──────────────────────────────────┐
│  后端 (Python FastAPI)                              │
│  ├─ /auth    JWT 认证                              │
│  ├─ /items   衣物上传 + AI 识别                     │
│  ├─ /closet  衣橱管理 + 向量搜索                    │
│  ├─ /recommend 天气感知推荐                         │
│  ├─ /tryon   虚拟试穿 (DashScope aitryon)          │
│  ├─ /weather 天气查询 (高德代理)                    │
│  └─ /api/chat 多轮对话 + Function Calling          │
└─────────────────┬──────────────────────────────────┘
                  │
       ┌──────────┼──────────┬─────────────┐
       ▼          ▼          ▼             ▼
   ChromaDB   SQLite    腾讯云COS      DashScope
   (向量索引)  (元数据)   (衣物图存储)   (多模态/Embedding)
```

---

## 目录结构

```
aitryon/
├── backend/                          # Python FastAPI 后端
│   ├── main.py                       # FastAPI 入口
│   ├── config.py                     # 配置管理（pydantic-settings）
│   ├── database.py                   # SQLAlchemy ORM
│   ├── .env.example                  # 环境变量模板
│   ├── requirements.txt              # Python 依赖
│   ├── agent/                        # Agent 模块
│   │   ├── core.py                   # LLM 调用 + Function Calling
│   │   ├── tools.py                  # 工具定义
│   │   ├── tool_executor.py          # 工具执行器
│   │   └── memory.py                 # 多轮对话记忆
│   ├── routers/                      # API 路由
│   │   ├── auth.py                   # 用户认证
│   │   ├── closet.py                 # 衣橱管理
│   │   ├── recommend.py              # 推荐
│   │   ├── tryon.py                  # 虚拟试穿
│   │   ├── weather.py                # 天气
│   │   └── chat.py                   # AI 对话
│   ├── services/                     # 业务逻辑
│   │   ├── closet_service.py         # 衣橱服务
│   │   ├── cos_storage.py            # 腾讯云 COS
│   │   ├── recommend_service.py      # 推荐服务
│   │   ├── tryon_service.py          # 试穿服务
│   │   ├── user_service.py           # 用户服务
│   │   └── vector_store.py           # ChromaDB 向量库
│   ├── models/                       # ORM 模型
│   ├── schemas/                      # Pydantic Schema
│   └── utils/                        # 工具类
│       ├── ai_recommend.py           # AI 推荐 Prompt
│       ├── ai_tryon.py               # AI 试穿封装
│       ├── ai_util.py                # AI 通用工具
│       ├── ai_weather.py             # 高德天气调用
│       └── jwt_util.py               # JWT 工具
│
├── ai-outfit-recommender/            # 前端 (Vue 3 + Vite)
│   ├── index.html
│   ├── vite.config.js                # Vite 配置（含 8000 端口代理）
│   ├── package.json
│   ├── .env.example                  # 前端环境变量模板
│   ├── public/
│   │   └── vite.svg
│   └── src/
│       ├── main.js                   # Vue 入口
│       ├── App.vue                   # 根组件
│       ├── style.css
│       ├── router/index.js           # 路由
│       ├── views/
│       │   ├── HomeView.vue          # 主页（三栏布局）
│       │   └── LoginView.vue         # 登录/注册
│       └── components/
│           ├── UploadInput.vue       # 上传衣物
│           ├── ClosetManager.vue     # 衣橱网格
│           ├── OutfitDisplay.vue     # 试穿展示
│           ├── RoleManager.vue       # 男/女模特切换
│           ├── WeatherWidget.vue     # 天气组件
│           ├── WeatherInput.vue      # 城市输入
│           ├── RecommendationList.vue # 推荐列表
│           └── ChatPanel.vue         # AI 对话面板
│
├── screenshots/                      # README 截图
│   ├── wardrobe.png
│   ├── tryon.png
│   ├── model_male.png                # 男模特底图
│   └── model_female.png              # 女模特底图
│
├── .env.example                      # 全局环境变量模板
├── .gitignore                        # Git 忽略规则
├── 代码审查报告.md                    # 项目代码审查报告
└── 前端对接指南.md                    # 前端对接后端说明
```

---

## 快速开始

### 1. 准备 API Key

注册以下服务并获取 Key：

| 服务 | 用途 | 获取地址 |
|------|------|----------|
| **DashScope**（通义千问）| 多模态识别 / Embedding / 对话 | https://dashscope.console.aliyun.com |
| **高德开放平台** | 天气查询 / IP 定位 | https://lbs.amap.com |
| **火山引擎**（即梦）| 试穿生图（可选）| https://www.volcengine.com |
| **腾讯云 COS** | 衣物图云存储（可选）| https://console.cloud.tencent.com/cos |

### 2. 启动后端

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
cp .env.example .env           # 填入真实 Key
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端

```bash
cd ai-outfit-recommender
npm install
cp .env.example .env           # 填入 VITE_AMAP_KEY
npm run dev
```

### 4. 浏览器访问

打开 http://localhost:5173，注册账号即可使用。

---

## 关键 API 一览

| 方法 | 路径 | 功能 | 鉴权 |
|------|------|------|------|
| POST | `/users/register` | 注册 | 否 |
| POST | `/users/login` | 登录 → 返回 JWT | 否 |
| POST | `/items` | 上传衣物（multipart image） | 是 |
| GET | `/closet/items?page=1&size=1000` | 衣橱列表 | 是 |
| DELETE | `/closet/items?url=xxx` | 删除衣物 | 是 |
| PUT | `/closet/items/name` | 重命名衣物 | 是 |
| GET | `/closet/search?q=xxx` | 语义搜索衣物 | 是 |
| GET | `/recommend?city=上海&purpose=日常` | AI 推荐穿搭 | 是 |
| POST | `/tryon` | 虚拟试穿 `{gender, clothingUrls}` | 是 |
| GET | `/weather?city=上海` | 天气查询 | 否 |
| POST | `/api/chat` | AI 对话 | 是 |
| POST | `/api/chat/stream` | AI 对话 SSE 流 | 是 |
| GET | `/uploads/xxx.jpg` | 静态文件 | 否 |

**统一响应格式：**
```json
{ "code": 1, "message": "success", "data": { ... } }
```

---

## 核心流程

### 衣物上传识别
```
用户上传图片
  → 后端 multipart 接收
  → 可选：上传到腾讯云 COS（持久化）
  → 调用 DashScope qwen-vl-plus 识别
  → 提取 category/color/material 等字段
  → 存 SQLAlchemy（SQLite/MySQL）
  → 写入 ChromaDB 向量索引
  → 返回衣物记录（含 COS URL）
```

### 虚拟试穿
```
用户选衣物 + 选模特
  → 后端加载模特底图（uploads/男.png 或 女.png）
  → 衣物图片 + 模特上传到 DashScope 临时存储
  → 调用 aitryon 异步任务
  → 轮询任务结果（最长 180s）
  → 保存试穿结果到 uploads/tryon_xxx.jpg
  → 返回结果 URL
```

### AI 智能对话
```
用户输入问题
  → 后端加载会话历史（Memory）
  → 调用 LLM（qwen-plus）+ Function Calling
  → LLM 自主决定调工具（查衣橱/查天气/推荐等）
  → 流式返回（SSE）每个 token
  → 前端实时渲染
```

---

## 安全配置

**所有 API Key 都通过 `.env` 注入，不硬编码在源码中。**

`.gitignore` 已排除：
- `backend/.env`、`backend/uploads/`、`backend/data/`（含 ChromaDB 和 SQLite）
- `ai-outfit-recommender/.env`、`node_modules/`、`dist/`
- 所有 `__pycache__/`、`venv/`、`.vscode/`

**部署到生产前必做：**
1. 修改 `JWT_SECRET` 为长随机字符串
2. 高德 API Key 申请时设置**域名白名单**
3. 数据库切换到 MySQL/PostgreSQL
4. 启用 HTTPS

---

## 游客试玩模式

为求职展示/公网 demo 设计，无需注册即可体验完整产品：

- **进入方式**：登录页点击「游客试玩」，或首页在无 token 时自动以游客身份访问。
- **身份隔离**：游客请求带 `X-Guest: 1`，后端映射到演示账号（`demo_user_id`，默认 1）的预置示例衣橱，开箱即有衣物可选。
- **权限边界**：游客可体验 AI 推荐、虚拟试穿、智能搜索、AI 对话、浏览搭配历史；**上传/删除/改名/保存搭配**等写操作一律 `403`，杜绝数据污染与 token 滥用。
- **演示衣橱**：服务启动时 `ensure_demo_closet()` 自动为演示账号预置覆盖全品类的示例衣物（不调用 AI 识别，零 token 消耗）。
- **登录后**：写操作、个人衣橱、个人搭配历史全部恢复。

## 已知限制

- ChromaDB 数据存储在 `data/chroma/`，迁移时需整目录复制
- 高德免费配额：每日 5000 次 IP 定位
- DashScope 试穿模型：约 5-15 秒/次
- 当前试穿模型在「长袖+长裤」等复杂组合上效果待提升

---

## 路线图

- [x] 多模态衣物识别
- [x] 向量语义搜索
- [x] 天气感知推荐
- [x] 虚拟试穿
- [x] AI 多轮对话
- [x] 游客试玩模式（预置示例衣橱 + 匿名身份，进首页即有衣物可体验）
- [x] 衣物搭配历史记录（登录用户可保存/查看/删除搭配）
- [x] 旅行场景打包推荐（胶囊衣橱清单生成）
- [x] 移动端 H5 适配（≤768px 单列可滚动：衣橱→试穿→AI助手，顶栏换行、历史抽屉全屏、衣橱网格降列、试穿图自适应）
- [ ] 多用户社交分享

## 模型与 API Key 策略

**统一使用阿里云 DashScope 单密钥（`DASHSCOPE_API_KEY`）**，覆盖全部 AI 能力：

- 衣物识别：`qwen-vl-plus`（多模态）
- 对话 / 推荐：`qwen-plus` / `qwen-vl`
- 向量语义检索：`text-embedding-v3`
- 虚拟试穿：DashScope `aitryon` 专用试穿模型

> 早期预留的「火山引擎即梦」配置（`VOLC_ACCESS_KEY` 等）已确认未被任何代码调用，已从 `config.py` 与 `.env.example` 中移除。公网 demo 不提供「通义 / 即梦」二选一开关——避免访客被迫持有两套密钥、增加 BYOK 摩擦；如需扩展其他生图供应商，仅在 `backend/utils/ai_tryon.py` 内部替换 provider 即可，对前端无感。

---

## License

MIT License
