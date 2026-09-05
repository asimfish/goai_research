<script setup lang="ts">
import { computed } from 'vue'
import { NIcon, NTooltip } from 'naive-ui'
import { CheckmarkOutline } from '@vicons/ionicons5'
import type { LedgerSummary, TaskSummary } from '../types'
import { DEFAULT_STAGES, PARALLEL_GROUPS, STAGE_GATE, STAGE_LABEL, roleVisual } from '../roles'
import { checkStatus, gateLabel } from '../labels'

/** 阶段脊柱：11 个编号节点连成一条线；并行阶段画成下方第二轨（DESIGN.md 页面 04）。 */
const props = defineProps<{ ledger: LedgerSummary; tasks?: TaskSummary[]; compact?: boolean; static?: boolean }>()

const stages = computed(() => {
  const s = props.ledger.stages
  return s && s.some((x) => !DEFAULT_STAGES.includes(x)) ? s : DEFAULT_STAGES
})
/** 主轨 = 每个并行组只留第一个；副轨 = 组内其余阶段，挂在主轨对应位置下方 */
const columns = computed(() => {
  const cols: { main: string; branch: string[] }[] = []
  const seen = new Set<string>()
  for (const s of stages.value) {
    if (seen.has(s)) continue
    const grp = PARALLEL_GROUPS.find((g) => g.includes(s))
    const members = grp ? grp.filter((x) => stages.value.includes(x)) : [s]
    members.forEach((x) => seen.add(x))
    cols.push({ main: members[0], branch: members.slice(1) })
  }
  return cols
})
const hasBranch = computed(() => columns.value.some((c) => c.branch.length))
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
function tip(s: string) {
  const g = STAGE_GATE[s]
  const info = g ? props.ledger.gates?.[g] : undefined
  if (!g) return s === 'final' ? '全部检查通过后交付' : '接收研究主题'
  return `${gateLabel(g)}：${checkStatus(info?.status)}${info?.detail ? ' — ' + info.detail : ''}`
}
</script>

<template>
  <div class="spine" :class="{ compact, branch: hasBranch }">
    <div class="track">
      <template v-for="(c, i) in columns" :key="c.main">
        <NTooltip :disabled="static">
          <template #trigger>
            <div class="node" :class="state(c.main)">
              <span class="circle">
                <NIcon v-if="state(c.main) === 'done'" :size="compact ? 11 : 14"><CheckmarkOutline /></NIcon>
                <span v-else-if="state(c.main) === 'warn'">!</span>
                <span v-else-if="state(c.main) === 'fail'">×</span>
                <span v-else>{{ num(c.main) }}</span>
              </span>
              <span v-if="!compact" class="lbl">{{ STAGE_LABEL[c.main] || c.main }}</span>
              <span v-if="runningByStage[c.main]" class="run" title="正在工作的角色数">{{ runningByStage[c.main] }}</span>
              <div v-if="c.branch.length" class="drop">
                <template v-for="b in c.branch" :key="b">
                  <span class="circle small" :class="state(b)">
                    <NIcon v-if="state(b) === 'done'" :size="10"><CheckmarkOutline /></NIcon>
                    <span v-else-if="state(b) === 'warn'">!</span><span v-else-if="state(b) === 'fail'">×</span><span v-else>{{ num(b) }}</span>
                  </span>
                  <span v-if="!compact" class="blbl">{{ STAGE_LABEL[b] || b }}</span>
                </template>
                <span class="par">并行</span>
              </div>
            </div>
          </template>
          <div style="max-width: 420px; font-size: 12.5px">{{ tip(c.main) }}<template v-for="b in c.branch" :key="b"><br>{{ tip(b) }}</template></div>
        </NTooltip>
        <span v-if="i < columns.length - 1" class="seg" :class="{ done: ['done', 'warn'].includes(state(c.main)) }" />
      </template>
    </div>
  </div>
</template>

<style scoped>
.spine { padding: 4px 0 0; overflow-x: auto; }
.track { display: flex; align-items: flex-start; }
.node { position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px; min-width: 64px; }
.compact .node { min-width: 34px; }
.circle { width: 30px; height: 30px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; border: 1.5px solid #9AA6AE; color: #66737B; background: #FBFAF7; font-size: 12px; font-weight: 600; }
.compact .circle { width: 24px; height: 24px; font-size: 10.5px; }
.circle.small { width: 22px; height: 22px; font-size: 10px; }
.node.done > .circle, .circle.small.done { background: var(--verdigris); border-color: var(--verdigris); color: #fff; }
.node.warn > .circle, .circle.small.warn { background: var(--amber); border-color: var(--amber); color: #fff; }
.node.fail > .circle, .circle.small.fail { background: var(--cinnabar); border-color: var(--cinnabar); color: #fff; }
.node.current > .circle, .circle.small.current { background: var(--ink); border-color: var(--ink); color: #fff; box-shadow: 0 0 0 5px rgba(45,116,104,.18); transform: scale(1.12); }
.lbl { font-size: 12px; color: var(--slate); white-space: nowrap; }
.node.current .lbl { color: var(--ink); font-weight: 600; }
.seg { flex: 1; min-width: 18px; height: 1.5px; background: #C9CCC6; margin-top: 15px; }
.compact .seg { margin-top: 12px; min-width: 10px; }
.seg.done { background: var(--verdigris); }
.run { position: absolute; top: -6px; right: 6px; background: var(--verdigris); color: #fff; border-radius: 999px; font-size: 10px; line-height: 15px; padding: 0 5px; }
.drop { display: flex; flex-direction: column; align-items: center; gap: 3px; margin-top: 2px; }
.drop::before { content: ''; width: 1.5px; height: 10px; background: #C9CCC6; display: block; }
.blbl { font-size: 11px; color: var(--slate); white-space: nowrap; }
.par { font-size: 10px; color: var(--verdigris); border: 1px dashed var(--verdigris); border-radius: 999px; padding: 0 6px; line-height: 14px; }
</style>
