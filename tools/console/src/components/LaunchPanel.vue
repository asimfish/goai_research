<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NAlert, NButton, NCollapse, NCollapseItem, NInput, NSelect, NSwitch, useMessage } from 'naive-ui'
import type { SelectOption } from 'naive-ui'
import { api } from '../api'
import type { ConsoleConfig } from '../types'

/** 「发起一项研究」纸张（DESIGN.md 页面 03）：一行主题 + 交付语言 + 私有语料开关；模型等放进高级选项。 */
const props = defineProps<{ config: ConsoleConfig | null; focus?: boolean }>()
const emit = defineEmits<{ (e: 'launched', id: string): void }>()
const message = useMessage()

const topic = ref('')
const language = ref<'zh' | 'en'>('zh')
const privateCorpus = ref(false)
const model = ref('')
const effort = ref('')
const slug = ref('')
const fallback = ref('')
const submitting = ref(false)
const input = ref<InstanceType<typeof NInput> | null>(null)

function fillDefaults() {
  if (!props.config) return
  model.value = model.value || props.config.model
  effort.value = effort.value || props.config.effort
  fallback.value = fallback.value || props.config.model_fallback || ''
  if (props.config.private_corpus_available && !topic.value) privateCorpus.value = true
}
watch(() => props.config, fillDefaults, { immediate: true })
watch(() => props.focus, (f) => { if (f) setTimeout(() => input.value?.focus(), 50) }, { immediate: true })

const modelOptions = computed(() => (props.config?.models || []).map((m) => ({ label: m, value: m })))
const effortOptions = computed(() => (props.config?.efforts || []).map((m) => ({ label: m, value: m })))
const effortLabel = (o: SelectOption) => `推理强度 ${o.label}`
const fallbackOptions = computed(() => [{ label: '不切换模型', value: '' }].concat((props.config?.models || []).filter((m) => m !== model.value).map((m) => ({ label: `容量不足时改用 ${m}`, value: m }))))
const loggedIn = computed(() => (props.config?.codex_login || '').includes('Logged in'))
const preview = computed(() => topic.value.trim().replace(/^调研主题：/, '').replace(/[。．.]$/, ''))

async function submit() {
  if (!preview.value) { message.warning('先填研究主题'); input.value?.focus(); return }
  submitting.value = true
  try {
    // 交付语言写进主题行：编排器定范围时以用户指定为准（skills/goai-orchestrator 语言契约）
    const topicLine = language.value === 'en' && !/english|英文/i.test(preview.value) ? `${preview.value}（English delivery）` : preview.value
    const r = await api.launch({ topic: topicLine, corpus: privateCorpus.value ? 'private' : 'public', model: model.value, effort: effort.value, slug: slug.value || undefined, model_fallback: fallback.value || undefined })
    message.success(`研究已开始：${r.path.split('/').pop()}`)
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
  <div class="sheet panel launch">
    <h2 class="serif">发起一项研究</h2>
    <NAlert v-if="config && !loggedIn" type="warning" :bordered="false" style="margin-bottom: 12px">
      Codex 尚未登录（{{ config.codex_home }}），启动后编排器可能立刻退出。
    </NAlert>
    <label class="lbl">研究主题</label>
    <NInput ref="input" v-model:value="topic" size="large" clearable placeholder="例如：钙钛矿太阳能电池的稳定性机制与表征方法" @keyup.enter="submit" />
    <div class="small dim preview">预览标题：{{ preview ? `${preview}综述` : '—' }}</div>

    <div class="seg">
      <button type="button" :class="{ on: language === 'zh' }" @click="language = 'zh'">中文交付</button>
      <button type="button" :class="{ on: language === 'en' }" @click="language = 'en'">English delivery</button>
    </div>

    <div class="sheet toggle">
      <div>
        <div class="card-h" style="font-size: 14px">接入私有语料</div>
        <div class="dim small">{{ config?.private_corpus_available ? '使用 NAS 上的全文 Parquet 库；仅在本次运行中使用，不会上传' : '服务端未配置私有语料，将使用随仓库提交的公开精简包' }}</div>
      </div>
      <NSwitch v-model:value="privateCorpus" :disabled="!config?.private_corpus_available" />
    </div>

    <NCollapse class="adv" arrow-placement="right">
      <NCollapseItem title="高级选项：模型与目录" name="adv">
        <div class="adv-row">
          <NSelect v-model:value="model" :options="modelOptions" size="small" filterable tag style="width: 180px" />
          <NSelect v-model:value="effort" :options="effortOptions" size="small" style="width: 150px" :render-label="effortLabel" />
          <NInput v-model:value="slug" size="small" placeholder="目录名后缀（可选）" style="width: 170px" />
        </div>
        <div class="adv-row" style="margin-top: 8px; align-items: center">
          <NSelect v-model:value="fallback" :options="fallbackOptions" size="small" style="width: 280px" />
          <span class="dim small">编排器连续三次遇到「模型容量不足」才切换，切换会记入账本</span>
        </div>
        <div class="dim small" style="margin-top: 8px">Codex 账号：<span class="mono">{{ config?.codex_email || '未知' }}</span> · {{ config?.codex_home }}</div>
        <div class="mono small dim" style="margin-top: 8px; word-break: break-all">bash scripts/reproduce_core.sh --topic "…" --workdir {{ config?.runs_root }}/&lt;时间戳&gt;_&lt;后缀&gt;</div>
      </NCollapseItem>
    </NCollapse>

    <div class="facts small dim">
      <span>11 个研究阶段</span><span>9 项质量检查</span><span>{{ model }} / {{ effort }}</span><span>可随时终止，过程可回放</span>
    </div>
    <NButton type="primary" size="large" block :loading="submitting" @click="submit" style="height: 48px; font-size: 16px">开始研究</NButton>
  </div>
</template>

<style scoped>
.launch { padding: 26px 28px 24px; }
.launch h2 { margin: 0 0 18px; font-size: 22px; line-height: 30px; }
.lbl { display: block; font-size: 13px; color: var(--slate); margin-bottom: 6px; }
.preview { margin: 6px 0 14px; }
.seg { display: grid; grid-template-columns: 1fr 1fr; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; margin-bottom: 14px; }
.seg button { border: 0; background: transparent; padding: 10px 0; font: inherit; color: var(--slate); cursor: pointer; }
.seg button.on { background: var(--verdigris-soft); color: var(--ink); font-weight: 600; }
.toggle { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 12px 16px; margin-bottom: 12px; }
.adv { margin-bottom: 8px; }
.adv-row { display: flex; gap: 10px; flex-wrap: wrap; }
.facts { display: flex; gap: 18px; margin: 14px 0 12px; }
.facts span::before { content: '◦ '; }
</style>
