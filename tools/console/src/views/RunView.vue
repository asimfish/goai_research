<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NAlert, NButton, NCollapse, NCollapseItem, NDrawer, NDrawerContent, NEmpty, NIcon, NPopconfirm, NSelect, NSwitch, NTabPane, NTabs, NTag,
  NTooltip, useMessage,
} from 'naive-ui'
import { ChevronDownOutline, ChevronUpOutline, DocumentTextOutline, GitNetworkOutline, StopOutline, TimeOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { Artifacts, FeedEvent, StateResponse, TaskSummary, WorkspaceInfo } from '../types'
import { WS_STATUS_LABEL, ago, bytes, dateTime, dur, hms, oneLine, statusType, tok } from '../format'
import { STAGE_LABEL, roleVisual } from '../roles'
import { SEVERITY_LABEL, commandLabel, gateLabel, taskStatus } from '../labels'
import StageSpine from '../components/StageSpine.vue'
import QualityStampGrid from '../components/QualityStampGrid.vue'
import ActiveAgentCard from '../components/ActiveAgentCard.vue'
import TaskTimeline from '../components/TaskTimeline.vue'
import TaskDrawer from '../components/TaskDrawer.vue'
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
const showDone = ref(false)
const showEvents = ref(false)
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
  } catch (e) { error.value = (e as Error).message } finally { ticking = false }
}
function schedule() { if (timer) clearInterval(timer); timer = window.setInterval(tick, interval.value) }
onMounted(async () => { await tick(); schedule(); artifacts.value = await api.artifacts(props.id).catch(() => null) })
/** 失败 / 终止的运行：自动读启动日志，把最后一条错误直接放到横幅下 */
watch(() => info.value?.status, async (s) => { if ((s === 'failed' || s === 'stopped' || s === 'ended') && !launcherLog.value) await loadLauncherLog() }, { immediate: true })
const failReason = computed(() => {
  if (info.value?.status !== 'failed' || !launcherLog.value) return ''
  const lines = (launcherLog.value.stderr || '').replace(/\x1b\[[0-9;]*m/g, '').split('\n').map((l) => l.trim()).filter((l) => l && !/^Reading additional input/.test(l))
  const err = lines.find((l) => /error|失败|not found|denied|Traceback|退出|拒绝/i.test(l)) || lines[0] || ''
  return err.slice(0, 300)
})
watch(interval, schedule)
watch(() => props.id, async () => { st.value = null; feed.value = []; lastSeq = 0; await tick(); artifacts.value = await api.artifacts(props.id).catch(() => null) })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

function normalize(t: TaskSummary): TaskSummary {
  if (info.value?.status === 'running') return t
  if (t.status === 'RUNNING' || t.status === 'STALE') return { ...t, status: info.value?.status === 'stopped' ? 'STOPPED' : 'ENDED', status_group: 'ENDED' }
  return t
}
const allTasks = computed<TaskSummary[]>(() => (st.value?.tasks || []).map(normalize))
const scoped = computed(() => runFilter.value ? allTasks.value.filter((t) => t.run_id === runFilter.value || t.kind === 'orchestrator') : allTasks.value)
const parallel = computed(() => scoped.value.filter((t) => t.kind === 'parallel'))
const running = computed(() => scoped.value.filter((t) => t.status_group === 'RUNNING'))
const latestRun = computed(() => [...parallel.value].sort((a, b) => (b.started || 0) - (a.started || 0))[0]?.run_id)
/** 「正在工作的角色」：运行中的任务；没有在跑的（已结束 / 编排器阶段）就显示最近一批 */
const active = computed<TaskSummary[]>(() => {
  if (running.value.length) return running.value
  if (runFilter.value) return parallel.value
  const latest = parallel.value.filter((t) => t.run_id === latestRun.value)
  if (latest.length) return latest
  return scoped.value.filter((t) => t.kind === 'orchestrator').slice(-1)
})
const doneTasks = computed(() => scoped.value.filter((t) => !active.value.includes(t) && t.kind === 'parallel'))
const doneRoles = computed(() => new Set(doneTasks.value.filter((t) => ['PASS', 'WARN'].includes(t.status_group)).map((t) => t.role)).size)
const ledger = computed(() => st.value?.ledger || {})
const openIssues = computed(() => ledger.value.open_issues || [])
const checksPassed = computed(() => Object.values(ledger.value.gates || {}).filter((g) => g.status === 'PASS' || g.status === 'WARN').length)

/** 一句话总状态：先自然语言，再证据 */
const headline = computed(() => {
  const w = info.value
  if (!w) return ''
  const stage = ledger.value.stage ? (STAGE_LABEL[ledger.value.stage] || ledger.value.stage) : ''
  const blockers = openIssues.value.filter((i) => i.severity === 'blocker').length
  if (w.status === 'running') {
    if (!ledger.value.stage) return '编排器正在读取规程、准备定范围'
    if (blockers) return `${stage}阶段有 ${blockers} 条阻断性审稿意见待处理`
    if (running.value.length) return `正在${stage}：${running.value.length} 个角色在工作${openIssues.value.length ? `，${openIssues.value.length} 条审稿意见待处理` : '，未发现阻塞'}`
    return `${stage}阶段进行中，编排器正在派发或验收`
  }
  if (w.status === 'done') return `研究已交付：质量检查 ${checksPassed.value} / 9 通过`
  if (w.status === 'stopped') return `运行已被手动终止，停在${stage || '起点'}`
  if (w.status === 'failed') return `运行失败，停在${stage || '起点'}${w.launcher.exit ? `（退出码 ${w.launcher.exit}）` : ''}`
  return `运行已结束，停在${stage || '起点'}`
})
const headlineKind = computed(() => { const s = info.value?.status; return s === 'running' ? (openIssues.value.some((i) => i.severity === 'blocker') ? 'warn' : 'run') : s === 'done' ? 'ok' : s === 'failed' ? 'bad' : 'wait' })
const elapsedText = computed(() => {
  const w = info.value
  if (!w) return ''
  if (w.status !== 'running') return ''
  const start = w.launcher.started ? Date.parse(w.launcher.started.split('\t').pop() || '') / 1000 : (w.created ? Date.parse(w.created) / 1000 : null)
  const end = st.value?.now || Date.now() / 1000
  return start && end > start ? `已运行 ${dur(end - start)}` : ''
})
const runOptions = computed(() => [{ label: `全部批次（${st.value?.all_runs.length || 0}）`, value: '' }].concat((st.value?.all_runs || []).slice().reverse().map((r) => ({ label: r, value: r }))))

async function stopRun() {
  try { const r = await api.stop(props.id); r.ok ? message.success(r.message) : message.warning(r.message); await tick() }
  catch (e) { message.error(`终止失败：${(e as Error).message}`) }
}
async function loadLauncherLog() { launcherLog.value = await api.launcherLog(props.id).catch(() => null) }

function feedLine(e: FeedEvent): string {
  switch (e.kind) {
    case 'message': return e.phase === 'started' ? '' : oneLine(e.text, 400)
    case 'reasoning': return showReasoning.value && e.phase === 'completed' ? `思考：${oneLine(e.text, 240)}` : ''
    case 'command': return e.phase === 'started' ? `执行命令 · ${commandLabel(e.command)}` : e.phase === 'completed' ? `命令结束 · 退出码 ${e.exit_code}${e.output ? ' · ' + oneLine(e.output, 120) : ''}` : ''
    case 'mcp': return e.phase === 'started' ? `调用工具 · ${e.server}.${e.tool}` : e.phase === 'completed' ? `工具返回 · ${e.tool}${e.error ? ' 失败：' + oneLine(e.error, 120) : ''}` : ''
    case 'web_search': return e.phase === 'completed' ? `检索网页 · ${oneLine(e.query, 160)}` : ''
    case 'file_change': return e.phase === 'completed' ? `写入文件 · ${(e.changes || []).slice(0, 4).map((c) => String(c.path).split('/').pop()).join(', ')}` : ''
    case 'todo': { const it = e.items || []; return `计划 ${it.filter((i) => i.completed).length}/${it.length}` }
    case 'usage': return `用量 · 输入 ${tok(e.usage?.input_tokens)} · 输出 ${tok(e.usage?.output_tokens)}`
    case 'status': return `状态 · ${taskStatus(e.text || '', e.text)}`
    case 'error': return `出错 · ${oneLine(e.text, 300)}`
    case 'ledger': return `账本 · ${e.text}`
    case 'audit': return `工具审计 · ${e.tool} ${e.duration_ms != null ? (e.duration_ms / 1000).toFixed(1) + 's' : ''} ${e.ok === false ? '⚠' : ''} ${e.run_id ? '← ' + e.run_id : ''}`
    default: return ''
  }
}
const feedRows = computed(() => feed.value.map((e) => ({ e, text: feedLine(e) })).filter((r) => r.text))
const artifactFiles = computed(() => {
  if (!artifacts.value) return [] as { label: string; path: string; bytes: number }[]
  const out: { label: string; path: string; bytes: number }[] = []
  for (const [k, v] of Object.entries(artifacts.value)) if (v && !Array.isArray(v) && 'path' in (v as object) && 'bytes' in (v as object)) out.push({ label: k, ...(v as { path: string; bytes: number }) })
  return out
})
function issueStage(target: string) { return STAGE_LABEL[target] || gateLabel(target) || target }
function issueRole(target: string) { return ({ lit_search: 'goai-lit-search', ref_gate: 'goai-ref-guard', taxonomy: 'goai-survey-writer', writing: 'goai-survey-writer', figures: 'goai-figure-studio', ideas: 'goai-idea-forge', style_bank: 'goai-style-bank' } as Record<string, string>)[target] || 'goai-orchestrator' }
</script>

<template>
  <div class="page" v-if="st && info">
    <div class="hd">
      <h1>运行实时观察</h1>
      <span class="dim">·</span>
      <span class="topic ellipsis" :title="info.topic">{{ info.topic || info.label }}</span>
      <span class="small"><span class="st-dot" :class="headlineKind" />{{ WS_STATUS_LABEL[info.status] || info.status }}</span>
      <span style="flex: 1" />
      <NSelect v-if="(st.all_runs.length || 0) > 1" v-model:value="runFilter" :options="runOptions" size="small" style="width: 220px" />
      <NButton v-if="info.final_pdf" size="small" tag="a" :href="api.pdfUrl(id)" target="_blank"><template #icon><NIcon><DocumentTextOutline /></NIcon></template>综述 PDF</NButton>
      <NPopconfirm v-if="isLive && info.launcher.alive" @positive-click="stopRun">
        <template #trigger><NButton size="small" type="error" ghost><template #icon><NIcon><StopOutline /></NIcon></template>终止运行</NButton></template>
        将结束编排器、所有子 agent 与 MCP 服务进程；已落盘的产物与账本保留，可回放。
      </NPopconfirm>
    </div>

    <NAlert v-if="error" type="error" :bordered="false" style="margin-bottom: 10px">连接后端失败：{{ error }}</NAlert>
    <template v-for="(ri, rid) in st.run_info" :key="rid"><NAlert v-if="ri.mcp_warning" type="warning" :bordered="false" style="margin-bottom: 10px">批次 {{ rid }}：{{ ri.mcp_warning }}</NAlert></template>

    <div class="sheet banner">
      <span class="banner-icon" :class="headlineKind"><NIcon :size="26"><GitNetworkOutline /></NIcon></span>
      <div>
        <div class="banner-text">{{ headline }}</div>
        <div class="small dim">{{ elapsedText }}<template v-if="elapsedText"> · </template>最近更新 {{ ago(info.last_activity, st.now) }}<template v-if="info.launcher.stopped"> · 于 {{ info.launcher.stopped }} 终止</template></div>
        <div v-if="failReason" class="fail-reason small"><span class="mono">{{ failReason }}</span> <a @click="showEvents = true">查看启动日志 ›</a></div>
      </div>
    </div>

    <div class="row1">
      <div class="sheet panel progress">
        <div class="ph"><span class="card-h">研究推进 <span class="dim small" style="font-weight: 400">阶段 · 负责角色</span></span><span class="dim small">{{ ledger.stage ? `第 ${ledger.round}/${ledger.max_rounds} 轮` : '账本尚未初始化' }}</span></div>
        <StageSpine :ledger="ledger" :tasks="scoped" />
      </div>
      <div class="sheet panel checks">
        <div class="ph"><span class="card-h">质量检查</span></div>
        <QualityStampGrid :ledger="ledger" />
      </div>
    </div>

    <div class="row2">
      <div class="sheet panel agents">
        <div class="ph">
          <span class="card-h">{{ running.length ? '正在工作的角色' : (info.status === 'running' ? '角色' : '最近工作的角色') }}</span>
          <span class="dim small">{{ running.length ? `${running.length} 个角色活跃 · ` : '' }}{{ doneRoles }} 个角色已完成</span>
        </div>
        <div v-if="active.length" class="agent-grid">
          <template v-for="(t, i) in active" :key="t.key">
            <ActiveAgentCard :task="t" :now="st.now" @open="(k) => (openKey = k)" />
            <span v-if="i < active.length - 1" class="conn" />
          </template>
        </div>
        <NEmpty v-else description="编排器完成定范围后会派出第一批角色（文献检索 ∥ 风格库）" style="margin: 30px 0" />
      </div>
      <div class="sheet panel issues">
        <div class="ph"><span class="card-h">待处理审稿意见</span><span class="dim small">{{ openIssues.length }} 条 / 共 {{ ledger.issues_total || 0 }}</span></div>
        <div v-if="openIssues.length" class="issue-list">
          <div v-for="i in openIssues" :key="i.id" class="issue" :class="i.severity" @click="router.push(`/roles/${issueRole(i.target)}`)">
            <div class="i-title">{{ oneLine(i.text, 80) }}</div>
            <div class="small dim"><RoleBadge :role="issueRole(i.target)" :size="18" style="vertical-align: -4px; margin-right: 4px" />责任角色：{{ roleVisual(issueRole(i.target)).label }} · 回到 {{ issueStage(i.target) }} · {{ SEVERITY_LABEL[i.severity] || i.severity }}</div>
          </div>
        </div>
        <div v-else class="dim small" style="padding: 18px 0">{{ ledger.stage ? '目前没有待处理的审稿意见。' : '审稿意见会在审稿阶段出现。' }}</div>
      </div>
    </div>

    <div class="sheet done-row" @click="showDone = !showDone">
      <span class="card-h">已完成 {{ doneTasks.length }} 个任务 · {{ doneRoles }} 个角色</span>
      <span style="flex: 1" />
      <NButton size="small" quaternary @click.stop="showEvents = true"><template #icon><NIcon><TimeOutline /></NIcon></template>查看事件记录</NButton>
      <NIcon :size="18" class="dim"><component :is="showDone ? ChevronUpOutline : ChevronDownOutline" /></NIcon>
    </div>
    <div v-if="showDone" class="sheet done-body">
      <div class="dim small" style="margin-bottom: 8px">批次时间线（点任务查看它的完整记录）</div>
      <TaskTimeline :tasks="scoped" :now="st.now" @open="(k) => (openKey = k)" />
      <div class="agent-grid wrap" style="margin-top: 14px">
        <ActiveAgentCard v-for="t in doneTasks" :key="t.key" :task="t" :now="st.now" @open="(k) => (openKey = k)" />
      </div>
    </div>

    <NDrawer v-model:show="showEvents" :width="880" placement="right">
      <NDrawerContent title="事件记录" closable :native-scrollbar="false">
        <div class="small dim" style="margin-bottom: 8px"><span class="mono">{{ info.path }}</span> · 创建 {{ dateTime(info.created) }}<span v-if="info.launcher.pid"> · 进程 {{ info.launcher.pid }}</span>
          <span style="margin-left: 12px; display: inline-flex; align-items: center; gap: 6px">思考 <NSwitch v-model:value="showReasoning" size="small" /></span></div>
        <NTabs type="line" size="small" @update:value="(v: string) => v === 'launcher' && loadLauncherLog()">
          <NTabPane name="feed" :tab="`事件流（${feedRows.length}）`">
            <div ref="feedEl" class="feed">
              <div v-for="r in feedRows" :key="r.e.seq" class="feed-row">
                <span class="dim mono">{{ hms(r.e.ts) }}</span>
                <span class="who ellipsis" :style="{ color: r.e.task ? roleVisual(r.e.role).color : '#66737B' }">{{ r.e.task ? `${roleVisual(r.e.role).label} · ${r.e.name}` : (r.e.kind === 'ledger' ? '运行账本' : '工具审计') }}</span>
                <span class="pre">{{ r.text }}</span>
              </div>
              <div v-if="!feedRows.length" class="dim">打开页面后新到达的事件会出现在这里；历史事件请点角色卡查看。</div>
            </div>
          </NTabPane>
          <NTabPane name="audit" :tab="`工具调用审计（${st.audit.total}）`">
            <div style="margin-bottom: 8px; display: flex; gap: 6px; flex-wrap: wrap"><NTag v-for="(v, k) in st.audit.by_tool" :key="k" size="small" :bordered="false">{{ k }} {{ v }}</NTag>
              <NTag v-if="st.audit.by_run['(未归因)']" size="small" type="warning" :bordered="false">未归因到任务 {{ st.audit.by_run['(未归因)'] }}</NTag></div>
            <div v-for="(r, i) in st.audit.recent.slice().reverse()" :key="i" class="audit mono">
              <span class="dim">{{ (r.ts || '').slice(11, 19) }}</span> {{ r.tool }} <span class="dim">{{ r.duration_ms != null ? (r.duration_ms / 1000).toFixed(1) + 's' : '' }}</span>
              <span v-if="r.ok === false" style="color: #B98032">⚠</span> <span v-if="r.run_id" class="dim">← {{ r.run_id }}</span> <span class="dim">{{ r.request }}</span>
            </div>
          </NTabPane>
          <NTabPane name="ledger" :tab="`运行账本（${ledger.log_tail?.length || 0}）`">
            <div v-for="(g, name) in ledger.gates" :key="name" class="audit"><span class="mono">{{ name }}</span> {{ gateLabel(String(name)) }} · {{ g.status || 'PENDING' }} <span class="dim">{{ g.detail }}</span></div>
            <div class="dim small" style="margin: 8px 0 4px">最近日志</div>
            <div v-for="(l, i) in ledger.log_tail" :key="i" class="audit mono">{{ l }}</div>
          </NTabPane>
          <NTabPane name="artifacts" tab="产物">
            <div v-for="f in artifactFiles" :key="f.path" class="mono small"><span class="dim" style="display: inline-block; width: 130px">{{ f.label }}</span>{{ f.path }} <span class="dim">{{ bytes(f.bytes) }}</span></div>
            <div v-if="artifacts?.sections.length" class="mono small"><span class="dim" style="display: inline-block; width: 130px">sections</span>{{ artifacts.sections.join(', ') }}</div>
            <div v-if="artifacts?.figures_svg.length" class="mono small"><span class="dim" style="display: inline-block; width: 130px">figures</span>{{ artifacts.figures_svg.join(', ') }}</div>
            <div v-if="!artifactFiles.length" class="dim">尚无产物文件。</div>
          </NTabPane>
          <NTabPane name="launcher" tab="启动日志">
            <NButton size="tiny" @click="loadLauncherLog" style="margin-bottom: 8px">刷新</NButton>
            <NCollapse v-if="launcherLog" :default-expanded-names="['stdout']">
              <NCollapseItem title="标准输出（reproduce_core.sh）" name="stdout"><pre class="box">{{ launcherLog.stdout || '（空）' }}</pre></NCollapseItem>
              <NCollapseItem title="错误输出" name="stderr"><pre class="box">{{ launcherLog.stderr || '（空）' }}</pre></NCollapseItem>
              <NCollapseItem title="编排器最终回复" name="final"><pre class="box">{{ launcherLog.orchestrator_final || '（尚无）' }}</pre></NCollapseItem>
            </NCollapse>
          </NTabPane>
        </NTabs>
      </NDrawerContent>
    </NDrawer>
    <TaskDrawer :ws-id="id" :task-key="openKey" :show-reasoning="showReasoning" @close="openKey = null" />
  </div>
  <div class="page" v-else>
    <NAlert v-if="error" type="error" :bordered="false">{{ error }}</NAlert>
    <NEmpty v-else description="加载中…" style="margin-top: 60px" />
  </div>
</template>

<style scoped>
.hd { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.hd h1 { font-size: 22px; line-height: 30px; margin: 0; font-weight: 600; }
.topic { font-weight: 600; max-width: 480px; }
.banner { display: flex; align-items: center; gap: 16px; padding: 14px 20px; margin-bottom: 16px; }
.banner-icon { width: 44px; height: 44px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; background: #EFEDE6; color: var(--slate); flex: none; }
.banner-icon.run, .banner-icon.ok { background: var(--verdigris-soft); color: var(--verdigris); } .banner-icon.warn { background: var(--amber-soft); color: var(--amber); } .banner-icon.bad { background: var(--cinnabar-soft); color: var(--cinnabar); }
.banner-text { font-size: 18px; line-height: 26px; font-weight: 600; }
.fail-reason { margin-top: 6px; color: var(--cinnabar); background: var(--cinnabar-soft); border-radius: 8px; padding: 6px 10px; word-break: break-all; }
.fail-reason a { cursor: pointer; color: var(--ink); text-decoration: underline; margin-left: 6px; }
.row1 { display: grid; grid-template-columns: minmax(0, 8fr) minmax(300px, 4fr); gap: 16px; margin-bottom: 16px; }
.row2 { display: grid; grid-template-columns: minmax(0, 8fr) minmax(300px, 4fr); gap: 16px; margin-bottom: 16px; }
.progress, .checks, .agents, .issues { padding: 18px 22px; }
.ph { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px; gap: 10px; }
.agent-grid { display: flex; align-items: stretch; gap: 0; }
.agent-grid > .agent, .agent-grid > :deep(.agent) { flex: 1; min-width: 0; }
.agent-grid.wrap { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.conn { width: 22px; height: 1.5px; background: #C9CCC6; align-self: center; flex: none; }
.issue-list { display: flex; flex-direction: column; gap: 10px; }
.issue { border-left: 3px solid var(--amber); background: var(--amber-soft); border-radius: 0 10px 10px 0; padding: 10px 14px; cursor: pointer; }
.issue.blocker { border-left-color: var(--cinnabar); background: var(--cinnabar-soft); }
.i-title { font-weight: 600; font-size: 13.5px; margin-bottom: 4px; }
.done-row { display: flex; align-items: center; gap: 12px; padding: 12px 20px; cursor: pointer; }
.done-body { padding: 16px 20px; margin-top: 10px; }
.feed { max-height: 60vh; overflow: auto; font-size: 12.5px; }
.feed-row { display: grid; grid-template-columns: 64px 180px 1fr; gap: 10px; padding: 3px 0; border-bottom: 1px dashed var(--line-soft); }
.audit { font-size: 12px; padding: 3px 0; border-bottom: 1px dashed var(--line-soft); }
.box { white-space: pre-wrap; word-break: break-word; background: #EEEDE6; padding: 8px 10px; border-radius: 6px; font-size: 12px; max-height: 360px; overflow: auto; }
@media (max-width: 1100px) { .row1, .row2 { grid-template-columns: 1fr; } .agent-grid { flex-direction: column; } .conn { display: none; } }
</style>
