<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton, NCard, NDataTable, NEmpty, NIcon, NInput, NPopconfirm, NSpace, NTag, NText, NTooltip, useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { CheckmarkCircleOutline, FolderOpenOutline, LayersOutline, PulseOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { ConsoleConfig, WorkspaceInfo } from '../types'
import { WS_STATUS_LABEL, ago, dateTime, statusType } from '../format'
import { GATE_ORDER } from '../roles'
import LaunchPanel from '../components/LaunchPanel.vue'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const rows = ref<WorkspaceInfo[]>([])
const now = ref(Date.now() / 1000)
const loading = ref(true)
const filter = ref('')
const config = ref<ConsoleConfig | null>(null)
let timer: number | undefined

async function refresh() {
  try {
    const r = await api.workspaces()
    rows.value = r.workspaces
    now.value = r.now
  } catch (e) {
    message.error(`读取工作区失败：${(e as Error).message}`)
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
  if (!q) return rows.value
  return rows.value.filter((w) => [w.topic, w.label, w.parent, w.path, w.status, w.stage || ''].join(' ').toLowerCase().includes(q))
})
const kpis = computed(() => [
  { label: '运行中', value: rows.value.filter((w) => w.status === 'running').length, icon: PulseOutline, color: '#5b8def' },
  { label: '已完成', value: rows.value.filter((w) => w.status === 'done').length, icon: CheckmarkCircleOutline, color: '#63c26b' },
  { label: '工作区', value: rows.value.length, icon: FolderOpenOutline, color: '#a78bfa' },
  { label: '子 agent 任务累计', value: rows.value.reduce((a, w) => a + w.tasks, 0), icon: LayersOutline, color: '#e0b060' },
])

async function stop(w: WorkspaceInfo) {
  try {
    const r = await api.stop(w.id)
    r.ok ? message.success(r.message) : message.warning(r.message)
    await refresh()
  } catch (e) {
    message.error(`终止失败：${(e as Error).message}`)
  }
}

const GATE_COLOR: Record<string, string> = { PASS: '#63c26b', WARN: '#f0a020', FAIL: '#f2726f', PENDING: 'rgba(255,255,255,.14)' }
function gateBar(w: WorkspaceInfo) {
  return h('div', { class: 'gates' }, GATE_ORDER.map((g) => {
    const s = w.gates[g] || (g in w.gates ? 'PENDING' : '')
    return h(NTooltip, { key: g }, {
      trigger: () => h('span', { class: 'seg', style: { background: GATE_COLOR[s] || 'rgba(255,255,255,.06)' } }),
      default: () => `${g}: ${s || '未记录'}`,
    })
  }))
}

const columns: DataTableColumns<WorkspaceInfo> = [
  {
    title: '状态', key: 'status', width: 92,
    render: (w) => h(NTag, { size: 'small', type: statusType(w.status), round: true, bordered: false, class: w.status === 'running' ? 'pulse' : '' },
      { default: () => WS_STATUS_LABEL[w.status] || w.status }),
  },
  {
    title: '研究主题', key: 'topic', minWidth: 340,
    render: (w) => h('div', { style: 'cursor:pointer;min-width:0', onClick: () => router.push(`/run/${w.id}`) }, [
      h('div', { class: 'ellipsis', style: 'font-weight:600', title: w.topic }, w.topic || '（无主题记录）'),
      h('div', { class: 'dim mono ellipsis', style: 'font-size:11.5px', title: w.path }, `${w.parent}/${w.label}`),
    ]),
  },
  {
    title: '阶段 / 轮次', key: 'stage', width: 140,
    render: (w) => w.stage ? h('div', [h('span', { class: 'mono' }, w.stage), h('span', { class: 'dim' }, ` · r${w.round}/${w.max_rounds}`)]) : h('span', { class: 'dim' }, '账本未初始化'),
  },
  { title: '闸门（9 个）', key: 'gates', width: 150, render: gateBar },
  { title: '批次 / 任务', key: 'tasks', width: 104, render: (w) => `${w.batches} / ${w.tasks}${w.tasks_running ? ` (▶${w.tasks_running})` : ''}` },
  {
    title: '最近活动', key: 'last_activity', width: 120,
    render: (w) => h(NTooltip, {}, { trigger: () => h('span', ago(w.last_activity, now.value)), default: () => dateTime(w.last_activity) }),
  },
  { title: '创建', key: 'created', width: 112, render: (w) => dateTime(w.created) },
  {
    title: '产物', key: 'final_pdf', width: 84,
    render: (w) => w.final_pdf
      ? h('a', { href: api.pdfUrl(w.id), target: '_blank', style: 'color:#63c26b' }, 'PDF ↗')
      : h('span', { class: 'dim' }, w.open_issues ? `${w.open_issues} open` : '—'),
  },
  {
    title: '操作', key: 'actions', width: 176,
    render: (w) => h(NSpace, { size: 6 }, {
      default: () => [
        h(NButton, { size: 'tiny', type: w.status === 'running' ? 'primary' : 'default', ghost: w.status === 'running', onClick: () => router.push(`/run/${w.id}`) },
          { default: () => w.status === 'running' ? '实时观察' : '回放' }),
        w.status === 'running' && w.launcher.alive
          ? h(NPopconfirm, { onPositiveClick: () => stop(w) }, {
              trigger: () => h(NButton, { size: 'tiny', type: 'error', ghost: true }, { default: () => '终止' }),
              default: () => `向 pid ${w.launcher.pid} 的整个进程组发 SIGTERM（编排器、子 agent、MCP server），8 秒后仍在则 SIGKILL。已落盘的产物与账本保留。`,
            })
          : null,
      ],
    }),
  },
]
</script>

<template>
  <div class="page">
    <div class="page-title">
      <div>
        <h1>运行与历史</h1>
        <NText depth="3">每一行是一个工作区：正式案例、历史运行、控制台新发起的运行都在这里；点主题进入按角色的实时观察 / 回放。</NText>
      </div>
    </div>

    <LaunchPanel :config="config" :focus="!!route.query.new" @launched="(id: string) => router.push(`/run/${id}`)" style="margin-bottom: 14px" />

    <div class="kpis">
      <NCard v-for="k in kpis" :key="k.label" size="small" class="kpi">
        <span class="kpi-icon" :style="{ background: k.color + '22', color: k.color }"><NIcon :size="22"><component :is="k.icon" /></NIcon></span>
        <div><div class="kpi-value">{{ k.value }}</div><div class="kpi-label">{{ k.label }}</div></div>
      </NCard>
      <NCard size="small" class="kpi search">
        <NInput v-model:value="filter" clearable placeholder="按主题 / 目录 / 状态 / 阶段过滤" />
      </NCard>
    </div>

    <NCard size="small" content-style="padding: 0">
      <NDataTable :columns="columns" :data="filtered" :loading="loading" :bordered="false" size="small" :row-key="(w: WorkspaceInfo) => w.id"
        :pagination="{ pageSize: 20 }" striped>
        <template #empty><NEmpty description="还没有任何工作区。在上方发起新研究，或用 --workspace-glob 把历史目录挂进来。" /></template>
      </NDataTable>
    </NCard>
  </div>
</template>

<style scoped>
.kpis { display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)) minmax(280px, 1.6fr); gap: 12px; margin-bottom: 12px; }
.kpi :deep(.n-card__content) { display: flex; align-items: center; gap: 12px; }
.kpi.search :deep(.n-card__content) { display: block; }
.kpi-icon { width: 40px; height: 40px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; flex: none; }
.kpi-value { font-size: 22px; font-weight: 700; line-height: 1.1; } .kpi-label { font-size: 12px; color: #9aa3b5; }
:deep(.gates) { display: flex; gap: 3px; } :deep(.seg) { display: inline-block; width: 12px; height: 8px; border-radius: 2px; }
:deep(.pulse) { animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .55; } }
</style>
