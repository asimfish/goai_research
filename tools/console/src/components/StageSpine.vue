<script setup lang="ts">
import { computed } from 'vue'
import { NIcon, NTooltip } from 'naive-ui'
import { CheckmarkOutline, AlertOutline, CloseOutline, TimeOutline } from '@vicons/ionicons5'
import type { LedgerSummary, TaskSummary } from '../types'
import { DEFAULT_STAGES, PARALLEL_GROUPS, STAGE_GATE, STAGE_LABEL, STAGE_ROLES, roleVisual } from '../roles'
import { checkStatus, gateLabel, checkSummary } from '../labels'

/** Research stages with explicit status and owners; parallel work is labelled separately. */
const props = defineProps<{ ledger: LedgerSummary; tasks?: TaskSummary[]; dense?: boolean; static?: boolean }>()

const stages = computed(() => {
  const s = props.ledger.stages
  return s && s.some((x) => !DEFAULT_STAGES.includes(x)) ? s : DEFAULT_STAGES
})
const parallelGroups = computed(() => PARALLEL_GROUPS.map(group => group.filter(s => stages.value.includes(s))).filter(group => group.length > 1))
const completed = computed(() => stages.value.filter(s => state(s) === 'done').length)
function parallelWith(s: string) { return parallelGroups.value.find(group => group.includes(s))?.filter(stage => stage !== s) || [] }
function stateLabel(s: string) {
  return { done: '已完成', warn: '需关注', fail: '未通过', current: '进行中', todo: '待开始' }[state(s)]
}
const runningByStage = computed(() => {
  const m: Record<string, number> = {}
  for (const t of props.tasks || []) if (t.status_group === 'RUNNING') { const st = roleVisual(t.role).stage; m[st] = (m[st] || 0) + 1 }
  return m
})
const currentIdx = computed(() => stages.value.indexOf(props.ledger.stage || ''))
type S = 'done' | 'warn' | 'fail' | 'current' | 'todo'
function state(s: string): S {
  if (props.static) return 'todo'
  const g = STAGE_GATE[s]
  const st = g ? props.ledger.gates?.[g]?.status : undefined
  if (st === 'PASS') return 'done'
  if (st === 'WARN') return 'warn'
  if (st === 'FAIL') return 'fail'
  if (props.ledger.stage === s) return 'current'
  if (s === 'intake' && currentIdx.value > 0) return 'done'
  if (s === 'final' && props.ledger.stage === 'final') return 'current'
  return 'todo'
}
function num(s: string) { return String(stages.value.indexOf(s) + 1).padStart(2, '0') }
function rolesOf(s: string) { return (STAGE_ROLES[s] || []).map((id) => ({ id, ...roleVisual(id) })) }
function gate(s: string) { return props.ledger.gates?.[STAGE_GATE[s] || ''] }
</script>

<template>
  <div class="spine" :class="{ dense }">
    <div class="track" role="list" aria-label="研究阶段">
      <NTooltip v-for="s in stages" :key="s" :delay="200" :show-arrow="false" :style="{ background: '#FBFAF7', color: '#172B3A', padding: '14px 16px', border: '1px solid #D8DAD6' }">
        <template #trigger>
          <div class="node" :class="state(s)" role="listitem" :aria-label="`${num(s)} ${STAGE_LABEL[s] || s} · ${stateLabel(s)} · 负责：${rolesOf(s).map(r => r.label).join('、')}`">
            <div class="node-top">
              <span class="ordinal">{{ num(s) }}</span>
              <span class="stage-status">
                <NIcon :size="13"><CheckmarkOutline v-if="state(s) === 'done'" /><AlertOutline v-else-if="state(s) === 'warn'" /><CloseOutline v-else-if="state(s) === 'fail'" /><TimeOutline v-else-if="state(s) === 'current'" /><span v-else class="pending-dot" /></NIcon>
                <span v-if="!dense">{{ stateLabel(s) }}</span>
              </span>
            </div>
            <div class="stage-title"><span class="lbl">{{ STAGE_LABEL[s] || s }}</span><span v-if="parallelWith(s).length && !dense" class="parallel-marker">并行</span></div>
            <div v-if="!dense" class="who"><span class="owner-label">负责</span>{{ rolesOf(s).map(r => r.label).join('、') }}</div>
            <span v-if="runningByStage[s]" class="running-count">{{ runningByStage[s] }} 个角色运行中</span>
          </div>
        </template>
        <div class="stage-tip">
          <section>
            <div class="tip-heading"><strong>{{ STAGE_LABEL[s] || s }}</strong><span v-if="!props.static" :class="state(s)">{{ gate(s) ? checkStatus(gate(s)?.status) : stateLabel(s) }}</span></div>
            <dl><dt>负责</dt><dd>{{ rolesOf(s).map(r => r.label).join('、') }}</dd><template v-if="STAGE_GATE[s]"><dt>检查</dt><dd>{{ gateLabel(STAGE_GATE[s]!) }}</dd></template><template v-if="parallelWith(s).length"><dt>并行</dt><dd>{{ parallelWith(s).map(stage => STAGE_LABEL[stage] || stage).join('、') }}</dd></template></dl>
            <p>{{ STAGE_GATE[s] ? checkSummary(STAGE_GATE[s]!, gate(s)?.detail) : s === 'final' ? '汇总论文、图表与研究记录' : '接收研究主题并确认范围' }}</p>
          </section>
        </div>
      </NTooltip>
    </div>
    <div v-if="!dense" class="stage-footer">
      <span class="stage-count" v-if="!props.static"><strong>{{ completed }}</strong> / {{ stages.length }} 个阶段已完成</span>
      <div v-if="parallelGroups.length" class="parallel-groups"><span>并行推进</span><span v-for="group in parallelGroups" :key="group.join('-')" class="parallel-group">{{ group.map(s => STAGE_LABEL[s] || s).join(' · ') }}</span></div>
    </div>
  </div>
</template>

<style scoped>
.spine { --stage-blue: #3d566b; --stage-soft: #edf1f5; --stage-border: #cdd7e0; container-type: inline-size; padding-top: 2px; }
.track { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.node { display: flex; flex-direction: column; min-width: 0; gap: 6px; padding: 11px 12px; background: var(--mist); border: 1px solid var(--line-soft); border-radius: 9px; transition: border-color .15s, background .15s; }
.node:hover { border-color: var(--stage-border); background: #f5f6f6; }
.node-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.ordinal { color: #8b969e; font-size: 10px; line-height: 16px; font-variant-numeric: tabular-nums; letter-spacing: .04em; }
.stage-status { display: inline-flex; align-items: center; gap: 3px; color: #7d878e; font-size: 10px; white-space: nowrap; line-height: 16px; }
.pending-dot { display: inline-block; box-sizing: border-box; width: 6px; height: 6px; border: 1px solid #aab2b8; border-radius: 50%; margin: 3px; }
.stage-title { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
.lbl { color: var(--ink); font-size: 13px; font-weight: 650; line-height: 20px; }
.who { color: var(--slate); font-size: 10px; line-height: 16px; overflow-wrap: anywhere; }
.owner-label { color: #8b969e; margin-right: 5px; }
.parallel-marker { color: #85919b; font-size: 9px; line-height: 14px; border-left: 1px solid var(--line); padding-left: 6px; }
.node.done .stage-status { color: var(--stage-blue); }
.node.current { background: var(--stage-soft); border-color: #93a8b9; }
.node.current .stage-status, .running-count { color: var(--stage-blue); font-weight: 600; }
.node.warn { background: #faf7f0; border-color: #e6d9c5; }
.node.warn .stage-status { color: #977345; }
.node.fail { background: #faf2f0; border-color: #e6cbc5; }
.node.fail .stage-status { color: var(--cinnabar); }
.running-count { font-size: 10px; }
.stage-footer { display: flex; align-items: center; flex-wrap: wrap; justify-content: space-between; gap: 8px 16px; margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--line-soft); font-size: 10px; color: var(--slate); }
.stage-count strong { color: var(--stage-blue); font-weight: 650; }
.parallel-groups { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.parallel-group { padding: 2px 7px; background: var(--stage-soft); border-radius: 4px; color: var(--stage-blue); }
.dense .track { grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 5px; }
.dense .node { padding: 7px 8px; gap: 2px; border-radius: 6px; }
.dense .lbl { font-size: 11px; line-height: 18px; }
.dense .ordinal { font-size: 9px; }
.dense .node-top { gap: 3px; }
.stage-tip { width: 260px; font-size: 12px; line-height: 1.7; }
.tip-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.tip-heading strong { font-size: 14px; }
.tip-heading .done, .tip-heading .current { color: var(--stage-blue, #3d566b); }
.tip-heading .warn { color: #977345; }.tip-heading .fail { color: var(--cinnabar); }
.stage-tip dl { display: grid; grid-template-columns: 40px 1fr; margin: 8px 0; gap: 2px 10px; }
.stage-tip dt { color: var(--slate); }.stage-tip dd { margin: 0; }.stage-tip p { margin: 0; color: var(--slate); }
@container (max-width: 620px) { .track { grid-template-columns: repeat(3, minmax(0, 1fr)); }.dense .track { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
@container (max-width: 380px) { .track, .dense .track { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
