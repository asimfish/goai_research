<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import {
  NConfigProvider, NDialogProvider, NGlobalStyle, NIcon, NMessageProvider, NNotificationProvider, NTooltip, dateZhCN, zhCN,
} from 'naive-ui'
import { DocumentTextOutline, PeopleOutline, ReaderOutline, SettingsOutline } from '@vicons/ionicons5'
import { api } from './api'
import type { ConsoleConfig, WorkspaceInfo } from './types'

const route = useRoute()
const config = ref<ConsoleConfig | null>(null)
const workspaces = ref<WorkspaceInfo[]>([])
const services = ref<{ online: number; total: number } | null>(null)
let timer: number | undefined

const nav = [
  { key: 'capabilities', to: '/roles', label: '角色与技能', icon: PeopleOutline, match: ['roles', 'role', 'skills', 'tools'] },
  { key: 'research', to: '/history', label: '研究工作台', icon: ReaderOutline, match: ['history', 'run', 'runIndex', 'experiments', 'costs'] },
  { key: 'results', to: '/results', label: '结果预览', icon: DocumentTextOutline, match: ['results'] },
]
const activeKey = computed(() => nav.find((n) => n.match.includes(String(route.name)))?.key || '')
interface SectionLink { to: string; label: string; match: string[] }
const sectionLinks: Record<string, SectionLink[]> = {
  capabilities: [
    { to: '/roles', label: '角色总览', match: ['roles', 'role'] },
    { to: '/skills', label: '技能', match: ['skills'] },
    { to: '/tools', label: '工具', match: ['tools'] },
  ],
  research: [
    { to: '/history', label: '发起研究', match: ['history'] },
    { to: '/run', label: '运行过程', match: ['run', 'runIndex'] },
    { to: '/experiments', label: '实验执行', match: ['experiments'] },
    { to: '/costs', label: '费用', match: ['costs'] },
  ],
}
const lastRunPath = ref('/run')
watch(() => route.fullPath, () => {
  if (route.name === 'run') lastRunPath.value = route.path
}, { immediate: true })
function sectionTarget(link: SectionLink) {
  if (link.to === '/run') return lastRunPath.value
  if (link.to === '/skills' && route.name === 'role') return { path: link.to, query: { role: String(route.params.id) } }
  return link.to
}

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
    fontFamily: 'var(--font-sans)', fontFamilyMono: 'var(--font-mono)',
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
      <div class="shell" :class="{ 'cost-page': route.name === 'costs' }">
        <nav class="rail" aria-label="主导航">
          <RouterLink to="/roles" class="brand" title="循证台 · goai research">
            <svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true">
              <path d="M9 24 21 6l2 2-12 18z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
              <path d="M6 26h16" stroke="currentColor" stroke-width="1.6"/><circle cx="23.5" cy="7.5" r="2.2" fill="none" stroke="currentColor" stroke-width="1.4"/>
            </svg>
            <span class="brand-name">循证台</span>
          </RouterLink>
          <div class="items">
            <div v-for="n in nav" :key="n.key" class="nav-group" :class="{ 'group-active': activeKey === n.key }">
              <RouterLink :id="`nav-${n.key}`" :to="n.to" class="item" :class="{ 'group-title': !!sectionLinks[n.key], active: !sectionLinks[n.key] && activeKey === n.key }" :aria-current="!sectionLinks[n.key] && activeKey === n.key ? 'page' : undefined">
                <NIcon :size="22"><component :is="n.icon" /></NIcon>
                <span>{{ n.label }}</span>
                <span v-if="n.key === 'research' && running" class="badge">{{ running }}</span>
              </RouterLink>
              <div v-if="sectionLinks[n.key]" class="submenu" role="group" :aria-labelledby="`nav-${n.key}`">
                <RouterLink v-for="link in sectionLinks[n.key]" :key="link.to" :to="sectionTarget(link)" class="subitem" :class="{ active: link.match.includes(String(route.name)) }" :aria-current="link.match.includes(String(route.name)) ? 'page' : undefined">
                  {{ link.label }}
                </RouterLink>
              </div>
            </div>
          </div>
          <div class="rail-foot">
            <NTooltip placement="right"><template #trigger>
              <RouterLink to="/settings" class="item mini" :class="{ active: route.name === 'settings' }" :aria-current="route.name === 'settings' ? 'page' : undefined" aria-label="设置"><NIcon :size="20"><SettingsOutline /></NIcon></RouterLink>
            </template>设置 · 服务端配置</NTooltip>
          </div>
        </nav>
        <div class="body">
          <header class="ctx">
            <div id="page-header-main" class="ctx-main">
              <h1 v-if="route.name !== 'experiments'" class="ctx-title">{{ route.meta.title || '循证台' }}</h1>
              <div id="page-header-actions" class="ctx-actions" />
            </div>
            <div class="ctx-right small">
              <NTooltip><template #trigger>
                <span><span class="st-dot" :class="services && services.online === services.total ? 'ok' : 'warn'" />{{ services ? `${services.online} 项服务在线` : '服务状态…' }}</span>
              </template>四个 MCP 服务（文献检索 / 引用核查 / 图纸 / 逆合成）的源码是否就位</NTooltip>
              <NTooltip v-if="config"><template #trigger>
                <span class="codex-status" :class="{ ready: loggedIn }" :aria-label="loggedIn ? 'Codex 已登录' : 'Codex 未登录'" tabindex="0"><span class="st-dot" :class="loggedIn ? 'ok' : 'warn'" />Codex<template v-if="!loggedIn"> 未登录</template></span>
              </template>{{ config.codex_version }} · {{ config.codex_email || '未读到账号' }} · CODEX_HOME={{ config.codex_home }} · 默认 {{ config.model }} / {{ config.effort }}<template v-if="config.model_fallback"> · 备用 {{ config.model_fallback }}</template><template v-if="config.proxy"> · 代理 {{ config.proxy }}</template></NTooltip>
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
.shell { display: flex; height: 100vh; height: 100dvh; overflow: hidden; }
.rail { width: 80px; box-sizing: border-box; flex: none; background: var(--mist); border-right: 1px solid var(--line); display: flex; flex-direction: column; align-items: center; padding: 18px 0 14px; }
.brand { display: flex; flex-direction: column; align-items: center; gap: 6px; color: var(--ink); text-decoration: none; margin-bottom: 14px; flex: none; }
.brand-name { font-size: 15px; font-weight: 600; letter-spacing: .12em; }
.items { display: flex; flex-direction: column; gap: 14px; width: 100%; box-sizing: border-box; padding: 0 4px; flex: 1; min-height: 0; overflow-y: auto; overflow-x: hidden; overscroll-behavior-y: contain; scrollbar-width: thin; scrollbar-color: #bec7c5 transparent; }
.items::-webkit-scrollbar { width: 3px; }
.items::-webkit-scrollbar-track { background: transparent; }
.items::-webkit-scrollbar-thumb { background: #bec7c5; border-radius: 999px; }
.items::-webkit-scrollbar-button { display: none; width: 0; height: 0; }
@supports selector(::-webkit-scrollbar) { .items { scrollbar-width: auto; scrollbar-color: auto; } }
.nav-group { flex: none; min-width: 0; }
.item { position: relative; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 10px 0 8px; border-radius: 12px; color: var(--slate); text-decoration: none; font-size: 12.5px; white-space: nowrap; }
.item:hover { background: #EFEDE6; color: var(--ink); }
.item.active { background: var(--verdigris-soft); color: var(--ink); font-weight: 600; }
.group-title { padding-bottom: 6px; font-weight: 600; }
.group-active > .group-title { color: var(--ink); }
.submenu { display: flex; flex-direction: column; gap: 2px; padding: 2px 0 4px; }
.subitem { position: relative; display: flex; align-items: center; justify-content: center; box-sizing: border-box; min-height: 32px; padding: 7px 0; border-radius: 7px; color: var(--slate); text-decoration: none; font-size: 12px; line-height: 18px; white-space: nowrap; }
.subitem:hover { background: #EFEDE6; color: var(--ink); }
.subitem.active { background: var(--verdigris-soft); color: var(--ink); font-weight: 600; }
.subitem.active::before { content: ''; position: absolute; left: 3px; width: 2px; height: 12px; border-radius: 2px; background: var(--verdigris); }
.item:focus-visible, .subitem:focus-visible { outline: 2px solid var(--verdigris); outline-offset: -2px; }
.item.mini { padding: 8px 0; }
.badge { position: absolute; top: 6px; right: 12px; background: var(--verdigris); color: #fff; border-radius: 999px; font-size: 10px; line-height: 16px; padding: 0 5px; }
.rail-foot { width: 100%; box-sizing: border-box; padding: 0 6px; border-top: 1px solid var(--line-soft); padding-top: 10px; flex: none; }
.body { flex: 1; min-width: 0; min-height: 0; display: flex; flex-direction: column; }
.ctx { min-height: 64px; box-sizing: border-box; flex: none; display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 10px 24px; border-bottom: 1px solid var(--line); background: var(--paper); }
.ctx-main { display: flex; align-items: center; gap: 18px; flex: 1; min-width: 0; }
.ctx-title { margin: 0; font-size: 21px; line-height: 30px; font-weight: 650; white-space: nowrap; flex: none; }
.ctx-actions { display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex: 1; min-width: 0; }
.ctx-actions:empty { display: none; }
.ctx-right { display: flex; gap: 16px; margin-left: auto; color: var(--slate); white-space: nowrap; flex: none; }
.codex-status.ready { color: var(--verdigris); }
.content { flex: 1; min-height: 0; overflow: hidden; }
@media (max-width: 1200px) { .ctx-right > :last-child { display: none; } }
@media (max-width: 1050px) { .ctx-right > :first-child { display: none; }.ctx { gap: 12px; padding-inline: 16px; }.ctx-title { font-size: 19px; }.ctx-main { gap: 12px; } }
@media (max-width: 700px) { .ctx-right { display: none; }.ctx-main { flex-wrap: wrap; }.ctx-actions { justify-content: flex-start; flex-wrap: wrap; } }
</style>
