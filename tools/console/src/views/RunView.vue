<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NAlert, NButton, NCard, NCollapse, NCollapseItem, NEmpty, NGi, NGrid, NPopconfirm, NSelect, NSpace, NSwitch, NTabPane, NTabs, NTag,
  NText, NTooltip, useMessage,
} from 'naive-ui'
import { api } from '../api'
import type { Artifacts, FeedEvent, StateResponse, TaskSummary, WorkspaceInfo } from '../types'
import { WS_STATUS_LABEL, ago, bytes, dateTime, hms, oneLine, statusType, tok } from '../format'
import { ROLE_ORDER, roleVisual } from '../roles'
import PipelineStrip from '../components/PipelineStrip.vue'
import TaskTimeline from '../components/TaskTimeline.vue'
import TaskCard from '../components/TaskCard.vue'
import TaskDrawer from '../components/TaskDrawer.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()
const message = useMessage()

const st = ref<StateResponse | null>(null)
const info = computed<WorkspaceInfo | null>(() => st.value?.workspace_info || null)
const error = ref('')
const showReasoning = ref(false)
const autoscroll = ref(true)
const runFilter = ref<string>('')
const openKey = ref<string | null>(null)
const feed = ref<FeedEvent[]>([])
const feedEl = ref<HTMLElement | null>(null)
const artifacts = ref<Artifacts | null>(null)
const launcherLog = ref<{ stdout: string; stderr: string; orchestrator_final: string } | null>(null)
let lastSeq = 0
let timer: number | undefined
let ticking = false

const isLive = computed(() => info.value?.status === 'running')
const interval = computed(() => (isLive.value ? 1500 : 6000))

async function tick() {
  if (ticking) return
  ticking = true
  try {
    const s = await api.state(props.id, 30)
    st.value = s
    error.value = ''
    const fd = await api.feed(props.id, lastSeq)
    if (fd.events.length) {
      const el = feedEl.value
      const nearBottom = el ? el.scrollHeight - el.clientHeight - el.scrollTop < 40 : true
      feed.value = feed.value.concat(fd.events).slice(-800)
      lastSeq = fd.events[fd.events.length - 1].seq
      await nextTick()
      if (autoscroll.value && nearBottom && el) el.scrollTop = el.scrollHeight
    }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    ticking = false
  }
}
function schedule() {
  if (timer) clearInterval(timer)
  timer = window.setInterval(tick, interval.value)
}
onMounted(async () => {
  await tick()
  schedule()
  artifacts.value = await api.artifacts(props.id).catch(() => null)
})
watch(interval, schedule)
watch(() => props.id, async () => { st.value = null; feed.value = []; lastSeq = 0; await tick(); artifacts.value = await api.artifacts(props.id).catch(() => null) })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

/** 工作区已结束时，残留的 RUNNING（缺 .exit）/ STALE（编排器流被截断）改成中性标签，别误导成还在跑 */
function normalize(t: TaskSummary): TaskSummary {
  if (info.value?.status === 'running') return t
  if (t.status === 'RUNNING' || t.status === 'STALE') {
    if (info.value?.status === 'stopped') return { ...t, status: '已终止（进程被杀）', status_group: 'ENDED' }
    return { ...t, status: t.status === 'RUNNING' ? '无退出记录' : '已结束（流被截断）', status_group: 'ENDED' }
  }
  return t
}
const visibleTasks = computed<TaskSummary[]>(() => {
  const tasks = (st.value?.tasks || []).map(normalize)
  if (!runFilter.value) return tasks
  return tasks.filter((t) => t.run_id === runFilter.value || t.kind === 'orchestrator')
})
const byRole = computed(() => {
  const m: Record<string, TaskSummary[]> = {}
  for (const t of visibleTasks.value) (m[t.role] ||= []).push(t)
  const order = ROLE_ORDER.concat(Object.keys(m).filter((r) => !ROLE_ORDER.includes(r)))
  return order.filter((r) => m[r]).map((r) => ({ role: r, tasks: m[r] }))
})
const runOptions = computed(() => [{ label: `全部批次（${st.value?.all_runs.length || 0}）`, value: '' }]
  .concat((st.value?.all_runs || []).slice().reverse().map((r) => ({ label: r, value: r }))))
const counts = computed(() => st.value?.counts || {})

async function stopRun() {
  try {
    const r = await api.stop(props.id)
    r.ok ? message.success(r.message) : message.warning(r.message)
    await tick()
  } catch (e) { message.error(`终止失败：${(e as Error).message}`) }
}
async function loadLauncherLog() {
  launcherLog.value = await api.launcherLog(props.id).catch(() => null)
}

function feedLine(e: FeedEvent): string {
  switch (e.kind) {
    case 'message': return e.phase === 'started' ? '' : `💬 ${oneLine(e.text, 400)}`
    case 'reasoning': return showReasoning.value && e.phase === 'completed' ? `🧠 ${oneLine(e.text, 240)}` : ''
    case 'command': return e.phase === 'started' ? `$ ${oneLine(e.command, 220)}` : e.phase === 'completed' ? `↳ exit ${e.exit_code} ${oneLine(e.output, 160)}` : ''
    case 'mcp': return e.phase === 'started' ? `🔧 ${e.server}.${e.tool}(${oneLine(e.arguments, 160)})` : e.phase === 'completed' ? `↳ ${e.tool} ${e.status} ${oneLine(e.error || e.result, 160)}` : ''
    case 'web_search': return e.phase === 'completed' ? `🌐 ${oneLine(e.query, 200)}` : ''
    case 'file_change': return e.phase === 'completed' ? `✎ ${(e.changes || []).slice(0, 6).map((c) => `${c.kind}:${String(c.path).split('/').pop()}`).join(', ')}` : ''
    case 'todo': { const it = e.items || []; return `☑ ${it.filter((i) => i.completed).length}/${it.length}` }
    case 'usage': return `Σ in ${tok(e.usage?.input_tokens)} · out ${tok(e.usage?.output_tokens)}`
    case 'status': return `■ ${e.text}`
    case 'error': return `⚠ ${oneLine(e.text, 300)}`
    case 'thread': return `▶ session ${e.text}`
    case 'ledger': return `📒 ${e.text}`
    case 'audit': return `🔧审计 ${e.tool} ${e.duration_ms != null ? (e.duration_ms / 1000).toFixed(1) + 's' : ''} ${e.ok === false ? '⚠' : ''} ${e.run_id ? '← ' + e.run_id : ''}`
    default: return ''
  }
}
const feedRows = computed(() => feed.value.map((e) => ({ e, text: feedLine(e) })).filter((r) => r.text))
const artifactFiles = computed(() => {
  if (!artifacts.value) return [] as { label: string; path: string; bytes: number }[]
  const out: { label: string; path: string; bytes: number }[] = []
  for (const [k, v] of Object.entries(artifacts.value)) if (v && !Array.isArray(v)) out.push({ label: k, path: v.path, bytes: v.bytes })
  return out
})
</script>

<template>
  <div class="page" v-if="st && info">
    <div class="page-title" style="flex-wrap: wrap">
      <NButton quaternary size="small" @click="router.push('/history')">← 运行与历史</NButton>
      <h1 class="ellipsis" style="max-width: 720px" :title="info.topic">{{ info.topic || info.label }}</h1>
      <NTag :type="statusType(info.status)" round :bordered="false">{{ WS_STATUS_LABEL[info.status] || info.status }}</NTag>
      <NText depth="3" class="mono" style="font-size: 12px">{{ info.path }}</NText>
      <span style="flex: 1" />
      <NSpace align="center" :size="10">
        <NSelect v-model:value="runFilter" :options="runOptions" size="small" style="width: 260px" />
        <NTooltip><template #trigger><NSwitch v-model:value="showReasoning" size="small" /></template>显示模型的 reasoning 摘要</NTooltip>
        <NTooltip><template #trigger><NSwitch v-model:value="autoscroll" size="small" /></template>新事件到达时自动滚动</NTooltip>
        <NPopconfirm v-if="isLive && info.launcher.alive" @positive-click="stopRun">
          <template #trigger><NButton type="error" size="small" ghost>终止运行</NButton></template>
          向 pid {{ info.launcher.pid }} 的整个进程组发 SIGTERM（编排器、子 agent、MCP server），8 秒后仍在则 SIGKILL。已落盘的产物与账本保留。
        </NPopconfirm>
        <NButton v-if="info.final_pdf" size="small" type="success" ghost tag="a" :href="api.pdfUrl(id)" target="_blank">打开综述 PDF ({{ bytes(info.final_pdf_bytes) }})</NButton>
      </NSpace>
    </div>

    <NAlert v-if="error" type="error" :bordered="false" style="margin-bottom: 10px">连接后端失败：{{ error }}</NAlert>
    <NAlert v-if="info.launcher.stopped" type="warning" :bordered="false" style="margin-bottom: 10px">该运行于 {{ info.launcher.stopped }} 被手动终止。</NAlert>
    <NAlert v-for="(ri, rid) in st.run_info" :key="rid" v-show="ri.mcp_warning" type="warning" :bordered="false" style="margin-bottom: 10px">
      批次 {{ rid }}：{{ ri.mcp_warning }}
    </NAlert>

    <NSpace :size="12" style="margin-bottom: 12px; flex-wrap: wrap">
      <NCard size="small" class="stat"><div class="dim">账本</div><div>{{ st.ledger.stage || '未初始化' }} <span class="dim" v-if="st.ledger.round">· 第 {{ st.ledger.round }}/{{ st.ledger.max_rounds }} 轮 · {{ st.ledger.effort }} / {{ st.ledger.strictness }}</span></div></NCard>
      <NCard size="small" class="stat"><div class="dim">子任务</div><div><NSpace :size="4"><NTag v-for="(v, k) in counts" :key="k" size="tiny" :type="statusType(String(k))" :bordered="false">{{ k }} {{ v }}</NTag></NSpace></div></NCard>
      <NCard size="small" class="stat"><div class="dim">open issues</div><div>{{ st.ledger.open_issues?.length || 0 }} <span class="dim">/ 共 {{ st.ledger.issues_total || 0 }}</span></div></NCard>
      <NCard size="small" class="stat"><div class="dim">MCP 审计</div><div>{{ st.audit.total }} <span class="dim">未归因 {{ st.audit.by_run['(未归因)'] || 0 }}</span></div></NCard>
      <NCard size="small" class="stat"><div class="dim">最近活动</div><div>{{ ago(info.last_activity, st.now) }}</div></NCard>
      <NCard size="small" class="stat" v-if="info.launcher.started"><div class="dim">启动</div><div class="mono" style="font-size: 12px">{{ info.launcher.started.split('\t').pop() }} · pid {{ info.launcher.pid }}{{ info.launcher.alive ? ' 存活' : (info.launcher.exit != null ? ` · exit ${info.launcher.exit}` : '') }}</div></NCard>
      <NCard size="small" class="stat" v-if="info.receipt"><div class="dim">复现回执</div><div>{{ info.receipt.status }} <span class="dim">{{ info.receipt.model }} / {{ info.receipt.reasoning_effort }}</span></div></NCard>
    </NSpace>

    <NCard size="small" title="流程：账本阶段 → 闸门 → 正在跑的角色" style="margin-bottom: 12px">
      <PipelineStrip :ledger="st.ledger" :tasks="visibleTasks" />
    </NCard>

    <NGrid cols="1 l:4" responsive="screen" :x-gap="12" :y-gap="12" style="margin-bottom: 12px">
      <NGi span="1 l:3">
        <NCard size="small" title="批次时间线" style="height: 100%">
          <div style="max-height: 320px; overflow: auto"><TaskTimeline :tasks="visibleTasks" :now="st.now" @open="(k) => (openKey = k)" /></div>
        </NCard>
      </NGi>
      <NGi>
        <NCard size="small" title="闸门与 issue" style="height: 100%">
          <div v-for="(g, name) in st.ledger.gates" :key="name" class="gate">
            <span class="mono">{{ name }}</span>
            <NTooltip><template #trigger><NTag size="tiny" :type="statusType(g.status || 'PENDING')" :bordered="false">{{ g.status || 'PENDING' }}</NTag></template>{{ g.detail || '无 detail' }}</NTooltip>
          </div>
          <NEmpty v-if="!st.ledger.gates || !Object.keys(st.ledger.gates).length" description="账本尚无闸门" size="small" />
          <div v-if="st.ledger.open_issues?.length" style="margin-top: 8px">
            <div v-for="i in st.ledger.open_issues" :key="i.id" class="issue">
              <NTag size="tiny" :type="i.severity === 'blocker' ? 'error' : i.severity === 'major' ? 'warning' : 'default'" :bordered="false">{{ i.id }} {{ i.severity }}</NTag>
              → {{ i.target }} <span class="dim">{{ i.text }}</span>
            </div>
          </div>
        </NCard>
      </NGi>
    </NGrid>

    <template v-for="g in byRole" :key="g.role">
      <div class="role-head">
        <span style="font-size: 16px">{{ roleVisual(g.role).icon }}</span>
        <span style="font-weight: 600">{{ roleVisual(g.role).label }}</span>
        <NText depth="3" class="mono" style="font-size: 12px">{{ g.role }}</NText>
        <NText depth="3" style="font-size: 12px">· {{ g.tasks.length }} 个任务<template v-if="g.tasks.filter((t) => t.status_group === 'RUNNING').length"> · {{ g.tasks.filter((t) => t.status_group === 'RUNNING').length }} 在跑</template></NText>
      </div>
      <NGrid cols="1 m:2 xl:3" responsive="screen" :x-gap="12" :y-gap="12" style="margin-bottom: 14px">
        <NGi v-for="t in g.tasks" :key="t.key">
          <TaskCard :task="t" :now="st.now" :show-reasoning="showReasoning" :autoscroll="autoscroll" @open="(k) => (openKey = k)" />
        </NGi>
      </NGrid>
    </template>
    <NEmpty v-if="!visibleTasks.length" description="还没有子 agent 任务。编排器完成定范围后会派出第一批（lit_search ∥ style_bank）。" style="margin: 30px 0" />

    <NTabs type="line" size="small" style="margin-top: 8px" @update:value="(v: string) => v === 'launcher' && loadLauncherLog()">
      <NTabPane name="feed" :tab="`全局事件流（${feedRows.length}）`">
        <div ref="feedEl" class="feed mono">
          <div v-for="r in feedRows" :key="r.e.seq" class="feed-row">
            <span class="dim">{{ hms(r.e.ts) }}</span>
            <span class="who" :style="{ color: roleVisual(r.e.role).color }">{{ r.e.task ? `${roleVisual(r.e.role).icon} ${r.e.name}` : (r.e.kind === 'ledger' ? '📒 账本' : '🔧 审计') }}</span>
            <span class="pre">{{ r.text }}</span>
          </div>
          <NText v-if="!feedRows.length" depth="3">打开页面后新到达的事件会出现在这里（历史事件请点任务卡查看）。</NText>
        </div>
      </NTabPane>
      <NTabPane name="audit" :tab="`MCP 审计（${st.audit.total}）`">
        <NSpace :size="6" style="margin-bottom: 8px"><NTag v-for="(v, k) in st.audit.by_tool" :key="k" size="small" :bordered="false">{{ k }} {{ v }}</NTag></NSpace>
        <div v-for="(r, i) in st.audit.recent.slice().reverse()" :key="i" class="audit mono">
          <span class="dim">{{ (r.ts || '').slice(11, 19) }}</span> {{ r.tool }} <span class="dim">{{ r.duration_ms != null ? (r.duration_ms / 1000).toFixed(1) + 's' : '' }}</span>
          <span v-if="r.ok === false" style="color: #f0a020">⚠</span> <span v-if="r.run_id" class="dim">← {{ r.run_id }}</span> <span class="dim">{{ r.request }}</span>
        </div>
      </NTabPane>
      <NTabPane name="ledger" :tab="`账本日志（${st.ledger.log_tail?.length || 0}）`">
        <div v-for="(l, i) in st.ledger.log_tail" :key="i" class="audit mono">{{ l }}</div>
      </NTabPane>
      <NTabPane name="artifacts" tab="产物">
        <NSpace vertical :size="6">
          <div v-for="f in artifactFiles" :key="f.path" class="mono" style="font-size: 12.5px">
            <span class="dim" style="display: inline-block; width: 130px">{{ f.label }}</span>{{ f.path }} <span class="dim">{{ bytes(f.bytes) }}</span>
          </div>
          <div v-if="artifacts?.sections.length" class="mono" style="font-size: 12.5px"><span class="dim" style="display: inline-block; width: 130px">sections</span>{{ artifacts.sections.join(', ') }}</div>
          <div v-if="artifacts?.figures_svg.length" class="mono" style="font-size: 12.5px"><span class="dim" style="display: inline-block; width: 130px">figures</span>{{ artifacts.figures_svg.join(', ') }}</div>
          <div v-if="artifacts?.reviews.length" class="mono" style="font-size: 12.5px"><span class="dim" style="display: inline-block; width: 130px">reviews</span>{{ artifacts.reviews.join(', ') }}</div>
          <NText v-if="!artifactFiles.length" depth="3">尚无产物文件。</NText>
        </NSpace>
      </NTabPane>
      <NTabPane name="launcher" tab="启动器日志">
        <NButton size="tiny" @click="loadLauncherLog" style="margin-bottom: 8px">刷新</NButton>
        <NCollapse v-if="launcherLog" :default-expanded-names="['stdout']">
          <NCollapseItem title="stdout（reproduce_core.sh）" name="stdout"><pre class="box">{{ launcherLog.stdout || '（空）' }}</pre></NCollapseItem>
          <NCollapseItem title="stderr" name="stderr"><pre class="box">{{ launcherLog.stderr || '（空）' }}</pre></NCollapseItem>
          <NCollapseItem title="编排器最终回复" name="final"><pre class="box">{{ launcherLog.orchestrator_final || '（尚无）' }}</pre></NCollapseItem>
        </NCollapse>
        <NText v-else depth="3">点「刷新」读取 launcher.stdout.log / stderr.log / orchestrator.final.md。</NText>
      </NTabPane>
    </NTabs>

    <TaskDrawer :ws-id="id" :task-key="openKey" :show-reasoning="showReasoning" @close="openKey = null" />
    <NText depth="3" style="font-size: 11px; display: block; margin-top: 16px">创建 {{ dateTime(info.created) }} · 刷新间隔 {{ interval / 1000 }}s · 耗时按启动/退出标记文件时间计算（回放时为归档文件的 mtime）</NText>
  </div>
  <div class="page" v-else>
    <NAlert v-if="error" type="error" :bordered="false">{{ error }}</NAlert>
    <NEmpty v-else description="加载中…" style="margin-top: 60px" />
  </div>
</template>

<style scoped>
.stat { min-width: 150px; } .stat .dim { font-size: 11.5px; margin-bottom: 2px; }
.gate { display: flex; justify-content: space-between; gap: 8px; padding: 3px 0; border-bottom: 1px dashed rgba(255,255,255,.08); font-size: 12px; }
.issue { font-size: 12px; padding: 3px 0; border-bottom: 1px dashed rgba(255,255,255,.08); }
.role-head { display: flex; align-items: center; gap: 8px; margin: 4px 0 8px; padding-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,.1); }
.feed { max-height: 320px; overflow: auto; font-size: 11.5px; }
.feed-row { display: flex; gap: 8px; padding: 1px 0; } .feed-row .who { min-width: 220px; }
.audit { font-size: 11.5px; padding: 2px 0; border-bottom: 1px dashed rgba(255,255,255,.08); }
.box { white-space: pre-wrap; word-break: break-word; background: rgba(0,0,0,.35); padding: 8px 10px; border-radius: 6px; font-size: 12px; max-height: 360px; overflow: auto; }
</style>
