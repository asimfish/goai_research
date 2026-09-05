<script setup lang="ts">
import { computed } from 'vue'
import type { TaskSummary } from '../types'
import { dur, oneLine } from '../format'
import { roleVisual } from '../roles'
import { latestMessage, taskStatus } from '../labels'
import RoleBadge from './RoleBadge.vue'

/** 正在工作的角色卡（DESIGN.md 页面 04）：角色、正在做的动作、最近产出、用时。细节留给点击后的抽屉。 */
const props = defineProps<{ task: TaskSummary; now: number }>()
const emit = defineEmits<{ (e: 'open', key: string): void }>()
const vis = computed(() => roleVisual(props.task.role))
const action = computed(() => oneLine(latestMessage(props.task.recent) || props.task.last_message || '正在准备…', 90))
const lastOutput = computed(() => {
  for (let i = props.task.recent.length - 1; i >= 0; i--) {
    const ev = props.task.recent[i]
    if (ev.kind === 'file_change' && ev.changes?.length) return ev.changes.map((c) => String(c.path).split('/').pop()).slice(0, 2).join('、')
    if (ev.kind === 'mcp' && ev.status === 'completed') return `${ev.tool} 返回`
  }
  return props.task.expected.length ? props.task.expected.map((e) => e.split('/').pop()).slice(0, 2).join('、') : '—'
})
const statusKey = computed(() => props.task.status_group === 'RUNNING' ? 'run' : props.task.status_group === 'PASS' ? 'ok' : props.task.status_group === 'WARN' ? 'warn' : ['FAIL', 'BLOCKED'].includes(props.task.status_group) ? 'bad' : 'wait')
const stale = computed(() => props.task.status === 'RUNNING' && props.task.last_activity != null && props.now - props.task.last_activity > 300)
</script>

<template>
  <div class="sheet agent" :class="statusKey" @click="emit('open', task.key)">
    <div class="hd">
      <RoleBadge :role="task.role" :size="44" :status="statusKey" />
      <div class="t">
        <div class="name">{{ vis.label }}</div>
        <div class="action">{{ action }}</div>
      </div>
    </div>
    <div class="ft small">
      <div><div class="dim">最近产出</div><div class="ellipsis val" :title="lastOutput">{{ lastOutput }}</div></div>
      <div><div class="dim">用时</div><div class="val">{{ dur(task.elapsed) }}</div></div>
      <div><div class="dim">状态</div><div class="val">{{ taskStatus(task.status_group, task.status) }}{{ stale ? '（5 分钟无输出）' : '' }}</div></div>
    </div>
    <div class="task mono small dim">{{ task.name }}</div>
  </div>
</template>

<style scoped>
.agent { padding: 16px 18px 12px; cursor: pointer; display: flex; flex-direction: column; gap: 12px; transition: box-shadow .18s; min-width: 0; }
.agent:hover { box-shadow: var(--shadow-float); }
.agent.run { border-color: #B8D3CD; }
.hd { display: flex; gap: 12px; align-items: flex-start; }
.t { min-width: 0; }
.name { font-size: 15px; font-weight: 600; }
.action { font-size: 13px; line-height: 19px; color: var(--ink); margin-top: 2px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.ft { display: grid; grid-template-columns: 1fr auto auto; gap: 14px; border-top: 1px solid var(--line-soft); padding-top: 10px; }
.val { color: var(--ink); }
.task { border-top: 1px dashed var(--line-soft); padding-top: 6px; }
</style>
