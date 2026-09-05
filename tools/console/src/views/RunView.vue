<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NAlert, NButton, NCard, NCollapse, NCollapseItem, NEmpty, NGi, NGrid, NIcon, NPopconfirm, NSelect, NSpace, NSwitch, NTabPane, NTabs, NTag,
  NText, NTooltip, useMessage,
} from 'naive-ui'
import { ArrowBackOutline, DocumentTextOutline, StopCircleOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { Artifacts, FeedEvent, StateResponse, TaskSummary, WorkspaceInfo } from '../types'
import { WS_STATUS_LABEL, ago, bytes, dateTime, hms, oneLine, statusType, tok } from '../format'
import { ROLE_ORDER, roleVisual } from '../roles'
import { commandLabel, gateLabel } from '../labels'
import StageStepper from '../components/StageStepper.vue'
import TaskTimeline from '../components/TaskTimeline.vue'
import TaskCard from '../components/TaskCard.vue'
import TaskDrawer from '../components/TaskDrawer.vue'
import QualityRail from '../components/QualityRail.vue'
import RoleBadge from '../components/RoleBadge.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()
const message = useMessage()

const st = ref<StateResponse | null>(null)
const info = computed<WorkspaceInfo | null>(() => st.value?.workspace_info || null)
const error = ref('')
const showReasoning = ref(false)
const runFilter = ref<string>('')
const openKey = ref<string | null>(null)
const feed = ref<FeedEvent[]>([])
const feedEl = ref<HTMLElement | null>(null)
const artifacts = ref<Artifacts | null>(null)
const launcherLog = ref<{ stdout: string; stderr: string; orchestrator_final: string } | null>(null)
const showTimeline = ref(false)
let lastSeq = 0
let timer: number | undefined
let ticking = false

const isLive = computed(() => info.value?.status === 'running')
const interval = computed(() => (isLive.value ? 1500 : 6000))

async function tick() {
  if (ticking) return
  ticking = true
  try {
    const s = await api.state(props.id, 40)
    st.value = s
    error.value = ''
    const fd = await api.feed(props.id, lastSeq)
    if (fd.events.length) {
      const el = feedEl.value
      const nearBottom = el ? el.scrollHeight - el.clientHeight - el.scrollTop < 40 : true
      feed.value = feed.value.concat(fd.events).slice(-800)
      lastSeq = fd.events[fd.events.length - 1].seq
      await nextTick()
      if (nearBottom && el) el.scrollTop = el.scrollHeight
    }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    ticking = false
  }
}
function schedule() { if (timer) clearInterval(timer); timer = window.setInterval(tick, interval.value) }
onMounted(async () => { await tick(); schedule(); artifacts.value = await api.artifacts(props.id).catch(() => null) })
watch(interval, schedule)
watch(() => props.id, async () => { st.value = null; feed.value = []; lastSeq = 0; await tick(); artifacts.value = await api.artifacts(props.id).catch(() => null) })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

/** 工作区已结束时，残留的 RUNNING / STALE 改成中性标签 */
function normalize(t: TaskSummary): TaskSummary {
  if (info.value?.status === 'running') return t
  if (t.status === 'RUNNING' || t.status === 'STALE') {
    if (info.value?.status === 'stopped') return { ...t, status: 'STOPPED', status_group: 'ENDED' }
    return { ...t, status: 'ENDED', status_group: 'ENDED' }
  }
  return t
}
const visibleTasks = computed<TaskSummary[]>(() => {
  const tasks = (st.value?.tasks || []).map(normalize)
  if (!runFilter.value) return tasks
  return tasks.filter((t) => t.run_id === runFilter.value || t.kind === 'orchestrator')
})
/** 默认只展示“正在跑 + 最近一批”的卡片，历史批次折叠在时间线里，避免几十张卡堆一屏 */
const focusTasks = computed<TaskSummary[]>(() => {
  const all = visibleTasks.value
  if (runFilter.value || all.length <= 9) return all
  const running = all.filter((t) => t.status_group === 'RUNNING')
  const latestRun = [...all].filter((t) => t.kind === 'parallel').sort((a, b) => (b.started || 0) - (a.started || 0))[0]?.run_id
  const orch = all.filter((t) => t.kind === 'orchestrator').slice(-1)
  const picked = new Map<string, TaskSummary>()
  for (const t of [...orch, ...running, ...all.filter((t) => t.run_id === latestRun)]) picked.set(t.key, t)
  return [...picked.values()]
})
const byRole = computed(() => {
  const m: Record<string, TaskSummary[]> = {}
  for (const t of focusTasks.value) (m[t.role] ||= []).push(t)
  const order = ROLE_ORDER.concat(Object.keys(m).filter((r) => !ROLE_ORDER.includes(r)))
  return order.filter((r) => m[r]).map((r) => ({ role: r, tasks: m[r] }))
})
const hiddenCount = computed(() => visibleTasks.value.length - focusTasks.value.length)
const runOptions = computed(() => [{ label: `全部批次（${st.value?.all_runs.length || 0}）`, value: '' }]
  .concat((st.value?.all_runs || []).slice().reverse().map((r) => ({ label: r, value: r }))))
const summary = computed(() => {
  const c: Record<string, number> = {}
  for (const t of visibleTasks.value) if (t.kind === 'parallel') c[t.status_group] = (c[t.status_group] || 0) + 1
  const parts = []
  if (c.RUNNING) parts.push(`${c.RUNNING} 个运行中`)
  if (c.PASS) parts.push(`${c.PASS} 个通过`)
  if (c.WARN) parts.push(`${c.WARN} 个有警告`)
  if (c.FAIL) parts.push(`${c.FAIL} 个失败`)
  if (c.BLOCKED) parts.push(`${c.BLOCKED} 个被阻塞`)
  if (c.ENDED) parts.push(`${c.ENDED} 个已结束`)
  return parts.join(' · ') || '尚无子任务'
})

async function stopRun() {
  try {
    const r = await api.stop(props.id)
    r.ok ? message.success(r.message) : message.warning(r.message)
    await tick()
  } catch (e) { message.error(`终止失败：${(e as Error).message}`) }
}
async function loadLauncherLog() { launcherLog.value = await api.launcherLog(props.id).catch(() => null) }

function feedLine(e: FeedEvent): string {
  switch (e.kind) {
    case 'message': return e.phase === 'started' ? '' : `${oneLine(e.text, 400)}`
    case 'reasoning': return showReasoning.value && e.phase === 'completed' ? `思考：${oneLine(e.text, 240)}` : ''
    case 'command': return e.phase === 'started' ? `执行命令 · ${commandLabel(e.command)}` : e.phase === 'completed' ? `命令结束 · 退出码 ${e.exit_code}${e.output ? ' · ' + oneLine(e.output, 120) : ''}` : ''
    case 'mcp': return e.phase === 'started' ? `调用工具 · ${e.server}.${e.tool}` : e.phase === 'completed' ? `工具返回 · ${e.tool} ${e.error ? '失败：' + oneLine(e.error, 120) : ''}` : ''
    case 'web_search': return e.phase === 'completed' ? `检索网页 · ${oneLine(e.query, 160)}` : ''
    case 'file_change': return e.phase === 'completed' ? `写入文件 · ${(e.changes || []).slice(0, 4).map((c) => String(c.path).split('/').pop()).join(', ')}` : ''
    case 'todo': { const it = e.items || []; return `计划 ${it.filter((i) => i.completed).length}/${it.length}` }
    case 'usage': return `用量 · 输入 ${tok(e.usage?.input_tokens)} · 输出 ${tok(e.usage?.output_tokens)}`
    case 'status': return `状态 · ${e.text}`
    case 'error': return `出错 · ${oneLine(e.text, 300)}`
    case 'thread': return ''
    case 'ledger': return `账本 · ${e.text}`
    case 'audit': return `工具审计 · ${e.tool} ${e.duration_ms != null ? (e.duration_ms / 1000).toFixed(1) + 's' : ''} ${e.ok === false ? '⚠' : ''} ${e.run_id ? '← ' + e.run_id : ''}`
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
    <div class="hd">
      <NButton quaternary size="small" @click="router.push('/history')"><template #icon><NIcon><ArrowBackOutline /></NIcon></template>运行与历史</NButton>
      <h1 class="ellipsis" :title="info.topic">{{ info.topic || info.label }}</h1>
      <NTag :type="statusType(info.status)" round :bordered="false" :class="{ pulse: info.status === 'running' }">{{ WS_STATUS_LABEL[info.status] || info.status }}</NTag>
      <span style="flex: 1" />
      <NSpace align="center" :size="10">
        <NSelect v-model:value="runFilter" :options="runOptions" size="small" style="width: 240px" />
        <NTooltip><template #trigger><span style="display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: #9aa3b5">思考 <NSwitch v-model:value="showReasoning" size="small" /></span></template>在事件流里显示模型的思考摘要</NTooltip>
        <NButton v-if="info.final_pdf" size="small" type="success" ghost tag="a" :href="api.pdfUrl(id)" target="_blank">
          <template #icon><NIcon><DocumentTextOutline /></NIcon></template>综述 PDF · {{ bytes(info.final_pdf_bytes) }}
        </NButton>
        <NPopconfirm v-if="isLive && info.launcher.alive" @positive-click="stopRun">
          <template #trigger><NButton type="error" size="small" ghost><template #icon><NIcon><StopCircleOutline /></NIcon></template>终止运行</NButton></template>
          将结束编排器、所有子 agent 和 MCP 服务进程；已落盘的产物与账本保留，这个工作区留在历史里可回放。
        </NPopconfirm>
      </NSpace>
    </div>
    <div class="sub dim">
      <span class="mono">{{ info.path }}</span>
      <span>· 创建 {{ dateTime(info.created) }}</span>
      <span>· 最近活动 {{ ago(info.last_activity, st.now) }}</span>
      <span v-if="info.launcher.pid">· 进程 {{ info.launcher.pid }}{{ info.launcher.alive ? '（存活）' : info.launcher.exit != null ? `（退出码 ${info.launcher.exit}）` : '' }}</span>
      <span v-if="info.receipt">· 复现回执 {{ info.receipt.status }}（{{ info.receipt.model }} / {{ info.receipt.reasoning_effort }}）</span>
    </div>

    <NAlert v-if="error" type="error" :bordered="false" style="margin-bottom: 10px">连接后端失败：{{ error }}</NAlert>
    <NAlert v-if="info.launcher.stopped" type="warning" :bordered="false" style="margin-bottom: 10px">该运行于 {{ info.launcher.stopped }} 被手动终止。</NAlert>
    <template v-for="(ri, rid) in st.run_info" :key="rid">
      <NAlert v-if="ri.mcp_warning" type="warning" :bordered="false" style="margin-bottom: 10px">批次 {{ rid }}：{{ ri.mcp_warning }}</NAlert>
    </template>

    <NCard size="small" class="stepper-card">
      <template #header>
        <span style="font-weight: 600">研究进度</span>
        <span class="dim" style="font-size: 12px; margin-left: 10px">
          <template v-if="st.ledger.stage">当前阶段 <b class="mono">{{ st.ledger.stage }}</b> · 第 {{ st.ledger.round }}/{{ st.ledger.max_rounds }} 轮 · {{ summary }}</template>
          <template v-else>账本尚未初始化 · {{ summary }}</template>
        </span>
      </template>
      <template #header-extra>
        <NButton size="tiny" quaternary @click="showTimeline = !showTimeline">{{ showTimeline ? '收起时间线' : `批次时间线（${st.all_runs.length} 批）` }}</NButton>
      </template>
      <StageStepper :ledger="st.ledger" :tasks="visibleTasks" />
      <div v-if="showTimeline" style="margin-top: 12px; max-height: 340px; overflow: auto; border-top: 1px solid rgba(255,255,255,.08); padding-top: 10px">
        <TaskTimeline :tasks="visibleTasks" :now="st.now" @open="(k) => (openKey = k)" />
      </div>
    </NCard>

    <div class="main">
      <div class="left">
        <template v-for="g in byRole" :key="g.role">
          <div class="role-head">
            <RoleBadge :role="g.role" :size="24" />
            <span class="rh-name">{{ roleVisual(g.role).label }}</span>
            <span class="dim" style="font-size: 12px">{{ g.tasks.length }} 个任务<template v-if="g.tasks.filter((t) => t.status_group === 'RUNNING').length">，{{ g.tasks.filter((t) => t.status_group === 'RUNNING').length }} 个在跑</template></span>
            <NButton size="tiny" quaternary @click="router.push(`/roles/${g.role}`)">角色说明</NButton>
          </div>
          <NGrid cols="1 m:2 xl:3" responsive="screen" :x-gap="12" :y-gap="12" class="cards">
            <NGi v-for="t in g.tasks" :key="t.key"><TaskCard :task="t" :now="st.now" @open="(k) => (openKey = k)" /></NGi>
          </NGrid>
        </template>
        <NEmpty v-if="!focusTasks.length" description="还没有子 agent 任务。编排器完成范围确认后会派出第一批（文献检索 ∥ 风格库）。" style="margin: 40px 0" />
        <NText v-if="hiddenCount > 0" depth="3" style="font-size: 12px; display: block; margin-top: 4px">
          只显示正在运行和最近一批的 {{ focusTasks.length }} 个任务；另有 {{ hiddenCount }} 个历史任务，在上方选择具体批次或展开时间线查看。
        </NText>
      </div>
      <div class="right"><QualityRail :ledger="st.ledger" /></div>
    </div>

    <NCard size="small" style="margin-top: 14px" content-style="padding-top: 4px">
      <NTabs type="line" size="small" @update:value="(v: string) => v === 'launcher' && loadLauncherLog()">
        <NTabPane name="feed" :tab="`事件流（${feedRows.length}）`">
          <div ref="feedEl" class="feed">
            <div v-for="r in feedRows" :key="r.e.seq" class="feed-row">
              <span class="dim mono">{{ hms(r.e.ts) }}</span>
              <span class="who" :style="{ color: r.e.task ? roleVisual(r.e.role).color : '#9aa3b5' }">{{ r.e.task ? `${roleVisual(r.e.role).label} · ${r.e.name}` : (r.e.kind === 'ledger' ? '运行账本' : '工具审计') }}</span>
              <span class="pre">{{ r.text }}</span>
            </div>
            <NText v-if="!feedRows.length" depth="3">打开页面后新到达的事件会出现在这里；历史事件请点任务卡查看。</NText>
          </div>
        </NTabPane>
        <NTabPane name="audit" :tab="`工具调用审计（${st.audit.total}）`">
          <NSpace :size="6" style="margin-bottom: 8px"><NTag v-for="(v, k) in st.audit.by_tool" :key="k" size="small" :bordered="false">{{ k }} {{ v }}</NTag>
            <NTag v-if="st.audit.by_run['(未归因)']" size="small" type="warning" :bordered="false">未归因到任务 {{ st.audit.by_run['(未归因)'] }}</NTag></NSpace>
          <div v-for="(r, i) in st.audit.recent.slice().reverse()" :key="i" class="audit mono">
            <span class="dim">{{ (r.ts || '').slice(11, 19) }}</span> {{ r.tool }} <span class="dim">{{ r.duration_ms != null ? (r.duration_ms / 1000).toFixed(1) + 's' : '' }}</span>
            <span v-if="r.ok === false" style="color: #f0a020">⚠</span> <span v-if="r.run_id" class="dim">← {{ r.run_id }}</span> <span class="dim">{{ r.request }}</span>
          </div>
        </NTabPane>
        <NTabPane name="ledger" :tab="`运行账本（${st.ledger.log_tail?.length || 0}）`">
          <div v-for="(g, name) in st.ledger.gates" :key="name" class="audit"><span class="mono">{{ name }}</span> {{ gateLabel(String(name)) }} · {{ g.status || 'PENDING' }} <span class="dim">{{ g.detail }}</span></div>
          <div class="dim" style="margin: 8px 0 4px; font-size: 12px">最近日志</div>
          <div v-for="(l, i) in st.ledger.log_tail" :key="i" class="audit mono">{{ l }}</div>
        </NTabPane>
        <NTabPane name="artifacts" tab="产物">
          <NSpace vertical :size="6">
            <div v-for="f in artifactFiles" :key="f.path" class="mono" style="font-size: 12.5px"><span class="dim" style="display: inline-block; width: 130px">{{ f.label }}</span>{{ f.path }} <span class="dim">{{ bytes(f.bytes) }}</span></div>
            <div v-if="artifacts?.sections.length" class="mono" style="font-size: 12.5px"><span class="dim" style="display: inline-block; width: 130px">sections</span>{{ artifacts.sections.join(', ') }}</div>
            <div v-if="artifacts?.figures_svg.length" class="mono" style="font-size: 12.5px"><span class="dim" style="display: inline-block; width: 130px">figures</span>{{ artifacts.figures_svg.join(', ') }}</div>
            <div v-if="artifacts?.reviews.length" class="mono" style="font-size: 12.5px"><span class="dim" style="display: inline-block; width: 130px">reviews</span>{{ artifacts.reviews.join(', ') }}</div>
            <NText v-if="!artifactFiles.length" depth="3">尚无产物文件。</NText>
          </NSpace>
        </NTabPane>
        <NTabPane name="launcher" tab="启动日志">
          <NButton size="tiny" @click="loadLauncherLog" style="margin-bottom: 8px">刷新</NButton>
          <NCollapse v-if="launcherLog" :default-expanded-names="['stdout']">
            <NCollapseItem title="标准输出（reproduce_core.sh）" name="stdout"><pre class="box">{{ launcherLog.stdout || '（空）' }}</pre></NCollapseItem>
            <NCollapseItem title="错误输出" name="stderr"><pre class="box">{{ launcherLog.stderr || '（空）' }}</pre></NCollapseItem>
            <NCollapseItem title="编排器最终回复" name="final"><pre class="box">{{ launcherLog.orchestrator_final || '（尚无）' }}</pre></NCollapseItem>
          </NCollapse>
          <NText v-else depth="3">点「刷新」读取启动器日志与编排器最终回复。</NText>
        </NTabPane>
      </NTabs>
    </NCard>

    <TaskDrawer :ws-id="id" :task-key="openKey" :show-reasoning="showReasoning" @close="openKey = null" />
  </div>
  <div class="page" v-else>
    <NAlert v-if="error" type="error" :bordered="false">{{ error }}</NAlert>
    <NEmpty v-else description="加载中…" style="margin-top: 60px" />
  </div>
</template>

<style scoped>
.hd { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.hd h1 { font-size: 20px; margin: 0; font-weight: 600; max-width: 640px; }
.sub { font-size: 12px; margin: 6px 0 14px; display: flex; gap: 8px; flex-wrap: wrap; }
.stepper-card { margin-bottom: 14px; }
.main { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 14px; align-items: start; }
.right { position: sticky; top: 0; }
.role-head { display: flex; align-items: center; gap: 10px; margin: 6px 0 10px; }
.rh-name { font-weight: 600; font-size: 14px; }
.cards { margin-bottom: 18px; }
.feed { max-height: 320px; overflow: auto; font-size: 12px; }
.feed-row { display: grid; grid-template-columns: 64px 200px 1fr; gap: 10px; padding: 2px 0; border-bottom: 1px dashed rgba(255,255,255,.06); }
.feed-row .who { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.audit { font-size: 11.5px; padding: 3px 0; border-bottom: 1px dashed rgba(255,255,255,.08); }
.box { white-space: pre-wrap; word-break: break-word; background: rgba(0,0,0,.35); padding: 8px 10px; border-radius: 6px; font-size: 12px; max-height: 360px; overflow: auto; }
.pulse { animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .55; } }
@media (max-width: 1100px) { .main { grid-template-columns: 1fr; } .right { position: static; } }
</style>
