<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NProgress, NTag, NTooltip } from 'naive-ui'
import type { TaskSummary } from '../types'
import { dur, hms, statusType, tok } from '../format'
import { roleVisual } from '../roles'
import { latestMessage, taskStatus, toActivity } from '../labels'
import RoleBadge from './RoleBadge.vue'

/** 低密度任务卡：角色 / 任务名 / 状态 · 进度 · 最新一句话 · ≤4 行人话活动。原始命令与 JSON 只在抽屉里看。 */
const props = defineProps<{ task: TaskSummary; now: number; rows?: number }>()
const emit = defineEmits<{ (e: 'open', key: string): void }>()

const vis = computed(() => roleVisual(props.task.role))
const stale = computed(() => props.task.status === 'RUNNING' && props.task.last_activity != null && props.now - props.task.last_activity > 300)
const steps = computed(() => (props.task.counts.command || 0) + (props.task.counts.mcp || 0) + (props.task.counts.web_search || 0) + (props.task.counts.file_change || 0))
const message = computed(() => latestMessage(props.task.recent) || props.task.last_message || '')
const activity = computed(() => {
  const rows = []
  for (let i = props.task.recent.length - 1; i >= 0 && rows.length < (props.rows || 4); i--) {
    const ev = props.task.recent[i]
    if (ev.kind === 'message') continue
    if (ev.kind === 'command' && ev.status === 'in_progress') continue
    const a = toActivity(ev)
    if (a) rows.unshift(a)
  }
  return rows
})
/** 运行中用“步数”做不定进度；结束了就满格 */
const percent = computed(() => props.task.status_group === 'RUNNING' ? Math.min(92, 10 + steps.value * 3) : 100)
const barStatus = computed(() => props.task.status_group === 'FAIL' || props.task.status_group === 'BLOCKED' ? 'error' : props.task.status_group === 'WARN' ? 'warning' : props.task.status_group === 'RUNNING' ? 'info' : 'success')
</script>

<template>
  <NCard size="small" class="tc" :class="task.status_group" hoverable @click="emit('open', task.key)">
    <div class="hd">
      <RoleBadge :role="task.role" :size="34" />
      <div class="titles">
        <div class="role">{{ vis.label }}</div>
        <NTooltip><template #trigger><div class="name mono">{{ task.name }}</div></template>{{ task.key }}</NTooltip>
      </div>
      <NTag size="small" :type="statusType(task.status_group)" round :bordered="false">
        {{ taskStatus(task.status_group, task.status) }}<template v-if="stale"> · 5 分钟无输出</template>
      </NTag>
    </div>
    <div class="prog">
      <NProgress type="line" :percentage="percent" :status="barStatus" :show-indicator="false" :height="6" :border-radius="3" :processing="task.status_group === 'RUNNING'" />
      <span class="prog-meta dim">
        {{ dur(task.elapsed) }} · 第 {{ steps }} 步
        <template v-if="task.tokens_in"> · 用量 {{ tok(task.tokens_in) }}</template>
      </span>
    </div>
    <p class="msg" v-if="message">{{ message }}</p>
    <p class="msg dim" v-else>等待第一条输出…</p>
    <ul class="acts">
      <li v-for="(a, i) in activity" :key="i" :class="a.tone">
        <span class="ic">{{ a.icon }}</span>
        <span class="lbl" v-if="a.label">{{ a.label }}</span>
        <span class="det ellipsis">{{ a.detail }}</span>
        <span class="ts mono dim">{{ hms(a.ts) }}</span>
      </li>
    </ul>
    <div v-if="task.validation" class="ft fail">未通过产物验收：{{ task.validation }}</div>
    <div v-else-if="task.expected.length && task.status_group !== 'RUNNING'" class="ft dim">交付产物：{{ task.expected.map((e) => e.split('/').pop()).join('、') }}</div>
  </NCard>
</template>

<style scoped>
.tc { cursor: pointer; height: 100%; }
.tc :deep(.n-card__content) { padding: 14px 16px 12px; display: flex; flex-direction: column; gap: 10px; }
.tc.RUNNING { box-shadow: 0 0 0 1px rgba(91,141,239,.45) inset; }
.hd { display: flex; align-items: center; gap: 12px; }
.titles { flex: 1; min-width: 0; }
.role { font-weight: 600; font-size: 14px; }
.name { color: #8a93a6; font-size: 11.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.prog { display: flex; align-items: center; gap: 10px; }
.prog :deep(.n-progress) { flex: 1; }
.prog-meta { font-size: 11.5px; white-space: nowrap; }
.msg { margin: 0; font-size: 13.5px; line-height: 1.55; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; color: #e6edf3; }
.acts { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
.acts li { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #c9d1d9; min-width: 0; }
.acts .ic { width: 16px; text-align: center; color: #8a93a6; flex: none; }
.acts .lbl { color: #9aa3b5; white-space: nowrap; flex: none; }
.acts .det { flex: 1; min-width: 0; }
.acts .ts { font-size: 11px; flex: none; }
.acts li.mcp .ic { color: #d2a8ff; } .acts li.file .ic { color: #7ee787; } .acts li.web .ic { color: #79c0ff; } .acts li.err .ic, .acts li.err .det { color: #f2726f; } .acts li.todo .ic { color: #e3b341; }
.ft { font-size: 11.5px; border-top: 1px solid rgba(255,255,255,.08); padding-top: 8px; }
.ft.fail { color: #f2726f; }
</style>
