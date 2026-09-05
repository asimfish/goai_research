<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import {
  NButton, NConfigProvider, NDialogProvider, NGlobalStyle, NIcon, NLayout, NLayoutContent, NLayoutSider, NMenu, NMessageProvider,
  NNotificationProvider, NTooltip, darkTheme, dateZhCN, zhCN,
} from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import { AddCircleOutline, ExtensionPuzzleOutline, PeopleOutline, SettingsOutline, TimeOutline } from '@vicons/ionicons5'
import { api } from './api'
import type { ConsoleConfig, Role } from './types'
import { roleVisual } from './roles'

const route = useRoute()
const router = useRouter()
const config = ref<ConsoleConfig | null>(null)
const roles = ref<Role[]>([])
const running = ref(0)

const icon = (c: unknown) => () => h(NIcon, null, { default: () => h(c as never) })
const dot = (color: string) => () => h('span', { class: 'role-dot', style: { background: color } })
const menu = computed<MenuOption[]>(() => [
  {
    label: () => h(RouterLink, { to: '/roles' }, { default: () => '角色' }), key: 'roles', icon: icon(PeopleOutline),
    children: roles.value.map((r) => ({
      label: () => h(RouterLink, { to: `/roles/${r.id}` }, { default: () => r.label }), key: `role:${r.id}`, icon: dot(roleVisual(r.id).color),
    })),
  },
  { label: () => h(RouterLink, { to: '/history' }, { default: () => '运行与历史' }), key: 'history', icon: icon(TimeOutline) },
  { label: () => h(RouterLink, { to: '/skills' }, { default: () => '技能与 MCP' }), key: 'skills', icon: icon(ExtensionPuzzleOutline) },
  { label: () => h(RouterLink, { to: '/settings' }, { default: () => '设置' }), key: 'settings', icon: icon(SettingsOutline) },
])
const activeKey = computed(() => {
  if (route.name === 'run') return 'history'
  if (route.name === 'role') return `role:${route.params.id}`
  return String(route.name || 'roles')
})

async function refresh() {
  try {
    const [c, w] = await Promise.all([api.config(), api.workspaces()])
    config.value = c
    running.value = w.workspaces.filter((x) => x.status === 'running').length
  } catch { /* 侧栏状态只是提示 */ }
}
onMounted(async () => {
  refresh(); setInterval(refresh, 10000)
  try { roles.value = (await api.roles()).roles } catch { /* 角色子菜单缺失时主菜单仍可用 */ }
})

const loggedIn = computed(() => (config.value?.codex_login || '').includes('Logged in'))
const themeOverrides = {
  common: {
    primaryColor: '#5b8def', primaryColorHover: '#7aa2f7', primaryColorPressed: '#4a7ad8', primaryColorSuppl: '#5b8def',
    borderRadius: '10px', fontSize: '13px', bodyColor: '#0f1115', cardColor: '#171a21', modalColor: '#171a21', popoverColor: '#1c2028',
    tableColor: '#171a21', inputColor: '#12151b', borderColor: 'rgba(255,255,255,.10)', dividerColor: 'rgba(255,255,255,.10)',
  },
  Layout: { siderColor: '#14161c', color: '#0f1115' },
  Menu: { itemColorActive: 'rgba(91,141,239,.16)', itemColorActiveHover: 'rgba(91,141,239,.22)', itemTextColorActive: '#8fb1ff', itemIconColorActive: '#8fb1ff',
          itemTextColorChildActive: '#8fb1ff', itemIconColorChildActive: '#8fb1ff', itemHeight: '36px' },
  Card: { borderColor: 'rgba(255,255,255,.08)' },
  DataTable: { thColor: '#12151b', tdColor: '#171a21', tdColorStriped: '#14171e', borderColor: 'rgba(255,255,255,.08)' },
}
</script>

<template>
  <NConfigProvider :theme="darkTheme" :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <NGlobalStyle />
    <NMessageProvider><NDialogProvider><NNotificationProvider>
      <NLayout has-sider style="height: 100vh">
        <NLayoutSider bordered :width="216" content-style="display:flex;flex-direction:column;height:100%">
          <div class="brand" @click="router.push('/roles')">
            <span class="logo"><svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 2.5 20.2 7v10L12 21.5 3.8 17V7L12 2.5z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12 7.2 16.2 9.6v4.8L12 16.8 7.8 14.4V9.6L12 7.2z" fill="currentColor" opacity=".9"/></svg></span>
            <div><div class="brand-name">goai research</div><div class="brand-sub">SAGE-Mat 控制台</div></div>
          </div>
          <div style="padding: 0 14px 10px">
            <NButton type="primary" block size="small" @click="router.push('/history?new=1')">
              <template #icon><NIcon><AddCircleOutline /></NIcon></template>发起新研究
            </NButton>
          </div>
          <div style="flex: 1; overflow: auto">
            <NMenu :options="menu" :value="activeKey" :default-expanded-keys="['roles']" :root-indent="18" :indent="14" />
          </div>
          <div class="side-status" v-if="config">
            <NTooltip placement="right"><template #trigger>
              <div class="chip"><span class="dot" :class="loggedIn ? 'ok' : 'warn'" />codex {{ config.codex_version?.replace('codex-cli ', '') || '?' }} · {{ loggedIn ? '已登录' : '未登录' }}</div>
            </template>CODEX_HOME={{ config.codex_home }} · {{ config.codex_login || '未探测' }} · 默认 {{ config.model }} / {{ config.effort }}</NTooltip>
            <NTooltip placement="right"><template #trigger>
              <div class="chip"><span class="dot" :class="config.private_corpus_available ? 'teal' : 'grey'" />{{ config.private_corpus_available ? '私有全库可用' : '仅公开精简语料' }}</div>
            </template>{{ config.private_corpus_roots || config.public_corpus }}</NTooltip>
            <NTooltip placement="right"><template #trigger>
              <div class="chip"><span class="dot" :class="running ? 'blue' : 'grey'" />{{ running ? `${running} 个运行中` : '当前无运行' }}</div>
            </template>由控制台或脚本启动、进程仍存活的工作区数</NTooltip>
          </div>
        </NLayoutSider>
        <NLayoutContent content-style="height: 100vh; overflow: auto">
          <RouterView />
        </NLayoutContent>
      </NLayout>
    </NNotificationProvider></NDialogProvider></NMessageProvider>
  </NConfigProvider>
</template>

<style scoped>
.brand { display: flex; align-items: center; gap: 10px; padding: 16px 18px 12px; cursor: pointer; }
.logo { color: #8fb1ff; display: inline-flex; }
.brand-name { font-weight: 700; font-size: 15px; letter-spacing: .02em; line-height: 1.2; }
.brand-sub { font-size: 11px; color: #8a93a6; margin-top: 2px; }
:deep(.role-dot) { display: inline-block; width: 9px; height: 9px; border-radius: 50%; }
.side-status { padding: 12px 14px 16px; display: flex; flex-direction: column; gap: 6px; border-top: 1px solid rgba(255,255,255,.08); }
.chip { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #c9d1d9; padding: 6px 10px; border: 1px solid rgba(255,255,255,.08); border-radius: 8px; background: rgba(255,255,255,.03); }
.dot { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.dot.ok { background: #63c26b; box-shadow: 0 0 6px #63c26b88; } .dot.warn { background: #f0a020; } .dot.teal { background: #2dd4bf; } .dot.blue { background: #5b8def; box-shadow: 0 0 6px #5b8def88; } .dot.grey { background: #4b5563; }
</style>
