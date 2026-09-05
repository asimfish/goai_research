<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import {
  NConfigProvider, NDialogProvider, NGlobalStyle, NIcon, NLayout, NLayoutContent, NLayoutSider, NMenu, NMessageProvider,
  NNotificationProvider, NTooltip, darkTheme, dateZhCN, zhCN,
} from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import { AddCircleOutline, PeopleOutline, SettingsOutline, TimeOutline } from '@vicons/ionicons5'
import { api } from './api'
import type { ConsoleConfig } from './types'

const route = useRoute()
const router = useRouter()
const config = ref<ConsoleConfig | null>(null)
const running = ref(0)

const icon = (c: unknown) => () => h(NIcon, null, { default: () => h(c as never) })
const menu: MenuOption[] = [
  { label: () => h(RouterLink, { to: '/roles' }, { default: () => '角色说明' }), key: 'roles', icon: icon(PeopleOutline) },
  { label: () => h(RouterLink, { to: '/history' }, { default: () => '运行与历史' }), key: 'history', icon: icon(TimeOutline) },
  { label: () => h(RouterLink, { to: '/history?new=1' }, { default: () => '发起新研究' }), key: 'new', icon: icon(AddCircleOutline) },
  { label: () => h(RouterLink, { to: '/settings' }, { default: () => '设置' }), key: 'settings', icon: icon(SettingsOutline) },
]
const activeKey = computed(() => {
  if (route.name === 'run') return 'history'
  if (route.name === 'history' && route.query.new) return 'new'
  return String(route.name || 'roles')
})

async function refresh() {
  try {
    const [c, w] = await Promise.all([api.config(), api.workspaces()])
    config.value = c
    running.value = w.workspaces.filter((x) => x.status === 'running').length
  } catch { /* 侧栏状态只是提示 */ }
}
onMounted(() => { refresh(); setInterval(refresh, 10000) })

const loggedIn = computed(() => (config.value?.codex_login || '').includes('Logged in'))
const themeOverrides = {
  common: {
    primaryColor: '#5b8def', primaryColorHover: '#7aa2f7', primaryColorPressed: '#4a7ad8', primaryColorSuppl: '#5b8def',
    borderRadius: '8px', fontSize: '13px', bodyColor: '#0f1115', cardColor: '#171a21', modalColor: '#171a21', popoverColor: '#1c2028',
    tableColor: '#171a21', inputColor: '#12151b', borderColor: 'rgba(255,255,255,.10)', dividerColor: 'rgba(255,255,255,.10)',
  },
  Layout: { siderColor: '#14161c', color: '#0f1115' },
  Menu: { itemColorActive: 'rgba(91,141,239,.16)', itemColorActiveHover: 'rgba(91,141,239,.22)', itemTextColorActive: '#8fb1ff', itemIconColorActive: '#8fb1ff' },
  Card: { borderColor: 'rgba(255,255,255,.08)' },
  DataTable: { thColor: '#12151b', tdColor: '#171a21', tdColorStriped: '#14171e', borderColor: 'rgba(255,255,255,.08)' },
}
</script>

<template>
  <NConfigProvider :theme="darkTheme" :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <NGlobalStyle />
    <NMessageProvider><NDialogProvider><NNotificationProvider>
      <NLayout has-sider style="height: 100vh">
        <NLayoutSider bordered :width="212" content-style="display:flex;flex-direction:column;height:100%">
          <div class="brand" @click="router.push('/roles')">
            <span class="logo"><svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 2.5 20.2 7v10L12 21.5 3.8 17V7L12 2.5z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12 7.2 16.2 9.6v4.8L12 16.8 7.8 14.4V9.6L12 7.2z" fill="currentColor" opacity=".9"/></svg></span>
            <div><div class="brand-name">goai research</div><div class="brand-sub">SAGE-Mat 控制台</div></div>
          </div>
          <NMenu :options="menu" :value="activeKey" :root-indent="18" :indent="18" style="flex: 1" />
          <div class="side-status" v-if="config">
            <NTooltip placement="right"><template #trigger>
              <div class="chip"><span class="dot" :class="loggedIn ? 'ok' : 'warn'" />codex {{ config.codex_version?.replace('codex-cli ', '') || '?' }} · {{ loggedIn ? '已登录' : '未登录' }}</div>
            </template>CODEX_HOME={{ config.codex_home }} · {{ config.codex_login || '未探测' }} · 默认 {{ config.model }} / {{ config.effort }}</NTooltip>
            <NTooltip placement="right"><template #trigger>
              <div class="chip"><span class="dot" :class="config.private_corpus_available ? 'teal' : 'grey'" />{{ config.private_corpus_available ? '私有全库可用' : '仅公开精简语料' }}</div>
            </template>{{ config.private_corpus_roots || config.public_corpus }}</NTooltip>
            <NTooltip placement="right"><template #trigger>
              <div class="chip"><span class="dot" :class="running ? 'blue' : 'grey'" />{{ running ? `${running} 个运行中` : '无运行' }}</div>
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
.side-status { padding: 12px 14px 16px; display: flex; flex-direction: column; gap: 6px; border-top: 1px solid rgba(255,255,255,.08); }
.chip { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #c9d1d9; padding: 6px 10px; border: 1px solid rgba(255,255,255,.08); border-radius: 8px; background: rgba(255,255,255,.03); }
.dot { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.dot.ok { background: #63c26b; box-shadow: 0 0 6px #63c26b88; } .dot.warn { background: #f0a020; } .dot.teal { background: #2dd4bf; } .dot.blue { background: #5b8def; box-shadow: 0 0 6px #5b8def88; } .dot.grey { background: #4b5563; }
</style>
