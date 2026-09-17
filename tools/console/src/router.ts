import { createRouter, createWebHashHistory } from 'vue-router'
import RolesView from './views/RolesView.vue'
import HistoryView from './views/HistoryView.vue'
import RunView from './views/RunView.vue'
import SettingsView from './views/SettingsView.vue'
import RoleView from './views/RoleView.vue'
import SkillsView from './views/SkillsView.vue'
import ToolsView from './views/ToolsView.vue'
import ResultsView from './views/ResultsView.vue'
import RunIndexView from './views/RunIndexView.vue'
import CostView from './views/CostView.vue'

// hash 路由：后端是纯静态托管，不需要 SPA 回退规则也能深链接。
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/experiments', name: 'experiments', component: () => import('@materials/views/MaterialsWorkbenchView.vue'), props: { headerTarget: '#page-header-main' }, meta: { title: '材料实验工作台' } },
    { path: '/', redirect: '/roles' },
    { path: '/roles', name: 'roles', component: RolesView, meta: { title: '角色总览' } },
    { path: '/roles/:id', name: 'role', component: RoleView, props: true, meta: { title: '角色详情' } },
    { path: '/skills', name: 'skills', component: SkillsView, meta: { title: '技能' } },
    { path: '/tools', name: 'tools', component: ToolsView, meta: { title: '工具' } },
    { path: '/history', name: 'history', component: HistoryView, meta: { title: '发起研究' } },
    { path: '/run', name: 'runIndex', component: RunIndexView, meta: { title: '运行过程' } },
    { path: '/run/:id', name: 'run', component: RunView, props: true, meta: { title: '运行过程' } },
    { path: '/results', name: 'results', component: ResultsView, meta: { title: '结果预览' } },
    { path: '/settings', name: 'settings', component: SettingsView, meta: { title: '设置' } },
    { path: '/costs', name: 'costs', component: CostView, meta: { title: '算力 / 费用统计' } },
  ],
})
