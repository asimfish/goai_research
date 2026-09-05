import { createRouter, createWebHashHistory } from 'vue-router'
import RolesView from './views/RolesView.vue'
import HistoryView from './views/HistoryView.vue'
import RunView from './views/RunView.vue'

// hash 路由：后端是纯静态托管，不需要 SPA 回退规则也能深链接。
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/roles' },
    { path: '/roles', name: 'roles', component: RolesView, meta: { title: '角色说明' } },
    { path: '/history', name: 'history', component: HistoryView, meta: { title: '历史与运行' } },
    { path: '/run/:id', name: 'run', component: RunView, props: true, meta: { title: '运行详情' } },
  ],
})
