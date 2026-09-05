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
.ev { padding: 3px 0; border-bottom: 1px dashed rgba(255,255,255,.08); font-size: 12.5px; word-break: break-word; line-height: 1.5; }
.t { color: #8a93a6; font-size: 11px; margin-right: 6px; }
.ev.message { color: #e6edf3; } .ev.reasoning { color: #9aa3b5; font-style: italic; }
.ev.command .mono { color: #c9d1d9; font-size: 12px; }
.out { color: #8a93a6; display: block; max-height: 7em; overflow: hidden; font-size: 11px; white-space: pre-wrap; margin-top: 2px; }
.ev.mcp { color: #d2a8ff; } .ev.web_search { color: #79c0ff; } .ev.file_change { color: #7ee787; } .ev.error { color: #f2726f; }
.ev.todo { color: #e3b341; } .todo-item { display: block; margin-left: 1.5em; font-size: 12px; }
.ev.usage, .ev.thread, .ev.status, .ev.raw { color: #8a93a6; font-size: 11.5px; }
</style>
