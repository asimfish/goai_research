<script setup lang="ts">
import { computed } from 'vue'
import { NIcon, NTooltip } from 'naive-ui'
import { CheckmarkOutline } from '@vicons/ionicons5'
import type { LedgerSummary, TaskSummary } from '../types'
import { DEFAULT_STAGES, PARALLEL_GROUPS, STAGE_GATE, STAGE_LABEL, STAGE_ROLES, roleVisual } from '../roles'
import { checkStatus, gateLabel } from '../labels'

/**
 * 阶段脊柱：11 个编号阶段连成一条线，并行阶段挂成第二轨；每个节点下方标出负责角色（色点 + 名字），
 * 以免把 11 个阶段误读成 11 个角色。dense = 首页账本卡里的紧凑版（字更小、角色只显示色点）。
 */
const props = defineProps<{ ledger: LedgerSummary; tasks?: TaskSummary[]; dense?: boolean; static?: boolean }>()

const stages = computed(() => {
  const s = props.ledger.stages
  return s && s.some((x) => !DEFAULT_STAGES.includes(x)) ? s : DEFAULT_STAGES
})
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
function tip(s: string) {
  const g = STAGE_GATE[s]
  const info = g ? props.ledger.gates?.[g] : undefined
  const who = `负责角色：${rolesOf(s).map((r) => r.label).join(' / ')}`
  if (!g) return `${STAGE_LABEL[s] || s} · ${who}${s === 'final' ? ' · 全部检查通过后交付' : ' · 接收研究主题并确认范围'}`
  return `${STAGE_LABEL[s] || s} · ${who} · 完成标准「${gateLabel(g)}」${props.static ? '' : `：${checkStatus(info?.status)}${info?.detail ? ' — ' + info.detail : ''}`}`
}
</script>

<template>
  <div class="spine" :class="{ dense }">
    <div class="track">
      <template v-for="(c, i) in columns" :key="c.main">
        <NTooltip>
          <template #trigger>
            <div class="node" :class="state(c.main)">
              <span class="circle">
                <NIcon v-if="state(c.main) === 'done'" :size="dense ? 11 : 14"><CheckmarkOutline /></NIcon>
                <span v-else-if="state(c.main) === 'warn'">!</span>
                <span v-else-if="state(c.main) === 'fail'">×</span>
                <span v-else>{{ num(c.main) }}</span>
              </span>
              <span class="lbl">{{ STAGE_LABEL[c.main] || c.main }}</span>
              <span class="who">
                <template v-for="r in rolesOf(c.main)" :key="r.id">
                  <span class="rdot" :style="{ background: r.color }" /><span v-if="!dense" class="rname">{{ r.label }}</span>
                </template>
              </span>
              <span v-if="runningByStage[c.main]" class="run" title="正在工作的角色数">{{ runningByStage[c.main] }}</span>
              <div v-if="c.branch.length" class="drop">
                <template v-for="b in c.branch" :key="b">
                  <span class="circle small" :class="state(b)">
                    <NIcon v-if="state(b) === 'done'" :size="10"><CheckmarkOutline /></NIcon>
                    <span v-else-if="state(b) === 'warn'">!</span><span v-else-if="state(b) === 'fail'">×</span><span v-else>{{ num(b) }}</span>
                  </span>
                  <span class="lbl">{{ STAGE_LABEL[b] || b }}</span>
                  <span class="who">
                    <template v-for="r in rolesOf(b)" :key="r.id"><span class="rdot" :style="{ background: r.color }" /><span v-if="!dense" class="rname">{{ r.label }}</span></template>
                  </span>
                </template>
                <span class="par">并行</span>
              </div>
            </div>
          </template>
          <div style="max-width: 440px; font-size: 12.5px">{{ tip(c.main) }}<template v-for="b in c.branch" :key="b"><br>{{ tip(b) }}</template></div>
        </NTooltip>
        <span v-if="i < columns.length - 1" class="seg" :class="{ done: ['done', 'warn'].includes(state(c.main)) }" />
      </template>
    </div>
    <div class="legend small dim" v-if="!dense">
      <span>11 个阶段由 9 个角色承担，节点下方为负责角色；</span>
      <span v-for="id in ['goai-orchestrator', 'goai-lit-search', 'goai-style-bank', 'goai-ref-guard', 'goai-survey-writer', 'goai-figure-studio', 'goai-idea-forge', 'goai-reviewer']" :key="id" class="lg"><span class="rdot" :style="{ background: roleVisual(id).color }" />{{ roleVisual(id).label }}</span>
    </div>
  </div>
</template>

<style scoped>
.spine { padding: 4px 0 0; overflow-x: auto; }
.track { display: flex; align-items: flex-start; }
.node { position: relative; display: flex; flex-direction: column; align-items: center; gap: 4px; min-width: 76px; }
.dense .node { min-width: 58px; gap: 3px; }
.circle { width: 30px; height: 30px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; border: 1.5px solid #9AA6AE; color: #66737B; background: #FBFAF7; font-size: 12px; font-weight: 600; }
.dense .circle { width: 24px; height: 24px; font-size: 10.5px; }
.circle.small { width: 22px; height: 22px; font-size: 10px; }
.dense .circle.small { width: 20px; height: 20px; }
.node.done > .circle, .circle.small.done { background: var(--verdigris); border-color: var(--verdigris); color: #fff; }
.node.warn > .circle, .circle.small.warn { background: var(--amber); border-color: var(--amber); color: #fff; }
.node.fail > .circle, .circle.small.fail { background: var(--cinnabar); border-color: var(--cinnabar); color: #fff; }
.node.current > .circle, .circle.small.current { background: var(--ink); border-color: var(--ink); color: #fff; box-shadow: 0 0 0 5px rgba(45,116,104,.18); transform: scale(1.12); }
.lbl { font-size: 12px; color: var(--ink); white-space: nowrap; }
.dense .lbl { font-size: 11px; }
.node.current > .lbl { font-weight: 600; }
.who { display: inline-flex; align-items: center; gap: 3px; font-size: 11px; color: var(--slate); white-space: nowrap; }
.rdot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; flex: none; }
.rname { margin-right: 4px; }
.seg { flex: 1; min-width: 16px; height: 1.5px; background: #C9CCC6; margin-top: 15px; }
.dense .seg { margin-top: 12px; min-width: 8px; }
.seg.done { background: var(--verdigris); }
.run { position: absolute; top: -6px; right: 4px; background: var(--verdigris); color: #fff; border-radius: 999px; font-size: 10px; line-height: 15px; padding: 0 5px; }
.drop { display: flex; flex-direction: column; align-items: center; gap: 3px; margin-top: 2px; }
.drop::before { content: ''; width: 1.5px; height: 10px; background: #C9CCC6; display: block; }
.drop .lbl { font-size: 11px; }
.par { font-size: 10px; color: var(--verdigris); border: 1px dashed var(--verdigris); border-radius: 999px; padding: 0 6px; line-height: 14px; margin-top: 2px; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 12px; margin-top: 12px; padding-top: 10px; border-top: 1px dashed var(--line-soft); }
.lg { display: inline-flex; align-items: center; gap: 4px; }
</style>
