import { createRouter, createWebHashHistory } from 'vue-router'
import RolesView from './views/RolesView.vue'
import HistoryView from './views/HistoryView.vue'
import RunView from './views/RunView.vue'
import SettingsView from './views/SettingsView.vue'
import RoleView from './views/RoleView.vue'
import SkillsMcpView from './views/SkillsMcpView.vue'
import ResultsView from './views/ResultsView.vue'
import RunIndexView from './views/RunIndexView.vue'

// hash 路由：后端是纯静态托管，不需要 SPA 回退规则也能深链接。
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/roles' },
    { path: '/roles', name: 'roles', component: RolesView, meta: { title: '角色' } },
    { path: '/roles/:id', name: 'role', component: RoleView, props: true, meta: { title: '角色详情' } },
    { path: '/skills', name: 'skills', component: SkillsMcpView, meta: { title: '技能与 MCP' } },
    { path: '/history', name: 'history', component: HistoryView, meta: { title: '历史与运行' } },
    { path: '/run', name: 'runIndex', component: RunIndexView, meta: { title: '运行' } },
    { path: '/run/:id', name: 'run', component: RunView, props: true, meta: { title: '运行实时观察' } },
    { path: '/results', name: 'results', component: ResultsView, meta: { title: '成果与历史回看' } },
    { path: '/settings', name: 'settings', component: SettingsView, meta: { title: '设置' } },
  ],
})
