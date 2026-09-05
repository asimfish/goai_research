<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  NAlert, NButton, NCard, NIcon, NInput, NRadioButton, NRadioGroup, NSelect, NSpace, NText, NTooltip, useMessage,
} from 'naive-ui'
import type { SelectOption } from 'naive-ui'
import { PlayOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { ConsoleConfig } from '../types'

const props = defineProps<{ config: ConsoleConfig | null; focus?: boolean }>()
const emit = defineEmits<{ (e: 'launched', id: string): void }>()
const message = useMessage()

const topic = ref('')
const corpus = ref<'public' | 'private'>('public')
const model = ref('')
const effort = ref('')
const slug = ref('')
const submitting = ref(false)
const input = ref<InstanceType<typeof NInput> | null>(null)

function fillDefaults() {
  if (!props.config) return
  model.value = model.value || props.config.model
  effort.value = effort.value || props.config.effort
  if (props.config.private_corpus_available && !topic.value) corpus.value = 'private'
}
watch(() => props.config, fillDefaults, { immediate: true })
watch(() => props.focus, (f) => { if (f) input.value?.focus() }, { immediate: true })

const modelOptions = computed(() => (props.config?.models || []).map((m) => ({ label: m, value: m })))
const effortOptions = computed(() => (props.config?.efforts || []).map((m) => ({ label: m, value: m })))
const loggedIn = computed(() => (props.config?.codex_login || '').includes('Logged in'))
const effortLabel = (o: SelectOption) => `推理强度 ${o.label}`
const cmd = computed(() => `GOAI_CORPUS=${corpus.value} GOAI_MODEL=${model.value} GOAI_REASONING_EFFORT=${effort.value} bash scripts/reproduce_core.sh --topic "…" --workdir ${props.config?.runs_root || 'workspace_runs/console'}/<时间戳>_${slug.value || '<主题前40字>'}`)

async function submit() {
  if (!topic.value.trim()) { message.warning('先填研究主题'); input.value?.focus(); return }
  submitting.value = true
  try {
    const r = await api.launch({ topic: topic.value.trim(), corpus: corpus.value, model: model.value, effort: effort.value, slug: slug.value || undefined })
    message.success(`已启动：${r.path.split('/').pop()}（pid ${r.pid}）`)
    emit('launched', r.id)
    topic.value = ''; slug.value = ''
  } catch (e) {
    message.error(`启动失败：${(e as Error).message}`)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <NCard size="small" class="launch">
    <template #header><span style="font-weight: 600">发起新研究</span> <NText depth="3" style="font-size: 12px; margin-left: 8px">一行主题就是发给编排器的全部输入</NText></template>
    <NAlert v-if="config && !loggedIn" type="warning" :bordered="false" style="margin-bottom: 10px">
      当前 CODEX_HOME（{{ config.codex_home }}）{{ config.codex_login || '未探测到登录状态' }}，启动后编排器可能立刻退出；5090 上请用 <code>--codex-home ~/.codex_rev</code> 启动控制台。
    </NAlert>
    <NInput ref="input" v-model:value="topic" size="large" clearable
      placeholder="输入一行研究主题，例如：Ba5Y12Zn[O(SiO4)]8及其结构相近化合物的合成条件" @keyup.enter="submit" />
    <div class="controls">
      <NRadioGroup v-model:value="corpus" size="small">
        <NRadioButton value="public">公开精简包</NRadioButton>
        <NTooltip :disabled="!!config?.private_corpus_available"><template #trigger>
          <NRadioButton value="private" :disabled="!config?.private_corpus_available">私有全库</NRadioButton>
        </template>服务端未配置私有语料（--private-corpus-env）</NTooltip>
      </NRadioGroup>
      <NSelect v-model:value="model" :options="modelOptions" size="small" filterable tag style="width: 170px" />
      <NSelect v-model:value="effort" :options="effortOptions" size="small" style="width: 150px" :render-label="effortLabel" />
      <NInput v-model:value="slug" size="small" placeholder="目录名后缀（可选）" style="width: 180px" />
      <span style="flex: 1" />
      <NButton type="primary" :loading="submitting" @click="submit">
        <template #icon><NIcon><PlayOutline /></NIcon></template>启动编排器
      </NButton>
    </div>
    <NText depth="3" class="mono hint">等价命令：{{ cmd }}</NText>
  </NCard>
</template>

<style scoped>
.controls { display: flex; align-items: center; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
.hint { display: block; font-size: 11.5px; margin-top: 8px; word-break: break-all; }
</style>
