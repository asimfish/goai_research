<script setup lang="ts">
import { computed } from 'vue'
import { NTooltip } from 'naive-ui'
import type { LedgerSummary, TaskSummary } from '../types'
import { DEFAULT_STAGES, PARALLEL_GROUPS, STAGE_GATE, STAGE_LABEL, roleVisual } from '../roles'

const props = defineProps<{ ledger: LedgerSummary; tasks: TaskSummary[]; static?: boolean }>()

const stages = computed(() => {
  const s = props.ledger.stages
  return s && s.some((x) => !DEFAULT_STAGES.includes(x)) ? s : DEFAULT_STAGES
})

const runningByStage = computed(() => {
  const m: Record<string, number> = {}
  for (const t of props.tasks) if (t.status_group === 'RUNNING') { const st = roleVisual(t.role).stage; m[st] = (m[st] || 0) + 1 }
  return m
})

function gateOf(stage: string) {
  const g = STAGE_GATE[stage]
  return g ? { name: g, info: props.ledger.gates?.[g] } : null
}
function statusClass(stage: string) {
  const g = gateOf(stage)
  if (!g) return stage === 'final' && props.ledger.stage === 'final' ? 'PASS' : 'none'
  return g.info?.status || 'PENDING'
}
function isParallelWithNext(i: number) {
  const a = stages.value[i], b = stages.value[i + 1]
  return PARALLEL_GROUPS.some((grp) => grp.includes(a) && grp.includes(b))
}
</script>

<template>
  <div class="strip">
    <template v-for="(s, i) in stages" :key="s">
      <NTooltip :disabled="static">
        <template #trigger>
          <div class="stage" :class="[statusClass(s), { cur: ledger.stage === s, par: PARALLEL_GROUPS.some((g) => g.includes(s)) }]">
            <div class="name">{{ STAGE_LABEL[s] || s }} <span class="mono id">{{ s }}</span></div>
            <div class="gate" v-if="gateOf(s)">
              <span class="mono">{{ gateOf(s)!.name }}</span>
              <span v-if="!static" class="st">{{ gateOf(s)!.info?.status || 'PENDING' }}<template v-if="gateOf(s)!.info?.round"> · r{{ gateOf(s)!.info?.round }}</template></span>
            </div>
            <div class="gate" v-else><span class="mono">{{ s === 'final' ? 'check-done' : '—' }}</span></div>
            <span v-if="runningByStage[s]" class="run">▶ {{ runningByStage[s] }}</span>
            <span v-if="ledger.stage === s" class="cur-mark">◀ 当前</span>
          </div>
        </template>
        <div style="max-width: 420px; font-size: 12px">
          <b>{{ s }}</b>
          <div v-if="gateOf(s)?.info?.detail">{{ gateOf(s)!.info!.detail }}</div>
          <div v-else class="dim">尚无闸门记录</div>
        </div>
      </NTooltip>
      <span v-if="i < stages.length - 1" class="arrow">{{ isParallelWithNext(i) ? '∥' : '→' }}</span>
    </template>
  </div>
</template>

<style scoped>
.strip { display: flex; flex-wrap: wrap; gap: 6px; align-items: stretch; }
.stage { position: relative; min-width: 118px; padding: 6px 10px 6px 12px; border: 1px solid rgba(255,255,255,.12); border-radius: 8px; background: rgba(255,255,255,.03); font-size: 12px; border-left-width: 4px; }
.stage.par { background: rgba(91,141,239,.06); }
.stage.cur { box-shadow: 0 0 0 1px #5b8def inset; border-color: #5b8def; }
.stage.PASS { border-left-color: #63c26b; } .stage.WARN { border-left-color: #f0a020; }
.stage.FAIL { border-left-color: #f2726f; } .stage.PENDING, .stage.none { border-left-color: rgba(255,255,255,.18); }
.name { font-weight: 600; } .id { font-size: 10.5px; opacity: .55; margin-left: 2px; font-weight: 400; }
.gate { color: #9aa3b5; font-size: 11px; display: flex; gap: 6px; flex-wrap: wrap; }
.gate .st { color: #d9dde5; }
.run { position: absolute; top: -8px; right: -6px; background: #5b8def; color: #fff; border-radius: 9px; font-size: 10px; padding: 0 6px; }
.cur-mark { position: absolute; bottom: -9px; right: 6px; font-size: 10px; color: #5b8def; background: #18181c; padding: 0 4px; }
.arrow { align-self: center; color: #6b7280; }
</style>
