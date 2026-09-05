# 控制台产品 UI 概念图

2026-09-06 生成的一组网页产品 UI 概念图（AI 生图，文字仅示意），作为控制台视觉方向的参照；实际实现见 `../src/`。

| 图 | 页面 | 落地情况 |
|---|---|---|
| `01-roles.png` | 角色说明：侧栏导航、KPI 统计、阶段状态机、带图标徽章的角色卡 | ✅ `views/RolesView.vue` |
| `02-runs-and-history.png` | 运行与历史：页内「发起新研究」面板、KPI、工作区表（分段闸门进度条、终止 / 实时观察 / PDF） | ✅ `views/HistoryView.vue` + `components/LaunchPanel.vue` |
| `03-run-detail.png` | 运行详情：流程条、批次时间线、按角色分组的任务卡、闸门与 issue、事件流 / 审计 / 产物 / 启动器日志 | ✅ `views/RunView.vue` |
| `04-role-detail.png` | 角色抽屉：角色卡四格、在状态机中的位置、skill 全文 + 工具面 | ✅ `views/RolesView.vue`（NDrawer） |

设计约定：暗色（背景 `#0f1115` / 面板 `#171a21` / 侧栏 `#14161c`），主色 `#5b8def`，每个角色一个固定颜色（`src/roles.ts`），图标用 ionicons 线性图标（不依赖系统 emoji 字体），字号 12–14px，圆角 8px，1px 低对比边框。
