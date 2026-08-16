# AI 智能衣橱 · 移动端 App 版 (Mobile H5)

> 基于多模态大模型的个性化穿搭推荐 + 虚拟试穿 **移动端应用**  
> FastAPI + Vue3 + 通义千问 VL + 即梦生图 · 前端按 9 张移动端设计稿重做

[![Branch](https://img.shields.io/badge/branch-mobile--redesign-pink)](https://github.com/XuHaobot/ai-wardrobe/tree/mobile-redesign)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen)](https://vuejs.org)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

---

## ⚠️ 这是移动端版本

本 README 对应的是 **`mobile-redesign` 分支**，是项目的**移动端 App 化重构版**：
底部 Tab 导航（衣橱 / 试穿 / 助手）、全屏单页流、游客与登录身份隔离、衣物标签编辑等。

- **桌面端（三栏原版）**：在 `main` 分支，README 见 https://github.com/XuHaobot/ai-wardrobe/blob/main/README.md
- **移动端（本版）**：在 `mobile-redesign` 分支，即当前文档所在分支

两个分支并存、互不覆盖。克隆后想看哪版就切哪条分支（`git checkout main` / `git checkout mobile-redesign`）。

---

## 移动端功能一览

底部三个 Tab 导航：

| Tab | 名称 | 内容 |
|-----|------|------|
| 👗 | **衣橱** | 分类筛选、网格浏览、点选衣物去试穿、衣物详情（标签增删改） |
| 🎨 | **试穿** | 男/女模特底图、选衣物一键试穿、试穿结果预览 |
| ✨ | **助手** | 天气卡片、场景入口、AI 穿搭对话推荐 |

二级页面：登录/注册、衣物上传、搭配结果（逐件添加进「我的搭配」）、衣物详情、旅行打包、我的搭配历史。

### 核心交互说明

- **搭配 = 用户自己拼**：AI 推荐的单品逐件显示「＋添加」按钮，你点选后才进入「我的搭配」；添加 ≥1 件后才出现「我的搭配」区块（不预留空方案）。底部「试穿这套 / 保存搭配」都基于你选入的单品。
- **试穿 Tab 图标**：🎨（用户指定）。
- **模特底图**：试穿舞台无结果时直接显示男/女模特底图（`/uploads/男.png`、`/uploads/女.png`），已随仓库提供。
- **衣物标签编辑**：在衣物详情页可新增 / 删除 / 保存标签（登录用户可写，游客仅预览）。
- **衣橱图片完整显示**：`object-fit: contain`，衣物不被裁切。

---

## 游客模式 vs 登录用户（身份隔离）

- **游客试玩**：登录页点「游客试玩」，或首页无 token 时自动以游客身份进入。后端映射到演示账号的预置示例衣橱，开箱即有衣物可体验。
- **权限边界**：游客可体验 AI 推荐、虚拟试穿、智能搜索、浏览搭配历史；**上传 / 删除 / 改标签 / 保存搭配** 等写操作一律 `403`，并提示「游客模式下无法…，请先登录」。
- **登录后**：写操作、个人衣橱、个人搭配历史全部恢复。
- 衣橱 / 历史页顶部有「游客试玩中…」banner 明确当前身份。

---

## 技术架构（移动端部分）

前端用**响应式断点**自动切换桌面 / 移动：

```
HomeView.vue
  ├─ isMobile > 768px  → 原三栏桌面版（与 main 分支一致）
  └─ isMobile ≤ 768px  → MobileApp.vue（本分支新增的移动端壳）
                          ├─ 底部 Tab：衣橱 / 试穿 / 助手
                          └─ provide 共享状态：currentRole / myOutfit / authHeaders / isGuest ...
```

后端与桌面端共用同一套 FastAPI（端口 8000），无需为移动端单独部署后端。

---

## 目录结构（移动端相关）

```
ai-outfit-recommender/src/
├── views/HomeView.vue              # 主页，按 isMobile 断点切换桌面/移动
├── style.css                       # 移动端设计系统（主色 #F05A8C、背景 #F9FAFB 等）
└── components/
    ├── MobileApp.vue               # 移动端壳：底部 Tab + 页面栈 + 共享状态
    ├── MobileLogin.vue             # 登录 / 注册 / 游客（按设计稿去卡片重绘）
    ├── MobileWardrobe.vue          # 衣橱：分类筛选 + 网格 + 选中
    ├── MobileItemDetail.vue        # 衣物详情：大图 + 标签增删改 + 删除
    ├── MobileTryOn.vue             # 试穿：性别切换 + 模特底图 + 试穿
    ├── MobileOutfitResult.vue      # 搭配结果：逐件添加 + 我的搭配
    ├── MobileUpload.vue            # 衣物上传：拍照 / 相册
    ├── MobilePacking.vue           # 旅行打包清单
    ├── MobileHistory.vue           # 我的搭配历史
    └── MobileAssistant.vue         # AI 助手：天气卡 + 场景 + 对话推荐
```

后端关键改动（本分支已含）：
- `backend/models/item.py`：衣物新增 `style` 标签字段
- `backend/database.py`：引擎无关列迁移（SQLite / MySQL 均补 `style` 列）
- `backend/services/closet_service.py`：`update_tags()`
- `backend/routers/closet.py`：`PUT /closet/items/tags`
- `backend/services/recommend_service.py`：修复旅行打包 `get_weather` / `httpx` 缺失导致的崩溃

---

## 快速开始

### 1. 准备 API Key

| 服务 | 用途 | 获取地址 |
|------|------|----------|
| **DashScope**（通义千问）| 多模态识别 / Embedding / 对话 / 试穿 | https://dashscope.console.aliyun.com |
| **高德开放平台** | 天气查询 / IP 定位 | https://lbs.amap.com |

> 仅演示 / 游客试玩可不填 Key：后端走演示账号示例衣橱，AI 增强类功能（识衣、真实推荐、试穿出图）需填 `DASHSCOPE_API_KEY`。

### 2. 启动后端（端口 8000）

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # 填入真实 Key
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端

```bash
cd ai-outfit-recommender
npm install
cp .env.example .env            # 填入 VITE_AMAP_KEY（天气用，可选）
npm run dev
```

### 4. 用手机视图预览

打开 http://localhost:5173 ，切到**移动视图**二选一：

- **浏览器 DevTools 设备模式**：F12 → 点「切换设备工具栏」(Ctrl+Shift+M) → 顶部选 iPhone / Pixel，或手动输 `390 × 844`。
- **真机访问**：手机与电脑同一局域网，浏览器开 `http://<电脑局域网IP>:5173`。

窗口宽度 **≤768px** 时自动渲染移动端 `MobileApp.vue`；拉宽即回到桌面三栏版。

> 💡 **演示衣橱图片已随仓库提供**：`backend/uploads/` 下 16 张示例衣物图与男/女模特底图（`女.png` / `男.png`）已提交进 Git。首次启动 `ensure_demo_closet()` 自动写入演示账号衣橱，无需额外操作即可看到完整界面与模特底图。

---

## 关键 API（移动端调用）

| 方法 | 路径 | 功能 | 游客可用 |
|------|------|------|----------|
| POST | `/users/register` `/users/login` | 注册 / 登录 | 否（游客走 X-Guest） |
| GET | `/closet/items` | 衣橱列表 | ✅（演示衣橱） |
| POST | `/items` | 上传衣物 | ❌ 需登录（游客 403） |
| DELETE | `/closet/items` | 删除衣物 | ❌ 需登录 |
| PUT | `/closet/items/tags` | 编辑标签 | ❌ 需登录 |
| GET | `/recommend` | AI 推荐穿搭 | ✅ |
| POST | `/tryon` | 虚拟试穿 `{gender, clothingUrls}` | ✅ |
| GET | `/recommend/packing` | 旅行打包清单 | ✅ |
| GET | `/outfit/history` | 我的搭配历史 | 登录返回个人，游客返回示例 |

**统一响应格式：** `{ "code": 1, "message": "success", "data": { ... } }`

---

## 常见问题 / 排错

- **衣橱空白 / 裂图**：后端必须跑在 **8000 端口**，与前端 `vite.config.js` 代理 `http://127.0.0.1:8000` 一致；否则衣橱显示 0 件。
- **移动端没出现**：浏览器窗口宽度需 ≤768px（DevTools 设备模式最稳）。
- **试穿无出图**：需在 `.env` 填 `DASHSCOPE_API_KEY`，模特底图已随仓库提供，缺 Key 时仅无试穿出图，其余正常。
- **旅行打包报错**：本分支已修复 `get_weather` / `httpx` 缺失，确保用的是 `mobile-redesign` 分支代码。

---

## 🔄 如何更新并推送到 GitHub（mobile-redesign 分支）

> 你平时改移动端，都在 **`mobile-redesign` 分支** 上操作，不要碰 `main`，这样桌面端原版永远不会被覆盖。

### 本地改完，提交并推送

```bash
# 1. 确认在移动端分支
git branch --show-current          # 应为 mobile-redesign

# 2. 看改动
git status

# 3. 添加改动文件（不要加 dist_bak_*、node_modules、venv）
git add ai-outfit-recommender/src/...   backend/...

# 4. 提交
git commit -m "feat: 移动端 xxx 优化"

# 5. 推到远程移动端分支（只推这个分支，不推 main）
git push origin mobile-redesign
```

### 切回桌面端看看

```bash
git checkout main          # 桌面三栏原版
git checkout mobile-redesign   # 回到移动端
```

### 想让桌面端也同步移动端的某次改动（可选）

```bash
git checkout mobile-redesign
git log --oneline -5               # 复制要同步的 commit hash
git checkout main
git cherry-pick <commit-hash>      # 把那次改动摘到 main
# 或整体合并：git merge mobile-redesign   （合并前请确认有意覆盖桌面端）
```

> ⚠️ **不要** 执行 `git push origin main`，除非你确实想把移动端改动并入桌面端原版。本仓库约定：`main` = 桌面端，`mobile-redesign` = 移动端，各自独立。

### 本机首次拉取已推送的分支

```bash
git fetch
git checkout -b mobile-redesign origin/mobile-redesign   # 首次需关联
```

---

## License

MIT License
