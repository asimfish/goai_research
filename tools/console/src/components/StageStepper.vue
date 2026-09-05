<script setup lang="ts">
import { computed } from 'vue'
import { NIcon, NTooltip } from 'naive-ui'
import { CheckmarkOutline } from '@vicons/ionicons5'
import type { LedgerSummary, TaskSummary } from '../types'
import { DEFAULT_STAGES, PARALLEL_GROUPS, STAGE_GATE, STAGE_LABEL, roleVisual } from '../roles'
import { checkStatus, gateLabel } from '../labels'

/** 圆点式阶段步进条：完成 = 绿勾，警告 = 黄，当前 = 蓝色脉冲，未到 = 灰；并行阶段并排显示。 */
const props = defineProps<{ ledger: LedgerSummary; tasks?: TaskSummary[]; static?: boolean }>()

const stages = computed(() => {
  const s = props.ledger.stages
  return s && s.some((x) => !DEFAULT_STAGES.includes(x)) ? s : DEFAULT_STAGES
})
/** 把并行阶段折成一列 */
const columns = computed(() => {
  const cols: string[][] = []
  const seen = new Set<string>()
  for (const s of stages.value) {
    if (seen.has(s)) continue
    const grp = PARALLEL_GROUPS.find((g) => g.includes(s))
    const col = grp ? grp.filter((x) => stages.value.includes(x)) : [s]
    col.forEach((x) => seen.add(x))
    cols.push(col)
  }
  return cols
})
const runningByStage = computed(() => {
  const m: Record<string, number> = {}
  for (const t of props.tasks || []) if (t.status_group === 'RUNNING') { const st = roleVisual(t.role).stage; m[st] = (m[st] || 0) + 1 }
  return m
})
const currentIdx = computed(() => stages.value.indexOf(props.ledger.stage || ''))
function state(s: string): 'done' | 'warn' | 'fail' | 'current' | 'todo' {
  if (props.static) return 'todo'
  const g = STAGE_GATE[s]
  const st = g ? props.ledger.gates?.[g]?.status : undefined
  if (st === 'PASS') return 'done'
  if (st === 'WARN') return 'warn'
  if (st === 'FAIL') return 'fail'
  if (props.ledger.stage === s || (s === 'final' && props.ledger.stage === 'final')) return 'current'
  if (s === 'intake' && currentIdx.value > 0) return 'done'
  return 'todo'
}
function tip(s: string) {
  const g = STAGE_GATE[s]
  const info = g ? props.ledger.gates?.[g] : undefined
  if (!g) return s === 'final' ? '全部检查通过后由 check-done 放行' : '接收研究主题'
  return `${gateLabel(g)}（${g}）：${checkStatus(info?.status)}${info?.detail ? ' — ' + info.detail : ''}`
}
</script>

<template>
  <div class="stepper">
    <template v-for="(col, ci) in columns" :key="ci">
      <div class="col" :class="{ par: col.length > 1 }">
        <NTooltip v-for="s in col" :key="s" :disabled="static">
          <template #trigger>
            <div class="step" :class="state(s)">
              <span class="circle">
                <NIcon v-if="state(s) === 'done'" :size="13"><CheckmarkOutline /></NIcon>
                <span v-else-if="state(s) === 'warn'">!</span>
                <span v-else-if="state(s) === 'fail'">×</span>
                <span v-else class="num">{{ stages.indexOf(s) + 1 }}</span>
              </span>
              <span class="lbl">{{ STAGE_LABEL[s] || s }}</span>
              <span v-if="runningByStage[s]" class="run">▶ {{ runningByStage[s] }}</span>
            </div>
          </template>
          <div style="max-width: 420px; font-size: 12px">{{ tip(s) }}</div>
        </NTooltip>
        <span v-if="col.length > 1" class="par-tag">并行</span>
      </div>
      <span v-if="ci < columns.length - 1" class="line" :class="{ done: col.every((s) => ['done', 'warn'].includes(state(s))) }" />
    </template>
  </div>
</template>

<style scoped>
.stepper { display: flex; align-items: flex-start; gap: 4px; overflow-x: auto; padding: 6px 2px 2px; }
.col { display: flex; flex-direction: column; gap: 6px; position: relative; padding-bottom: 14px; }
.col.par { border: 1px dashed rgba(91,141,239,.35); border-radius: 10px; padding: 6px 6px 16px; background: rgba(91,141,239,.05); }
.par-tag { position: absolute; bottom: 2px; left: 8px; font-size: 10px; color: #7aa2f7; }
.step { display: flex; flex-direction: column; align-items: center; gap: 4px; min-width: 66px; font-size: 12px; color: #9aa3b5; }
.circle { width: 26px; height: 26px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; border: 2px solid rgba(255,255,255,.18); font-size: 11px; font-weight: 600; background: #171a21; }
.step.done .circle { background: #63c26b; border-color: #63c26b; color: #0f1115; } .step.done { color: #d9dde5; }
.step.warn .circle { background: #f0a020; border-color: #f0a020; color: #0f1115; } .step.warn { color: #d9dde5; }
.step.fail .circle { background: #f2726f; border-color: #f2726f; color: #0f1115; }
.step.current .circle { background: #5b8def; border-color: #5b8def; color: #fff; box-shadow: 0 0 0 4px rgba(91,141,239,.25); animation: pulse 1.8s ease-in-out infinite; } .step.current { color: #fff; font-weight: 600; }
.line { flex: 1; min-width: 14px; height: 2px; background: rgba(255,255,255,.14); margin-top: 18px; } .line.done { background: #63c26b88; }
.run { font-size: 10px; background: #5b8def; color: #fff; border-radius: 8px; padding: 0 6px; }
@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 4px rgba(91,141,239,.25); } 50% { box-shadow: 0 0 0 7px rgba(91,141,239,.12); } }
</style>
