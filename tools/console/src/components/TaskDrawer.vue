<script setup lang="ts">
import { ref, watch } from 'vue'
import { NCollapse, NCollapseItem, NDrawer, NDrawerContent, NSpace, NSpin, NTag, NText } from 'naive-ui'
import { api } from '../api'
import type { TaskDetail } from '../types'
import { dur, statusType, tok } from '../format'
import { roleVisual } from '../roles'
import EventLine from './EventLine.vue'
import RoleBadge from './RoleBadge.vue'

const props = defineProps<{ wsId: string; taskKey: string | null; showReasoning: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()
const detail = ref<TaskDetail | null>(null)
const loading = ref(false)

watch(() => props.taskKey, async (k) => {
  detail.value = null
  if (!k) return
  loading.value = true
  try { detail.value = await api.task(props.wsId, k) } finally { loading.value = false }
}, { immediate: true })
</script>

<template>
  <NDrawer :show="!!taskKey" :width="920" placement="right" @update:show="(v: boolean) => !v && emit('close')">
    <NDrawerContent closable :native-scrollbar="false">
      <template #header>
        <NSpace align="center" v-if="detail">
          <RoleBadge :role="detail.role" :size="36" />
          <span>{{ roleVisual(detail.role).label }} · <span class="mono">{{ detail.name }}</span></span>
          <NTag size="small" :type="statusType(detail.status_group)" round :bordered="false">{{ detail.status }}</NTag>
          <NText depth="3" class="mono" style="font-size: 12px">{{ detail.run_id }}</NText>
        </NSpace>
        <span v-else>任务详情</span>
      </template>
      <NSpin :show="loading">
        <template v-if="detail">
          <NText depth="3" style="font-size: 12px; display: block; margin-bottom: 8px">
            ⏱ {{ dur(detail.elapsed) }} · tok in {{ tok(detail.tokens_in) }} (cached {{ tok(detail.tokens_cached) }}) / out {{ tok(detail.tokens_out) }} · reasoning {{ tok(detail.tokens_reasoning) }}
            · exit {{ detail.exit ?? '—' }} · session {{ detail.thread_id || '—' }} · {{ detail.items_total }} 条事件
          </NText>
          <NText v-if="detail.expected.length" style="font-size: 12px; display: block; margin-bottom: 8px">
            声明产物：<span class="mono">{{ detail.expected.join(', ') }}</span>
            <template v-if="detail.dependencies.length">　依赖：<span class="mono">{{ detail.dependencies.join(', ') }}</span></template>
          </NText>
          <div v-if="detail.validation" style="color: #f2726f; margin-bottom: 8px">⛔ {{ detail.validation }}</div>
          <NCollapse :default-expanded-names="detail.final ? ['final'] : []" style="margin-bottom: 12px">
            <NCollapseItem v-if="detail.prompt_full" :title="`提示词（${detail.prompt_full.length} 字）`" name="prompt"><pre class="box">{{ detail.prompt_full }}</pre></NCollapseItem>
            <NCollapseItem v-if="detail.final" title="最终回复" name="final"><pre class="box">{{ detail.final }}</pre></NCollapseItem>
            <NCollapseItem v-if="detail.stderr" title="stderr" name="stderr"><pre class="box">{{ detail.stderr }}</pre></NCollapseItem>
          </NCollapse>
          <h4 style="margin: 6px 0; font-size: 12.5px; color: #8a93a6">事件流</h4>
          <EventLine v-for="(ev, i) in detail.items" :key="ev.item_id || i" :ev="ev" :show-reasoning="showReasoning" />
        </template>
      </NSpin>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
.box { white-space: pre-wrap; word-break: break-word; background: rgba(0,0,0,.35); padding: 8px 10px; border-radius: 6px; font-size: 12px; max-height: 420px; overflow: auto; }
</style>
