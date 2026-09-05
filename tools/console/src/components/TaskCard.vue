<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { NCard, NSpace, NTag, NText, NTooltip } from 'naive-ui'
import type { TaskSummary } from '../types'
import { dur, statusType, tok } from '../format'
import { roleVisual } from '../roles'
import EventLine from './EventLine.vue'
import RoleBadge from './RoleBadge.vue'

const props = defineProps<{ task: TaskSummary; now: number; showReasoning: boolean; autoscroll: boolean }>()
const emit = defineEmits<{ (e: 'open', key: string): void }>()

const body = ref<HTMLElement | null>(null)
const vis = computed(() => roleVisual(props.task.role))
const stale = computed(() => props.task.status === 'RUNNING' && props.task.last_activity != null && props.now - props.task.last_activity > 300)
const c = computed(() => props.task.counts || {})

watch(() => props.task.recent.length + (props.task.recent.at(-1)?.status || ''), async () => {
  if (!props.autoscroll || !body.value) return
  const el = body.value
  const nearBottom = el.scrollHeight - el.clientHeight - el.scrollTop < 40
  await nextTick()
  if (nearBottom) el.scrollTop = el.scrollHeight
})
</script>

<template>
  <NCard size="small" class="task-card" :class="task.status_group" :style="{ borderTop: `3px solid ${vis.color}` }" hoverable>
    <template #header>
      <div class="hd" @click="emit('open', task.key)">
        <RoleBadge :role="task.role" :size="26" />
        <span class="role">{{ vis.label }}</span>
        <NTooltip><template #trigger><span class="name mono">{{ task.name }}</span></template>{{ task.key }}</NTooltip>
      </div>
    </template>
    <template #header-extra>
      <NTag size="small" :type="statusType(task.status_group)" round :bordered="false">
        {{ task.status_group === 'RUNNING' ? '运行中' : task.status }}{{ stale ? ' · 5min 无输出' : '' }}
      </NTag>
    </template>
    <div class="meta dim">
      <span><b>耗时</b> {{ dur(task.elapsed) }}</span>
      <span><b>tok</b> {{ tok(task.tokens_in) }} / {{ tok(task.tokens_out) }}</span>
      <span><b>cmd</b> {{ c.command || 0 }}</span>
      <NTooltip><template #trigger><span><b>MCP</b> {{ c.mcp || 0 }}<template v-if="task.audit_calls">/{{ task.audit_calls }}</template></span></template>Codex 事件流里的 mcp_tool_call / 服务端审计归因到本任务的调用</NTooltip>
      <span><b>web</b> {{ c.web_search || 0 }}</span>
      <span><b>files</b> {{ c.file_change || 0 }}</span>
      <span v-if="task.exit != null">exit {{ task.exit }}<template v-if="task.process_exit && task.process_exit !== task.exit"> (proc {{ task.process_exit }})</template></span>
    </div>
    <div ref="body" class="body">
      <EventLine v-for="(ev, i) in task.recent" :key="ev.item_id || i" :ev="ev" :show-reasoning="showReasoning" compact />
      <NText v-if="!task.recent.length" depth="3" style="font-size: 12px">等待事件…</NText>
    </div>
    <div v-if="task.validation" class="ft fail">⛔ {{ task.validation }}</div>
    <div v-else-if="task.status_group === 'RUNNING' && task.current_command" class="ft mono">$ {{ task.current_command }}</div>
    <div v-else-if="task.final" class="ft pre">{{ task.final.slice(-420) }}</div>
    <div v-else-if="task.expected.length" class="ft">声明产物：{{ task.expected.join(', ') }}</div>
  </NCard>
</template>

<style scoped>
.task-card { display: flex; flex-direction: column; height: 460px; }
.task-card :deep(.n-card__content) { display: flex; flex-direction: column; flex: 1; min-height: 0; padding-top: 6px; }
.task-card.RUNNING { box-shadow: 0 0 0 1px rgba(91,141,239,.45) inset; }
.hd { display: flex; align-items: center; gap: 8px; cursor: pointer; min-width: 0; }
.role { font-weight: 600; white-space: nowrap; }
.name { color: #8a93a6; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta { display: flex; gap: 10px; flex-wrap: wrap; font-size: 11.5px; margin-bottom: 4px; } .meta b { font-weight: 500; color: #6f7a8f; }
.body { flex: 1; overflow: auto; min-height: 0; }
.ft { margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,.1); color: #8a93a6; font-size: 11.5px; max-height: 6em; overflow: hidden; }
.ft.fail { color: #f2726f; }
</style>
