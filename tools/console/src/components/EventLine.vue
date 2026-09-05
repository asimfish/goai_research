<script setup lang="ts">
import { computed } from 'vue'
import type { EventItem } from '../types'
import { hms, tok } from '../format'

const props = defineProps<{ ev: EventItem; showReasoning?: boolean; compact?: boolean }>()

const visible = computed(() => {
  const e = props.ev
  if (e.kind === 'reasoning' && !props.showReasoning) return false
  return ['message', 'reasoning', 'command', 'mcp', 'web_search', 'file_change', 'todo', 'usage', 'error', 'thread', 'status', 'raw'].includes(e.kind)
})
const cmdRc = computed(() => {
  const e = props.ev
  if (e.exit_code == null) return e.status === 'in_progress' ? '…' : ''
  return `exit ${e.exit_code}`
})
const todoDone = computed(() => (props.ev.items || []).filter((i) => i.completed).length)
const fileList = computed(() => (props.ev.changes || []).slice(0, 8).map((c) => `${c.kind}:${String(c.path).split('/').pop()}`).join(', '))
</script>

<template>
  <div v-if="visible" class="ev" :class="ev.kind">
    <span class="t mono">{{ hms(ev.ts) }}</span>
    <template v-if="ev.kind === 'message'">💬 <span class="pre">{{ ev.text }}</span></template>
    <template v-else-if="ev.kind === 'reasoning'">🧠 <span class="pre">{{ ev.text }}</span></template>
    <template v-else-if="ev.kind === 'command'">
      <span class="mono">$ {{ ev.command }}</span> <span class="t">{{ cmdRc }}</span>
      <div v-if="ev.output && !compact" class="out mono">{{ ev.output.slice(-800) }}</div>
    </template>
    <template v-else-if="ev.kind === 'mcp'">
      🔧 <span class="mono">{{ ev.server }}.{{ ev.tool }}({{ (ev.arguments || '').slice(0, 220) }})</span>
      <span class="t"> {{ ev.error ? '⚠ ' + ev.error : (ev.result ? ev.result.slice(0, 300) : ev.status) }}</span>
    </template>
    <template v-else-if="ev.kind === 'web_search'">🌐 {{ ev.query }}</template>
    <template v-else-if="ev.kind === 'file_change'">✎ {{ fileList }}</template>
    <template v-else-if="ev.kind === 'todo'">
      ☑ {{ todoDone }}/{{ (ev.items || []).length }}
      <span v-for="(i, k) in ev.items" :key="k" class="todo-item">{{ i.completed ? '✓' : '○' }} {{ i.text }}</span>
    </template>
    <template v-else-if="ev.kind === 'usage'">
      Σ in {{ tok(ev.usage?.input_tokens) }} (cached {{ tok(ev.usage?.cached_input_tokens) }}) · out {{ tok(ev.usage?.output_tokens) }} · reasoning {{ tok(ev.usage?.reasoning_output_tokens) }}
    </template>
    <template v-else-if="ev.kind === 'error'">⚠ {{ ev.text }}</template>
    <template v-else-if="ev.kind === 'thread'">▶ session {{ ev.text }}</template>
    <template v-else-if="ev.kind === 'status'">■ {{ ev.text }}</template>
    <template v-else>· {{ ev.text }}</template>
  </div>
</template>

<style scoped>
.ev { padding: 3px 0; border-bottom: 1px dashed var(--line-soft); font-size: 12.5px; word-break: break-word; line-height: 1.5; }
.t { color: var(--slate); font-size: 11px; margin-right: 6px; }
.ev.message { color: var(--ink); } .ev.reasoning { color: var(--slate); font-style: italic; }
.ev.command .mono { color: #2F3F4A; font-size: 12px; }
.out { color: var(--slate); display: block; max-height: 7em; overflow: hidden; font-size: 11px; white-space: pre-wrap; margin-top: 2px; background: #EEEDE6; padding: 4px 8px; border-radius: 6px; }
.ev.mcp { color: #5B3E8C; } .ev.web_search { color: #2A5D8F; } .ev.file_change { color: var(--verdigris); } .ev.error { color: var(--cinnabar); }
.ev.todo { color: var(--amber); } .todo-item { display: block; margin-left: 1.5em; font-size: 12px; }
.ev.usage, .ev.thread, .ev.status, .ev.raw { color: var(--slate); font-size: 11.5px; }
</style>
