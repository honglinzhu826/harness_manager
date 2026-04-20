# Harness Manager（中文说明）

Harness Manager 是一个开源 GUI 控制台，用于以 **PTY 持久会话** 的方式统一托管多个代码 Agent 的原生 TUI（例如 Codex CLI、Claude Code、Kimi CLI）。

## 核心定位

- 不重写 Agent 协议，不模拟对话 API。
- 直接拉起真实 CLI 的 TUI，会话状态由进程本身持续维护。
- 后端负责会话生命周期、输入输出转发、子会话编排。
- 前端负责会话管理与终端可视化。

## 技术栈

- 后端：Python + FastAPI + ptyprocess
- 前端：React + Vite（统一聊天 UI）

## 仓库结构

- `backend/`：FastAPI 服务、Agent 适配器、PTY 会话管理、子任务编排器
- `frontend/`：React 前端、xterm 终端组件
- `docs/`：架构设计与 skill 契约说明

## 后端启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

如后端地址非默认值，请设置：

```bash
export VITE_API_BASE=http://localhost:8000/api
```

### 统一对话交互

- 在同一个输入区下方选择 Agent、Model 和 CWD。
- 用户首次发送消息时，后端才懒加载创建 PTY 会话。
- 后续消息复用同一后台会话，前端始终保持统一聊天界面。

## MVP API

- `GET /api/agents`
- `POST /api/sessions`
- `GET /api/sessions`
- `POST /api/sessions/{id}/input`
- `GET /api/sessions/{id}/drain`
- `DELETE /api/sessions/{id}`
- `POST /api/orchestrator/jobs`
- `GET /api/orchestrator/jobs/{job_id}`
- `POST /api/orchestrator/jobs/{job_id}/cancel`

## 常见问题

### 1) `npm install` 报错找不到 `xterm-addon-fit`

新版本生态应使用带命名空间的包名：

- `@xterm/xterm`
- `@xterm/addon-fit`

本仓库已切换为上述依赖与对应 import 路径。

### 2) 会话关闭后输入报错

API 会返回可识别的状态码（例如 409），表示会话已关闭，需要重新创建或重连。
