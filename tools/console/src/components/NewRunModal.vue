<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  NAlert, NButton, NForm, NFormItem, NInput, NModal, NRadio, NRadioGroup, NSelect, NSpace, NText, useMessage,
} from 'naive-ui'
import { api } from '../api'
import type { ConsoleConfig } from '../types'

const props = defineProps<{ show: boolean; config: ConsoleConfig | null }>()
const emit = defineEmits<{ (e: 'update:show', v: boolean): void; (e: 'launched', id: string): void }>()
const message = useMessage()

const topic = ref('')
const corpus = ref<'public' | 'private'>('public')
const model = ref('')
const effort = ref('')
const slug = ref('')
const submitting = ref(false)

function fillDefaults() {
  if (!props.config) return
  model.value = model.value || props.config.model
  effort.value = effort.value || props.config.effort
  if (props.config.private_corpus_available && !topic.value) corpus.value = 'private'
}
watch(() => props.show, (v) => { if (v) fillDefaults() })
watch(() => props.config, () => fillDefaults(), { immediate: true })

const modelOptions = computed(() => (props.config?.models || []).map((m) => ({ label: m, value: m })))
const effortOptions = computed(() => (props.config?.efforts || []).map((m) => ({ label: m, value: m })))
const loggedIn = computed(() => (props.config?.codex_login || '').includes('Logged in'))

async function submit() {
  if (!topic.value.trim()) { message.warning('先填研究主题'); return }
  submitting.value = true
  try {
    const r = await api.launch({ topic: topic.value.trim(), corpus: corpus.value, model: model.value, effort: effort.value, slug: slug.value || undefined })
    message.success(`已启动：${r.path.split('/').pop()}（pid ${r.pid}）`)
    emit('update:show', false)
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
  <NModal :show="show" @update:show="(v: boolean) => emit('update:show', v)" preset="card" title="发起新的研究主题" style="width: 680px" :mask-closable="false">
    <NAlert v-if="config && !loggedIn" type="warning" :bordered="false" style="margin-bottom: 12px">
      当前 CODEX_HOME（{{ config.codex_home }}）显示 {{ config.codex_login || '未探测到登录状态' }}。启动后编排器可能立刻退出；
      在 5090 上请用 <code>--codex-home ~/.codex_rev</code> 启动控制台。
    </NAlert>
    <NForm label-placement="top">
      <NFormItem label="研究主题（这是发给编排器的唯一输入，一行即可）">
        <NInput v-model:value="topic" type="textarea" :autosize="{ minRows: 2, maxRows: 5 }"
          placeholder="例：Ba5Y12Zn[O(SiO4)]8及其结构相近化合物的合成条件" />
      </NFormItem>
      <NFormItem label="全文语料">
        <NRadioGroup v-model:value="corpus">
          <NSpace>
            <NRadio value="public">公开精简包（21 篇被引全文，随仓库提交）</NRadio>
            <NRadio value="private" :disabled="!config?.private_corpus_available">
              私有全库（NAS Parquet{{ config?.private_corpus_available ? '' : '，服务端未配置' }}）
            </NRadio>
          </NSpace>
        </NRadioGroup>
      </NFormItem>
      <NSpace :size="16">
        <NFormItem label="模型" style="min-width: 220px"><NSelect v-model:value="model" :options="modelOptions" filterable tag /></NFormItem>
        <NFormItem label="推理强度" style="min-width: 160px"><NSelect v-model:value="effort" :options="effortOptions" /></NFormItem>
        <NFormItem label="目录名后缀（可选）" style="min-width: 200px"><NInput v-model:value="slug" placeholder="默认取主题前 40 字" /></NFormItem>
      </NSpace>
      <NText depth="3" style="font-size: 12px; display: block">
        等价命令：<code class="mono">GOAI_CORPUS={{ corpus }} GOAI_MODEL={{ model }} GOAI_REASONING_EFFORT={{ effort }} bash scripts/reproduce_core.sh --topic "…" --workdir {{ config?.runs_root }}/&lt;时间戳&gt;_&lt;后缀&gt;</code>
        ；进程独立会话运行，关闭浏览器不影响；「终止」向整个进程组发 SIGTERM。
      </NText>
    </NForm>
    <template #footer>
      <NSpace justify="end">
        <NButton @click="emit('update:show', false)">取消</NButton>
        <NButton type="primary" :loading="submitting" @click="submit">启动编排器</NButton>
      </NSpace>
    </template>
  </NModal>
</template>
