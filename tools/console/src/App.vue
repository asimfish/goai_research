<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import {
  NConfigProvider, NDialogProvider, NGlobalStyle, NIcon, NMessageProvider, NNotificationProvider, NTooltip, dateZhCN, zhCN,
} from 'naive-ui'
import { DocumentTextOutline, ExtensionPuzzleOutline, PeopleOutline, PulseOutline, ReaderOutline, SettingsOutline } from '@vicons/ionicons5'
import { api } from './api'
import type { ConsoleConfig, WorkspaceInfo } from './types'
import { WS_STATUS_LABEL } from './format'
import { STAGE_LABEL } from './roles'

const route = useRoute()
const router = useRouter()
const config = ref<ConsoleConfig | null>(null)
const workspaces = ref<WorkspaceInfo[]>([])
const services = ref<{ online: number; total: number } | null>(null)
let timer: number | undefined

const nav = [
  { key: 'roles', to: '/roles', label: '角色', icon: PeopleOutline, match: ['roles', 'role'] },
  { key: 'history', to: '/history', label: '研究', icon: ReaderOutline, match: ['history'] },
  { key: 'run', to: '/run', label: '运行', icon: PulseOutline, match: ['run', 'runIndex'] },
  { key: 'skills', to: '/skills', label: '技能', icon: ExtensionPuzzleOutline, match: ['skills'] },
  { key: 'results', to: '/results', label: '成果', icon: DocumentTextOutline, match: ['results'] },
]
const activeKey = computed(() => nav.find((n) => n.match.includes(String(route.name)))?.key || '')

/** 顶部上下文条里的“当前研究”：运行中的优先，否则最近一次 */
const current = computed<WorkspaceInfo | null>(() => {
  const running = workspaces.value.find((w) => w.status === 'running')
  return running || workspaces.value.find((w) => w.topic) || null
})
const running = computed(() => workspaces.value.filter((w) => w.status === 'running').length)
const loggedIn = computed(() => (config.value?.codex_login || '').includes('Logged in'))

async function refresh() {
  try {
    const [c, w, m] = await Promise.all([api.config(), api.workspaces(), api.mcp().catch(() => ({ servers: [] }))])
    config.value = c
    workspaces.value = w.workspaces
    services.value = { online: m.servers.filter((s) => s.exists).length, total: m.servers.length || 4 }
  } catch { /* 上下文条只是提示 */ }
}
onMounted(() => { refresh(); timer = window.setInterval(refresh, 10000) })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

const themeOverrides = {
  common: {
    primaryColor: '#172B3A', primaryColorHover: '#24405A', primaryColorPressed: '#0F1E2A', primaryColorSuppl: '#2D7468',
    successColor: '#2D7468', warningColor: '#B98032', errorColor: '#A94D45', infoColor: '#2D7468',
    textColorBase: '#172B3A', textColor1: '#172B3A', textColor2: '#2F3F4A', textColor3: '#66737B',
    bodyColor: '#F5F3ED', cardColor: '#FBFAF7', modalColor: '#FBFAF7', popoverColor: '#FBFAF7', tableColor: '#FBFAF7', inputColor: '#FFFFFF',
    borderColor: '#D8DAD6', dividerColor: '#E7E8E3', borderRadius: '10px', borderRadiusSmall: '8px', fontSize: '14px', fontSizeSmall: '13px',
    fontFamily: 'Inter, "Noto Sans SC", "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
  },
  Card: { borderRadius: '12px', color: '#FBFAF7', borderColor: '#D8DAD6', titleFontSizeSmall: '15px', paddingSmall: '16px 20px' },
  Button: { borderRadiusMedium: '10px', borderRadiusSmall: '8px', fontWeight: '500' },
  Tag: { borderRadius: '999px' },
  DataTable: { thColor: '#F1EFE8', tdColor: '#FBFAF7', tdColorStriped: '#F7F5EF', borderColor: '#E7E8E3', thTextColor: '#66737B', thFontWeight: '500' },
  Drawer: { color: '#FBFAF7' },
  Tabs: { tabTextColorLine: '#66737B', tabTextColorActiveLine: '#172B3A', barColor: '#2D7468' },
  Progress: { fillColor: '#2D7468', railColor: '#E7E8E3' },
}
</script>

<template>
  <NConfigProvider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <NGlobalStyle />
    <NMessageProvider><NDialogProvider><NNotificationProvider>
      <div class="shell">
        <nav class="rail">
          <RouterLink to="/roles" class="brand" title="循证台 · goai research">
            <svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true">
              <path d="M9 24 21 6l2 2-12 18z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
              <path d="M6 26h16" stroke="currentColor" stroke-width="1.6"/><circle cx="23.5" cy="7.5" r="2.2" fill="none" stroke="currentColor" stroke-width="1.4"/>
            </svg>
            <span class="brand-name serif">循证台</span>
          </RouterLink>
          <div class="items">
            <RouterLink v-for="n in nav" :key="n.key" :to="n.to" class="item" :class="{ active: activeKey === n.key }">
              <NIcon :size="22"><component :is="n.icon" /></NIcon>
              <span>{{ n.label }}</span>
              <span v-if="n.key === 'run' && running" class="badge">{{ running }}</span>
            </RouterLink>
          </div>
          <div class="rail-foot">
            <NTooltip placement="right"><template #trigger>
              <RouterLink to="/settings" class="item mini" :class="{ active: route.name === 'settings' }"><NIcon :size="20"><SettingsOutline /></NIcon></RouterLink>
            </template>设置 · 服务端配置</NTooltip>
          </div>
        </nav>
        <div class="body">
          <header class="ctx">
            <div class="ctx-left">
              <template v-if="current">
                <span class="st-dot" :class="current.status === 'running' ? 'run' : current.status === 'done' ? 'ok' : current.status === 'failed' ? 'bad' : 'wait'" />
                <RouterLink :to="`/run/${current.id}`" class="ctx-topic ellipsis" :title="current.topic">{{ current.topic }}</RouterLink>
                <span class="dim small">· {{ WS_STATUS_LABEL[current.status] || current.status }}<template v-if="current.stage"> · {{ STAGE_LABEL[current.stage] || current.stage }}</template></span>
              </template>
              <span v-else class="dim small">尚无研究运行 —— 去「研究」发起一项</span>
            </div>
            <div class="ctx-right small">
              <NTooltip><template #trigger>
                <span><span class="st-dot" :class="services && services.online === services.total ? 'ok' : 'warn'" />{{ services ? `${services.online} 项服务在线` : '服务状态…' }}</span>
              </template>四个 MCP 服务（文献检索 / 引用核查 / 图纸 / 逆合成）的源码是否就位</NTooltip>
              <NTooltip v-if="config"><template #trigger>
                <span><span class="st-dot" :class="loggedIn ? 'ok' : 'warn'" />Codex {{ loggedIn ? '已登录' : '未登录' }}</span>
              </template>{{ config.codex_version }} · CODEX_HOME={{ config.codex_home }} · 默认 {{ config.model }} / {{ config.effort }}</NTooltip>
              <NTooltip v-if="config"><template #trigger>
                <span><span class="st-dot" :class="config.private_corpus_available ? 'ok' : 'wait'" />{{ config.private_corpus_available ? '私有全库可用' : '公开精简语料' }}</span>
              </template>{{ config.private_corpus_roots || config.public_corpus }}</NTooltip>
            </div>
          </header>
          <main class="content"><RouterView /></main>
        </div>
      </div>
    </NNotificationProvider></NDialogProvider></NMessageProvider>
  </NConfigProvider>
</template>

<style scoped>
.shell { display: flex; height: 100vh; }
.rail { width: 88px; flex: none; background: var(--mist); border-right: 1px solid var(--line); display: flex; flex-direction: column; align-items: center; padding: 18px 0 14px; }
.brand { display: flex; flex-direction: column; align-items: center; gap: 6px; color: var(--ink); text-decoration: none; margin-bottom: 22px; }
.brand-name { font-size: 15px; font-weight: 600; letter-spacing: .12em; }
.items { display: flex; flex-direction: column; gap: 6px; width: 100%; padding: 0 10px; flex: 1; }
.item { position: relative; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 10px 0 8px; border-radius: 12px; color: var(--slate); text-decoration: none; font-size: 12.5px; }
.item:hover { background: #EFEDE6; color: var(--ink); }
.item.active { background: var(--verdigris-soft); color: var(--ink); font-weight: 600; }
.item.mini { padding: 8px 0; }
.badge { position: absolute; top: 6px; right: 12px; background: var(--verdigris); color: #fff; border-radius: 999px; font-size: 10px; line-height: 16px; padding: 0 5px; }
.rail-foot { width: 100%; padding: 0 10px; border-top: 1px solid var(--line-soft); padding-top: 10px; }
.body { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.ctx { height: 64px; flex: none; display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 0 40px; border-bottom: 1px solid var(--line); background: var(--paper); }
.ctx-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
.ctx-topic { color: var(--ink); text-decoration: none; font-weight: 600; max-width: 520px; }
.ctx-topic:hover { text-decoration: underline; }
.ctx-right { display: flex; gap: 22px; color: var(--slate); white-space: nowrap; }
.content { flex: 1; overflow: auto; }
</style>
