<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton, NCard, NDataTable, NEmpty, NInput, NPopconfirm, NSpace, NStatistic, NTag, NText, NTooltip, useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { api } from '../api'
import type { ConsoleConfig, WorkspaceInfo } from '../types'
import { WS_STATUS_LABEL, ago, dateTime, statusType } from '../format'
import NewRunModal from '../components/NewRunModal.vue'

const router = useRouter()
const message = useMessage()
const rows = ref<WorkspaceInfo[]>([])
const now = ref(Date.now() / 1000)
const loading = ref(true)
const filter = ref('')
const showNew = ref(false)
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
const runningCount = computed(() => rows.value.filter((w) => w.status === 'running').length)
const doneCount = computed(() => rows.value.filter((w) => w.status === 'done').length)
const totalTasks = computed(() => rows.value.reduce((a, w) => a + w.tasks, 0))

async function stop(w: WorkspaceInfo) {
  try {
    const r = await api.stop(w.id)
    r.ok ? message.success(r.message) : message.warning(r.message)
    await refresh()
  } catch (e) {
    message.error(`终止失败：${(e as Error).message}`)
  }
}

const columns: DataTableColumns<WorkspaceInfo> = [
  {
    title: '状态', key: 'status', width: 96,
    render: (w) => h(NTag, { size: 'small', type: statusType(w.status), round: true, bordered: false }, { default: () => WS_STATUS_LABEL[w.status] || w.status }),
  },
  {
    title: '研究主题', key: 'topic', minWidth: 300, ellipsis: { tooltip: true },
    render: (w) => h('div', { style: 'cursor:pointer', onClick: () => router.push(`/run/${w.id}`) }, [
      h('div', { style: 'font-weight:600' }, w.topic || '（无主题记录）'),
      h('div', { class: 'dim mono', style: 'font-size:11.5px' }, `${w.parent}/${w.label}`),
    ]),
  },
  {
    title: '阶段 / 轮次', key: 'stage', width: 150,
    render: (w) => w.stage ? h('div', [h('span', { class: 'mono' }, w.stage), h('span', { class: 'dim' }, ` · r${w.round}/${w.max_rounds}`)]) : h('span', { class: 'dim' }, '账本未初始化'),
  },
  {
    title: '闸门', key: 'gates', width: 170,
    render: (w) => h(NSpace, { size: 4 }, { default: () => Object.entries(w.gate_counts).map(([k, v]) => h(NTag, { size: 'tiny', type: statusType(k), bordered: false, key: k }, { default: () => `${k} ${v}` })) }),
  },
  { title: '批次 / 任务', key: 'tasks', width: 110, render: (w) => `${w.batches} / ${w.tasks}${w.tasks_running ? ` (▶${w.tasks_running})` : ''}` },
  {
    title: '最近活动', key: 'last_activity', width: 130,
    render: (w) => h(NTooltip, {}, { trigger: () => h('span', ago(w.last_activity, now.value)), default: () => dateTime(w.last_activity) }),
  },
  { title: '创建', key: 'created', width: 120, render: (w) => dateTime(w.created) },
  {
    title: '产物', key: 'final_pdf', width: 90,
    render: (w) => w.final_pdf
      ? h('a', { href: api.pdfUrl(w.id), target: '_blank', style: 'color:#63c26b' }, 'PDF ↗')
      : h('span', { class: 'dim' }, w.open_issues ? `${w.open_issues} open issue` : '—'),
  },
  {
    title: '操作', key: 'actions', width: 170,
    render: (w) => h(NSpace, { size: 6 }, {
      default: () => [
        h(NButton, { size: 'tiny', onClick: () => router.push(`/run/${w.id}`) }, { default: () => w.status === 'running' ? '实时观察' : '回放' }),
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
      <h1>运行与历史</h1>
      <NText depth="3">每一行是一个工作区：正式案例、历史运行、控制台新发起的运行都在这里；点主题进入按角色的实时观察 / 回放。</NText>
      <span style="flex: 1" />
      <NButton type="primary" @click="showNew = true">＋ 发起新研究</NButton>
    </div>

    <NSpace :size="14" style="margin-bottom: 14px">
      <NCard size="small" style="min-width: 150px"><NStatistic label="运行中" :value="runningCount" /></NCard>
      <NCard size="small" style="min-width: 150px"><NStatistic label="已完成" :value="doneCount" /></NCard>
      <NCard size="small" style="min-width: 150px"><NStatistic label="工作区" :value="rows.length" /></NCard>
      <NCard size="small" style="min-width: 150px"><NStatistic label="子 agent 任务累计" :value="totalTasks" /></NCard>
      <NCard size="small" style="flex: 1; min-width: 320px">
        <NInput v-model:value="filter" clearable placeholder="按主题 / 目录 / 状态 / 阶段过滤" />
      </NCard>
    </NSpace>

    <NDataTable :columns="columns" :data="filtered" :loading="loading" :bordered="false" size="small" :row-key="(w: WorkspaceInfo) => w.id"
      :pagination="{ pageSize: 20 }" striped>
      <template #empty><NEmpty description="还没有任何工作区。点右上角「发起新研究」，或用 --workspace-glob 把历史目录挂进来。" /></template>
    </NDataTable>

    <NewRunModal v-model:show="showNew" :config="config" @launched="(id: string) => router.push(`/run/${id}`)" />
  </div>
</template>
