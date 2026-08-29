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

## 🚀 上线前优化记录（2026-08-29，对外演示部署准备）

本轮共改动 16 个文件（+403 / -73 行），构建与接口冒烟测试全部通过。修复了 5 个**实测复现**的部署级致命 Bug，以及一批移动端体验与性能问题。

### 1. 部署级致命 Bug（不修必翻车）

| # | 问题 | 根因 | 修复 |
|---|------|------|------|
| 1 | **AI 功能全部失败**：助手推荐 / 旅行打包 / 上传识别约 10 秒必报错 | `main.js` 全局 fetch 拦截器给所有请求硬加 10s 超时，而后端 LLM 调用需 30~60s | 改为分级超时：AI 类接口（`/recommend` `/tryon` `/items` `/closet/search` `/api/chat` `/weather`）180s，其余 15s；组件自带 `signal` 时不再叠加 |
| 2 | **全新数据库下所有写操作失败**：种子衣物插不进、注册 / 保存搭配报 `NOT NULL constraint failed: closet_items.id` | 三张表主键用 `BigInteger`，MySQL 正常但 **SQLite 仅原生 `INTEGER PRIMARY KEY` 才自增**（本地老库是历史建表，从未暴露） | `models/item.py` `user.py` `outfit_history.py` 主键改 `BigInteger().with_variant(Integer, "sqlite")`；已用全新库验证种子 16 件 / 注册 / 保存搭配全通 |
| 3 | **容器内游客衣橱为空、模特底图 404** | `.dockerignore` 排除了整个 `backend/uploads`（演示衣物图与 `男/女.png` 都在里面），seed 脚本找不到图全部跳过 | 仅排除运行时产物 `backend/uploads/tryon_*`（约 15MB 历史试穿图），演示资产约 3.2MB 照常进镜像；同时显式 `!backend/.env` 保证 DashScope / 高德 Key 进容器 |
| 4 | **打开首页看到一坨 JSON 而非 App** | `@app.get("/")`（API 说明 JSON）注册在 SPA 兜底路由之前，永远优先命中 | 根路径 `/` 让给前端 SPA，API 信息移到 `/api`（兼作健康检查） |
| 5 | **手机首次打开掉进桌面版登录页** | 路由守卫无 token 且无 `guest_mode` 时强制跳 `/login`（Element Plus 桌面页） | 移动端（≤768px 或移动 UA）首次访问自动写入 `guest_mode=1` 以游客身份进入；401 时也静默降级为游客并刷新，不再跳桌面页 |

### 2. 移动端体验优化

- **助手页假天气 → 真天气**：原写死「28°C 广州 晴」；现改为 IP 定位城市（`/api/locate/ip`）→ 后端高德天气（`/weather`，Key 不出后端），含天气图标、穿衣建议、加载态与失败降级重试。推荐请求携带定位城市，天气参与推荐。
- **问候语**：写死的「早上好 Alex」→ 按时间段（早上好 / 中午好 / 下午好 / 晚上好）。
- **长任务预期管理**：AI 推荐（10~40s）、试穿生图（20~90s）、打包清单（30~60s）的 loading 均标注大致耗时，避免误以为卡死。
- **试穿页登录态感知**：登录用户显示「去衣橱选衣物」，游客才显示「登录 / 注册」引导（原来登录了也显示「游客试玩模式」）。
- **推荐结果显示真实衣物名**：助手页预取衣橱，把推荐 URL 映射回衣物名称，不再显示清一色「单品」。
- **登录后清游客缓存**：登录成功即清空游客身份下的衣橱 / 已选 / 我的搭配，避免看到游客数据。
- **细节**：衣橱页加载骨架、衣橱 / 历史页图片懒加载（`loading="lazy"`）。

### 3. 性能优化（手机 4G 首屏）

- `HomeView.vue` 桌面端 10 个组件全部改 `defineAsyncComponent` 异步加载——**移动端不再下载桌面 JS**；
- `vite.config.js` 增加 `manualChunks`：`vue` / `element-plus` 拆成独立稳定 chunk，业务代码迭代后框架缓存仍命中；业务入口 chunk 仅 ~53KB（gzip 18KB）；
- `backend/main.py` 启用 gzip（JS 传输 1MB → ~350KB，`/uploads` 图片跳过压缩省 CPU）；
- `/uploads` 图片增加 `Cache-Control: max-age=604800`，二次打开明显提速。

### 4. 页面基建

- `index.html`：标题改「AI 智能衣橱 · 穿搭推荐与虚拟试穿」、`lang=zh-CN`、新增 `favicon.svg`（粉色渐变 👗）、`viewport-fit=cover`（iPhone 底部安全区生效）、`theme-color`、Apple PWA meta。

### 5. 已验证项

✅ 前端构建通过　✅ `/` 返回 SPA（带 gzip）　✅ `/api` 健康检查　✅ `/login` SPA 回退　✅ 游客衣橱 16 件　✅ 真实天气返回　✅ 全新库种子 / 注册 / 保存搭配全通

### 6. 部署清单（Docker）

```bash
cd E:/aitryon
docker build -t ai-wardrobe:latest .
docker run -d -p 8080:8080 ai-wardrobe:latest
# 自检：
#   1. 浏览器开 http://localhost:8080/ → 应是 App 首页（不是 JSON）
#   2. /uploads/男.png → 模特图正常
#   3. 手机打开 → 自动游客进入助手页，天气卡为真实数据
#   4. 点场景等推荐（30s 内）→ 添加单品 → 试穿这套（90s 内出图）
```

> 已知事项：游客「我的搭配」为 4 条前端示例数据（有文案标注）；`jwt_secret` 仍为默认值，短期演示无碍，长期公网建议更换。

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
