<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NEmpty, NIcon, NInput, NPopconfirm, NTooltip, useMessage } from 'naive-ui'
import { CheckmarkCircleOutline, PauseCircleOutline, SearchOutline, SyncOutline, CloseCircleOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { ConsoleConfig, WorkspaceInfo } from '../types'
import { GATE_ORDER, STAGE_LABEL } from '../roles'
import { ago, dateTime } from '../format'
import LaunchPanel from '../components/LaunchPanel.vue'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const rows = ref<WorkspaceInfo[]>([])
const now = ref(Date.now() / 1000)
const loading = ref(true)
const filter = ref('')
const tab = ref<'all' | 'running' | 'done'>('all')
const config = ref<ConsoleConfig | null>(null)
let timer: number | undefined

async function refresh() {
  try {
    const r = await api.workspaces()
    rows.value = r.workspaces
    now.value = r.now
  } catch (e) {
    message.error(`读取运行失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
}
onMounted(async () => {
  config.value = await api.config().catch(() => null)
  await refresh()
  timer = window.setInterval(refresh, 5000)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

const filtered = computed(() => {
  const q = filter.value.trim().toLowerCase()
  return rows.value.filter((w) => {
    if (tab.value === 'running' && w.status !== 'running') return false
    if (tab.value === 'done' && w.status !== 'done') return false
    if (!q) return true
    return [w.topic, w.label, w.parent, w.status, w.stage || ''].join(' ').toLowerCase().includes(q)
  })
})
function checks(w: WorkspaceInfo) { return GATE_ORDER.filter((g) => ['PASS', 'WARN'].includes(w.gates[g] || '')).length }
function stageNo(w: WorkspaceInfo) { const i = ['intake', 'scoping', 'lit_search', 'style_bank', 'ref_gate', 'taxonomy', 'figures', 'writing', 'ideas', 'review', 'final'].indexOf(w.stage || ''); return i >= 0 ? String(i + 1).padStart(2, '0') : '—' }
function statusText(w: WorkspaceInfo) {
  if (w.status === 'running') return `运行中 · ${stageNo(w)} / 11 ${STAGE_LABEL[w.stage || ''] || ''}`
  if (w.status === 'done') return `已交付 · ${checks(w)} / 9`
  if (w.status === 'stopped') return `已终止 · ${stageNo(w)} / 11 ${STAGE_LABEL[w.stage || ''] || ''}`
  if (w.status === 'failed') return `失败 · ${stageNo(w)} / 11`
  if (w.open_issues) return `待处理意见 · ${w.open_issues} 条`
  return `已结束 · ${stageNo(w)} / 11`
}
function statusKind(w: WorkspaceInfo) { return w.status === 'running' ? 'run' : w.status === 'done' ? 'ok' : w.status === 'failed' ? 'bad' : w.open_issues ? 'warn' : 'wait' }
async function stop(w: WorkspaceInfo) {
  try { const r = await api.stop(w.id); r.ok ? message.success(r.message) : message.warning(r.message); await refresh() }
  catch (e) { message.error(`终止失败：${(e as Error).message}`) }
}
</script>

<template>
  <div class="page">
    <div class="page-title"><div><h1>研究</h1><div class="lead">发起一项研究，或回到最近的运行。</div></div></div>
    <div class="layout">
      <LaunchPanel :config="config" :focus="!!route.query.new" @launched="(id: string) => router.push(`/run/${id}`)" />

      <div class="sheet panel recent">
        <div class="hd">
          <h2 class="serif">最近运行</h2>
          <div class="tools">
            <NInput v-model:value="filter" size="small" clearable placeholder="搜索研究主题" style="width: 200px"><template #prefix><NIcon><SearchOutline /></NIcon></template></NInput>
            <div class="seg">
              <button :class="{ on: tab === 'all' }" @click="tab = 'all'">全部</button>
              <button :class="{ on: tab === 'running' }" @click="tab = 'running'">运行中</button>
              <button :class="{ on: tab === 'done' }" @click="tab = 'done'">已交付</button>
            </div>
          </div>
        </div>
        <div class="list" v-if="filtered.length">
          <div v-for="w in filtered" :key="w.id" class="row" @click="router.push(`/run/${w.id}`)">
            <span class="icon" :class="statusKind(w)">
              <NIcon :size="20">
                <SyncOutline v-if="w.status === 'running'" /><CheckmarkCircleOutline v-else-if="w.status === 'done'" /><CloseCircleOutline v-else-if="w.status === 'failed'" /><PauseCircleOutline v-else />
              </NIcon>
            </span>
            <div class="main">
              <div class="topic ellipsis" :title="w.topic">{{ w.topic || '（无主题记录）' }}</div>
              <div class="meta small dim">
                <span>{{ dateTime(w.created) }}</span>
                <NTooltip><template #trigger><span>· 最近活动 {{ ago(w.last_activity, now) }}</span></template>{{ dateTime(w.last_activity) }}</NTooltip>
                <span class="mono">· {{ w.parent }}/{{ w.label }}</span>
              </div>
            </div>
            <div class="status small"><span class="st-dot" :class="statusKind(w)" />{{ statusText(w) }}</div>
            <div class="act" @click.stop>
              <NButton size="small" quaternary @click="router.push(`/run/${w.id}`)">{{ w.status === 'running' ? '打开观察 ›' : '回放过程 ›' }}</NButton>
              <NButton v-if="w.final_pdf" size="small" quaternary tag="a" :href="api.pdfUrl(w.id)" target="_blank">查看成果 ›</NButton>
              <NPopconfirm v-if="w.status === 'running' && w.launcher.alive" @positive-click="stop(w)">
                <template #trigger><NButton size="small" quaternary type="error">终止</NButton></template>
                将结束编排器、所有子 agent 与 MCP 服务进程；已落盘的产物与账本保留，可回放。
              </NPopconfirm>
            </div>
          </div>
        </div>
        <NEmpty v-else :description="loading ? '加载中…' : '没有匹配的运行'" style="margin: 40px 0" />
        <div class="foot small dim">每次研究都会留下可回放的过程记录与完整成果清单。</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: 5fr 7fr; gap: 24px; align-items: start; }
.recent { padding: 22px 24px; }
.hd { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.hd h2 { margin: 0; font-size: 20px; }
.tools { display: flex; gap: 10px; align-items: center; }
.seg { display: inline-flex; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.seg button { border: 0; background: transparent; padding: 5px 12px; font: inherit; font-size: 13px; color: var(--slate); cursor: pointer; }
.seg button.on { background: var(--verdigris-soft); color: var(--ink); font-weight: 600; }
.list { display: flex; flex-direction: column; gap: 8px; }
.row { display: grid; grid-template-columns: 40px minmax(0, 1fr) 200px auto; gap: 14px; align-items: center; padding: 12px 14px; border: 1px solid var(--line); border-radius: 12px; background: #FBFAF7; cursor: pointer; }
.row:hover { box-shadow: var(--shadow-float); }
.icon { width: 40px; height: 40px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; background: #EFEDE6; color: var(--slate); }
.icon.run { background: var(--verdigris-soft); color: var(--verdigris); } .icon.ok { background: var(--verdigris-soft); color: var(--verdigris); }
.icon.warn { background: var(--amber-soft); color: var(--amber); } .icon.bad { background: var(--cinnabar-soft); color: var(--cinnabar); }
.topic { font-weight: 600; font-size: 14.5px; }
.meta { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 2px; }
.status { color: var(--ink); }
.act { display: flex; gap: 2px; }
.foot { margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line-soft); }
@media (max-width: 1100px) { .layout { grid-template-columns: 1fr; } .row { grid-template-columns: 40px 1fr; } }
</style>
