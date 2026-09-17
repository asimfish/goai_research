<script setup lang="ts">
import { computed } from 'vue'
import { NEmpty, NTooltip } from 'naive-ui'
import type { TaskSummary } from '../types'
import { dur, hms, dateTime } from '../format'
import { roleVisual } from '../roles'
import { taskEnd, timelineRange } from '../taskTimeline'

const props = defineProps<{ tasks: TaskSummary[]; now: number }>()
const emit = defineEmits<{ (e: 'open', key: string): void }>()

const rows = computed(() => props.tasks.filter((t) => t.started !== null && Number.isFinite(t.started)))
const range = computed(() => timelineRange(rows.value, props.now))
const t0 = computed(() => range.value.start)
const t1 = computed(() => range.value.end)
const span = computed(() => range.value.duration)
const crossesDay = computed(() => new Date(t0.value * 1000).toDateString() !== new Date(t1.value * 1000).toDateString())
function axisTime(ts: number) { return crossesDay.value ? dateTime(ts) : hms(ts) }
const byRun = computed(() => {
  const m: Record<string, TaskSummary[]> = {}
  for (const t of rows.value) (m[t.run_id] ||= []).push(t)
  return Object.keys(m).sort().map((k) => ({ run: k, tasks: m[k].sort((a, b) => a.started! - b.started!) }))
})
function left(t: TaskSummary) { return ((t.started! - t0.value) / span.value) * 100 }
function width(t: TaskSummary) { return Math.min(100 - left(t), Math.max(0.3, ((taskEnd(t, props.now) - t.started!) / span.value) * 100)) }
</script>

<template>
  <div v-if="rows.length" class="tl" :data-start="t0" :data-end="t1">
    <div class="tl-summary dim">历时 {{ dur(t1 - t0) }}<span v-if="rows.some(t => t.status_group === 'RUNNING' && !t.ended)"> · 运行中</span></div>
    <template v-for="g in byRun" :key="g.run">
      <div class="run mono">{{ g.run }}</div>
      <div v-for="t in g.tasks" :key="t.key" class="row" @click="emit('open', t.key)">
        <span class="name mono" :title="t.key"><span class="dot" :style="{ background: roleVisual(t.role).color }" />{{ t.name }}</span>
        <div class="track">
          <NTooltip>
            <template #trigger><div class="bar" :class="t.status_group" :style="{ left: left(t) + '%', width: width(t) + '%', background: roleVisual(t.role).color }" /></template>
            {{ roleVisual(t.role).label }} · {{ t.status }} · {{ dur(taskEnd(t, now) - t.started!) }} · {{ hms(t.started) }} → {{ t.ended ? hms(t.ended) : t.status_group === 'RUNNING' ? '进行中' : '结束时间未记录' }}
          </NTooltip>
        </div>
        <span class="d dim">{{ dur(taskEnd(t, now) - t.started!) }}</span>
      </div>
    </template>
    <div class="axis dim"><span>{{ axisTime(t0) }}</span><span>{{ axisTime(t0 + (t1 - t0) / 2) }}</span><span>{{ axisTime(t1) }}</span></div>
  </div>
  <NEmpty v-else description="暂无已启动的任务" size="small" />
</template>

<style scoped>
.tl { font-size: 11.5px; }
.tl-summary { text-align: right; margin-bottom: 6px; font-variant-numeric: tabular-nums; }
.run { color: var(--slate); margin: 6px 0 2px; }
.row { display: flex; align-items: center; gap: 8px; height: 18px; cursor: pointer; }
.row:hover { background: #F3F1EA; }
.name { width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
.track { flex: 1; min-width: 0; position: relative; height: 12px; background: #E7E8E3; border-radius: 3px; overflow: hidden; }
.bar { position: absolute; top: 0; height: 12px; border-radius: 3px; opacity: .85; min-width: 2px; }
.bar.FAIL, .bar.BLOCKED { opacity: .45; background-image: repeating-linear-gradient(45deg, transparent 0 4px, rgba(0,0,0,.45) 4px 8px); }
.bar.RUNNING { box-shadow: 0 0 6px rgba(45,116,104,.6); }
.d { width: 64px; text-align: right; }
.axis { display: flex; justify-content: space-between; margin-left: 248px; margin-right: 72px; font-size: 10.5px; margin-top: 2px; }
</style>
