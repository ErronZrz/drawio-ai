## drawio MCP Server 能力概述

根据已连接的 MCP 服务信息，**drawio MCP Server** 提供了以下 **5 个核心功能**：

| 工具名称 | 功能说明 |
|---------|---------|
| `start_session` | 启动新的绘图会话，自动打开浏览器进行实时预览 |
| `display_diagram` | 从 XML 创建并显示**全新的** draw.io 图表（会替换整个图表） |
| `edit_diagram` | 通过 ID 操作编辑当前图表，支持 `add`（添加）、`update`（更新）、`delete`（删除）单元格 |
| `get_diagram` | 获取当前图表的 XML（从浏览器获取最新状态，包括用户手动编辑的内容） |
| `export_diagram` | 将当前图表导出为 `.drawio` 文件 |

### 详细说明

1. **`start_session`**
   - 启动嵌入式服务器并打开浏览器窗口
   - 实时显示图表更新

2. **`display_diagram`**
   - 输入：有效的 draw.io/mxGraph XML 格式
   - 用于从零开始创建新图表
   - ⚠️ 会**完全替换**当前图表

3. **`edit_diagram`**
   - 支持三种操作：
     - `add`：添加新元素（需提供新的 `cell_id` 和 `new_xml`）
     - `update`：更新现有元素（需先调用 `get_diagram` 获取当前 ID）
     - `delete`：删除元素（只需 `cell_id`）
   - 会自动保留用户在浏览器中的手动修改

4. **`get_diagram`**
   - 返回当前图表的完整 XML
   - 在执行 `update` 或 `delete` 前建议先调用此工具

5. **`export_diagram`**
   - 输入：文件保存路径（如 `./diagram.drawio`）
   - 导出为标准 `.drawio` 格式，可用 draw.io 桌面版或在线版打开

### 典型使用流程

```
start_session → display_diagram → [edit_diagram] → export_diagram
                                       ↑
                              get_diagram（查看当前状态）
```

这个 MCP Server 非常适合用于快速生成和编辑架构图、流程图、示意图等技术文档中的图表！

## 问题

如果我有一个域名、一台个人服务器（已经使用 Caddy 反向代理了多个子域名到一些 Docker Compose 容器上），也有一些 GLM 额度，想要创建一个 drawio 绘图 Web 应用，支持：
- 访问网站时，页面显示一个入口按钮，用户点击则为该用户创建一个 session，并提供让用户查看的 URL；
- 用户可以开始和 GLM 进行对话，表达自己的需求，GLM 执行绘图，用户可以随时通过上一步获取的 URL 查看；
- 用户可以手动修改并要求 GLM 继续修改，直至满意，然后通过网站上的下载功能将 drawio 文件下载到本地（暂不用考虑其他格式的文件导出）。

请帮助我梳理实现步骤。

## 🎨 基于 drawio MCP Server 的 Web 绘图应用实现方案

根据你的需求，我来帮你梳理完整的实现步骤。这个方案将构建一个 **前后端分离** 的 Web 应用，核心是将 drawio MCP Server 能力封装为 Web 服务。

---

## 一、整体架构设计

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户浏览器                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   入口页面    │    │   对话界面    │    │  图表预览页   │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
└─────────┼───────────────────┼───────────────────┼──────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        后端服务 (FastAPI/Flask)                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │ Session 管理  │    │  GLM 对话    │    │ 图表渲染/导出 │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    drawio MCP Server (核心引擎)                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │start_session │    │display/edit  │    │export_diagram│          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、技术栈建议

| 层次 | 技术选型 | 说明 |
|-----|---------|------|
| **前端** | Vue.js + Tailwind CSS | 简洁现代的 UI |
| **后端** | Python FastAPI | 异步支持好，适合流式对话 |
| **AI 对话** | 智谱 GLM API | 你已有额度 |
| **绘图引擎** | drawio MCP Server | 核心能力提供者 |
| **会话存储** | Redis / SQLite | 存储用户 session 和图表数据 |
| **反向代理** | Caddy | 你已有的基础设施 |
| **容器化** | Docker Compose | 便于部署 |

---

## 三、详细实现步骤

### 📦 第一步：项目初始化

```
drawio-web/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 入口
│   │   ├── routers/
│   │   │   ├── session.py       # Session 管理接口
│   │   │   ├── chat.py          # GLM 对话接口
│   │   │   └── diagram.py       # 图表操作接口
│   │   ├── services/
│   │   │   ├── mcp_client.py    # MCP Server 客户端封装
│   │   │   ├── glm_service.py   # GLM API 封装
│   │   │   └── session_manager.py
│   │   └── models/
│   │       └── schemas.py       # Pydantic 数据模型
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Home.vue         # 入口页面
│   │   │   ├── Chat.vue         # 对话界面
│   │   │   └── Preview.vue      # 图表预览
│   │   └── ...
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── Caddyfile                    # 如已在服务器 /etc/caddy 中设置，可直接更新
```

---

### 🔧 第二步：后端核心模块实现

#### 2.1 MCP Client 封装 (`mcp_client.py`)

```python
import subprocess
import json
from typing import Dict, Any

class DrawioMCPClient:
    """封装 drawio MCP Server 调用"""
    
    def __init__(self):
        self.sessions: Dict[str, Any] = {}  # session_id -> session_info
    
    async def start_session(self, session_id: str) -> dict:
        """为用户创建新的绘图会话"""
        # 调用 MCP Server 的 start_session
        # 返回 preview_url
        pass
    
    async def display_diagram(self, session_id: str, xml: str) -> bool:
        """显示/替换整个图表"""
        pass
    
    async def edit_diagram(self, session_id: str, operations: list) -> bool:
        """编辑图表（添加/更新/删除元素）"""
        pass
    
    async def get_diagram(self, session_id: str) -> str:
        """获取当前图表 XML"""
        pass
    
    async def export_diagram(self, session_id: str) -> bytes:
        """导出为 .drawio 文件内容"""
        pass
```

#### 2.2 GLM 服务封装 (`glm_service.py`)

```python
from zhipuai import ZhipuAI

class GLMService:
    """智谱 GLM API 封装"""
    
    SYSTEM_PROMPT = """你是一个专业的图表绘制助手，使用 draw.io 格式。
    用户会描述他们想要的图表，你需要：
    1. 理解用户需求
    2. 生成符合 mxGraph XML 格式的图表代码
    3. 支持增量修改现有图表
    
    输出格式要求：
    - 新建图表时返回完整的 mxGraphModel XML
    - 修改图表时返回操作指令 JSON（add/update/delete）
    """
    
    def __init__(self, api_key: str):
        self.client = ZhipuAI(api_key=api_key)
    
    async def chat(self, user_message: str, current_diagram_xml: str = None) -> dict:
        """
        与 GLM 对话，返回绘图指令
        返回: {"action": "display" | "edit", "data": xml_or_operations}
        """
        pass
```

#### 2.3 API 路由设计

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/api/session` | POST | 创建新会话，返回 session_id 和 preview_url |
| `/api/session/{id}` | GET | 获取会话状态 |
| `/api/chat/{session_id}` | POST | 发送消息给 GLM，流式返回 |
| `/api/diagram/{session_id}` | GET | 获取当前图表 XML |
| `/api/diagram/{session_id}/download` | GET | 下载 .drawio 文件 |

---

### 🎨 第三步：前端页面实现

#### 3.1 入口页面 (`Home.vue`)

```vue
<template>
  <div class="flex flex-col items-center justify-center min-h-screen">
    <h1 class="text-3xl font-bold mb-8">AI 绘图助手</h1>
    <button @click="createSession" class="btn-primary">
      开始绘图
    </button>
  </div>
</template>

<script setup>
const createSession = async () => {
  const res = await fetch('/api/session', { method: 'POST' })
  const { session_id, preview_url } = await res.json()
  // 跳转到对话页面，同时打开预览窗口
  window.open(preview_url, '_blank')
  router.push(`/chat/${session_id}`)
}
</script>
```

#### 3.2 对话界面 (`Chat.vue`)

- 左侧：聊天消息列表 + 输入框
- 右侧：嵌入的 iframe 预览（或提供跳转链接）
- 底部：下载按钮

#### 3.3 预览页面

直接使用 drawio MCP Server 提供的预览 URL（如 `http://localhost:6002?mcp=session_id`）

---

### 🐳 第四步：Docker Compose 部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8005:8005"
    environment:
      - GLM_API_KEY=${GLM_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - drawio-mcp
  
  frontend:
    build: ./frontend
    ports:
      - "3005:80"
  
  drawio-mcp:
    image: node:18
    command: npx @next-ai-drawio/mcp-server@latest
    ports:
      - "6002:6002"
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

---

### 🌐 第五步：Caddy 反向代理配置

```caddyfile
# Caddyfile
drawio.yourdomain.com {
    # 前端
    handle / {
        reverse_proxy frontend:3005
    }
    
    # 后端 API
    handle /api/* {
        reverse_proxy backend:8005
    }
    
    # drawio 预览
    handle /preview/* {
        reverse_proxy drawio-mcp:6002
    }
}
```

---

## 四、关键技术难点与解决方案

| 难点 | 解决方案 |
|-----|---------|
| **MCP Server 多会话支持** | 为每个用户启动独立的 MCP 进程，或修改 MCP Server 支持多会话 |
| **GLM 生成有效的 mxGraph XML** | 在 Prompt 中提供 XML 模板和示例，做好输出格式校验 |
| **实时预览同步** | 使用 WebSocket 推送图表更新事件 |
| **会话持久化** | Redis 存储会话状态，支持断线重连 |

---

## 五、开发优先级建议

1. **P0 - MVP 核心功能**
   - [ ] 后端 MCP Client 封装
   - [ ] GLM 对话 + 图表生成
   - [ ] 基础前端页面

2. **P1 - 完整体验**
   - [ ] 会话管理（创建/恢复）
   - [ ] 下载功能
   - [ ] Docker 部署

3. **P2 - 优化增强**
   - [ ] 流式对话响应
   - [ ] 历史记录保存
   - [ ] 多种图表模板

---

## 六、下一步行动

你想先从哪个部分开始实现？我可以帮你：

1. **搭建项目骨架** - 生成完整的项目目录和基础代码
2. **实现 MCP Client** - 封装 drawio MCP Server 的 Python 客户端
3. **设计 GLM Prompt** - 优化提示词以生成高质量的 mxGraph XML
4. **编写 Docker Compose** - 完整的部署配置

请告诉我你的优先级，我们逐步推进！

---

## 七、项目进展记录

### ✅ 已完成（2024-12-18）

#### 1. 应用骨架搭建

**后端 (FastAPI)**
- `backend/app/main.py` - FastAPI 入口，配置 CORS，自动加载根目录 `.env`
- `backend/app/routers/session.py` - 会话管理 API
- `backend/app/routers/chat.py` - GLM 对话 API（流式响应）
- `backend/app/routers/diagram.py` - 图表操作 API
- `backend/app/services/session_manager.py` - 会话管理器
- `backend/app/services/glm_service.py` - GLM 服务封装（OpenAI 兼容接口）
- `backend/app/services/mcp_client.py` - MCP 客户端封装
- `backend/app/models/schemas.py` - Pydantic 数据模型
- `backend/requirements.txt` - Python 依赖

**前端 (Vue 3 + Vite)**
- `frontend/src/views/Home.vue` - 入口页面
- `frontend/src/views/Chat.vue` - 对话界面
- `frontend/src/views/Preview.vue` - 图表预览页
- `frontend/src/router/index.js` - 路由配置
- `frontend/src/App.vue` - 根组件
- `frontend/src/style.css` - Tailwind CSS

**部署配置**
- `docker-compose.yml` - 容器编排
- `Caddyfile` - 反向代理配置
- `.env` / `.env.example` - 环境变量配置（统一放在根目录）

#### 2. API Key 验证

- ✅ 创建测试脚本 `backend/tests/test_glm_api.py`
- ✅ 配置智谱 Coding API（OpenAI 兼容模式）
  - Base URL: `https://open.bigmodel.cn/api/coding/paas/v4`
  - 模型: `codegeex-4`
  - **注意**：GLM Coding 套餐使用 OpenAI 兼容接口，专门用于编程需求。
- ✅ 解决 SSL 验证问题（适配 Whistle 代理）
- ✅ API 连接测试通过
- ✅ 图表 XML 生成测试通过

#### 3. 启动脚本

- ✅ 创建 `start.sh` 一键启动脚本
  - 自动检查环境依赖
  - 同时启动前后端服务
  - 支持 Ctrl+C 优雅停止

#### 4. MCP Server 集成（2024-12-18）

- ✅ 更新 MCP Server 配置为 `@next-ai-drawio/mcp-server@latest`
- ✅ MCP 客户端测试全部通过（6/6）
  - 连接测试 ✓
  - 启动会话测试 ✓
  - 显示图表测试 ✓
  - 获取图表测试 ✓
  - 编辑图表测试 ✓
  - 导出图表测试 ✓

#### 5. GLM Prompt 优化（2024-12-18）

- ✅ 重新设计系统提示词，支持对话 + 绘图双重能力
- ✅ 添加意图识别机制，区分闲聊和画图需求
- ✅ 丰富图表生成模板和样式示例
- ✅ 优化交互引导，提升用户体验

#### 6. 前后端联调（2024-12-18）

- ✅ 统一环境配置到根目录 `.env`
- ✅ 修复 Home.vue 重复打开预览窗口问题
- ✅ 修复 ChatMessage 对象属性访问错误
- ✅ 修复 httpx 代理干扰问题（禁用代理设置）
- ✅ 端口配置调整：后端 8005，前端 3005
- ✅ 简单绘图功能测试通过

---

### 📋 后续规划

#### 阶段一：本地开发环境完善 (P0) ✅ 已完成

| 任务 | 说明 | 状态 |
|-----|------|------|
| 后端服务调试 | 启动 FastAPI，验证各接口 | ✅ 完成 |
| 前端服务调试 | 启动 Vite，验证页面渲染 | ✅ 完成 |
| 前后端联调 | 测试完整用户流程 | ✅ 完成 |

#### 阶段二：核心功能实现 (P0) ✅ 基本完成

| 任务 | 说明 | 状态 |
|-----|------|------|
| MCP 客户端通信 | 实现与 drawio MCP Server 的真实通信 | ✅ 完成 |
| GLM Prompt 优化 | 设计高质量的图表生成提示词 | ✅ 完成 |
| 图表预览集成 | 将 MCP Server 预览页面集成到前端 | ✅ 完成 |
| 下载功能 | 实现 .drawio 文件导出下载 | 待开始 |

#### 阶段三：部署上线 (P1)

| 任务 | 说明 | 状态 |
|-----|------|------|
| Docker 镜像构建 | 构建前后端 Docker 镜像 | 待开始 |
| Docker Compose 部署 | 在服务器上部署完整应用 | 待开始 |
| Caddy 配置 | 配置子域名反向代理 | 待开始 |
| HTTPS 证书 | Caddy 自动申请 Let's Encrypt 证书 | 待开始 |

#### 阶段四：体验优化 (P2)

| 任务 | 说明 | 状态 |
|-----|------|------|
| 流式响应优化 | GLM 对话流式输出到前端 | 待开始 |
| 会话持久化 | Redis 存储会话，支持断线重连 | 待开始 |
| UI 美化 | 优化交互体验和视觉效果 | 待开始 |
| 图表模板 | 提供常用图表模板快速开始 | 待开始 |

---

### 🚀 下一步建议

**当前可用：**

```bash
# 1. 启动应用
./start.sh

# 2. 访问服务
# - 前端: http://localhost:3005
# - 后端 API 文档: http://localhost:8005/docs
```

**优先处理：**
1. 实现下载功能，完成核心功能闭环
2. 继续优化 GLM Prompt，提升图表生成质量
3. 准备 Docker 部署配置