<script setup lang="ts">
import { computed } from 'vue'
import { NEmpty, NTooltip } from 'naive-ui'
import type { TaskSummary } from '../types'
import { dur, hms } from '../format'
import { roleVisual } from '../roles'

const props = defineProps<{ tasks: TaskSummary[]; now: number }>()
const emit = defineEmits<{ (e: 'open', key: string): void }>()

const rows = computed(() => props.tasks.filter((t) => t.started))
const t0 = computed(() => Math.min(...rows.value.map((t) => t.started!)))
const t1 = computed(() => Math.max(props.now, ...rows.value.map((t) => t.ended || props.now)))
const span = computed(() => Math.max(1, t1.value - t0.value))
const byRun = computed(() => {
  const m: Record<string, TaskSummary[]> = {}
  for (const t of rows.value) (m[t.run_id] ||= []).push(t)
  return Object.keys(m).sort().map((k) => ({ run: k, tasks: m[k].sort((a, b) => a.started! - b.started!) }))
})
function left(t: TaskSummary) { return ((t.started! - t0.value) / span.value) * 100 }
function width(t: TaskSummary) { return Math.max(0.3, (((t.ended || props.now) - t.started!) / span.value) * 100) }
</script>

<template>
  <div v-if="rows.length" class="tl">
    <template v-for="g in byRun" :key="g.run">
      <div class="run mono">{{ g.run }}</div>
      <div v-for="t in g.tasks" :key="t.key" class="row" @click="emit('open', t.key)">
        <span class="name mono" :title="t.key">{{ roleVisual(t.role).icon }} {{ t.name }}</span>
        <div class="track">
          <NTooltip>
            <template #trigger><div class="bar" :class="t.status_group" :style="{ left: left(t) + '%', width: width(t) + '%', background: roleVisual(t.role).color }" /></template>
            {{ roleVisual(t.role).label }} · {{ t.status }} · {{ dur(t.elapsed) }} · {{ hms(t.started) }} → {{ t.ended ? hms(t.ended) : '…' }}
          </NTooltip>
        </div>
        <span class="d dim">{{ dur(t.elapsed) }}</span>
      </div>
    </template>
    <div class="axis dim"><span>{{ hms(t0) }}</span><span>{{ hms(t0 + span / 2) }}</span><span>{{ hms(t1) }}</span></div>
  </div>
  <NEmpty v-else description="暂无已启动的任务" size="small" />
</template>

<style scoped>
.tl { font-size: 11.5px; }
.run { color: #8a93a6; margin: 6px 0 2px; }
.row { display: flex; align-items: center; gap: 8px; height: 18px; cursor: pointer; }
.row:hover { background: rgba(255,255,255,.04); }
.name { width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.track { flex: 1; position: relative; height: 12px; background: rgba(0,0,0,.35); border-radius: 3px; }
.bar { position: absolute; top: 0; height: 12px; border-radius: 3px; opacity: .85; min-width: 2px; }
.bar.FAIL, .bar.BLOCKED { opacity: .45; background-image: repeating-linear-gradient(45deg, transparent 0 4px, rgba(0,0,0,.45) 4px 8px); }
.bar.RUNNING { box-shadow: 0 0 6px rgba(91,141,239,.8); }
.d { width: 64px; text-align: right; }
.axis { display: flex; justify-content: space-between; margin-left: 248px; font-size: 10.5px; margin-top: 2px; }
</style>
