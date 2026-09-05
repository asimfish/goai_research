# goai console（前端）

Vite + Vue 3 + TypeScript + Naive UI。后端是 `tools/console_server.py`（纯标准库，同时托管本目录的 `dist/`）。

```bash
pnpm install
pnpm run dev        # http://127.0.0.1:5173，/api 代理到 GOAI_CONSOLE_API（默认 http://127.0.0.1:5051）
pnpm run build      # vue-tsc 类型检查 + 产物到 dist/（已提交，服务端直接托管，不需要 node）
```

页面：`/#/roles` 首页与角色总览 · `/#/roles/<id>` 角色详情 · `/#/history` 研究（发起 / 最近运行）· `/#/run` 与 `/#/run/<id>` 运行实时观察 · `/#/skills` 技能与工具 · `/#/results` 成果与历史回看 · `/#/settings`。视觉系统见 `design/round3/DESIGN.md`。
数据契约见 `src/types.ts`，与 `console_server.py` / `live_view.py` 的 JSON 一致。
