<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { NEmpty, NIcon, NInput, NSpin, NTooltip, useMessage } from 'naive-ui'
import { SearchOutline, ServerOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { McpServer } from '../types'
import { roleVisual } from '../roles'

const message = useMessage()
const servers = ref<McpServer[]>([])
const loading = ref(true), query = ref(''), expanded = ref<string | null>(null)
const labels: Record<string, string> = { 'goai-litsearch': '文献检索服务', 'goai-refcheck': '引用核查服务', 'goai-figure': '图纸渲染服务', 'goai-retro': '逆合成与方案服务' }
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return servers.value
  return servers.value.map(s => ({ ...s, tools: (s.id + (labels[s.id] || '') + s.summary).toLowerCase().includes(q) ? s.tools : s.tools.filter(t => (t.name + t.summary).toLowerCase().includes(q)) })).filter(s => s.tools.length)
})
onMounted(async () => {
  try { servers.value = (await api.mcp()).servers }
  catch (e) { message.error(`加载工具失败：${(e as Error).message}`) }
  finally { loading.value = false }
})
</script>

<template>
  <div class="page panel-page tools-page">
    <div class="tools-toolbar">
      <NInput v-model:value="query" clearable placeholder="搜索服务或工具" class="search"><template #prefix><NIcon><SearchOutline /></NIcon></template></NInput>
      <span v-if="!loading" class="dim small">{{ servers.filter(s => s.exists).length }} / {{ servers.length }} 项 MCP 服务在线 · {{ servers.reduce((sum, s) => sum + s.tools.length, 0) }} 个工具</span>
    </div>
    <NSpin :show="loading" class="panel-spin">
      <div v-if="filtered.length" class="services-grid">
        <section v-for="s in filtered" :key="s.id" class="sheet svc">
          <button type="button" class="svc-hd" :aria-expanded="expanded === s.id" @click="expanded = expanded === s.id ? null : s.id">
            <span class="svc-icon"><NIcon :size="24"><ServerOutline /></NIcon></span>
            <span class="svc-name"><strong>{{ labels[s.id] || s.id }}</strong><span class="dim small mono">{{ s.id }}</span></span>
            <span class="svc-status small"><span class="st-dot" :class="s.exists ? 'ok' : 'bad'" />{{ s.exists ? '在线' : '缺失' }}</span>
          </button>
          <div class="svc-body">
          <p class="dim small summary">{{ s.summary.replace(/^[^—]*——\s*/, '') }}</p>
          <div class="tools">
            <NTooltip v-for="t in s.tools" :key="t.name">
              <template #trigger><button type="button" class="mono tool" @click="expanded = s.id">{{ t.name }}</button></template>
              <div class="tool-tip"><b>{{ t.name }}</b>（{{ t.params.map(p => p.name).join(', ') || '无参数' }}）<div>{{ t.summary }}</div><div v-if="t.used_by.length">使用者：{{ t.used_by.map(u => roleVisual(u).label).join('、') }}</div></div>
            </NTooltip>
          </div>
          <div v-if="expanded === s.id" class="detail">
            <div v-for="t in s.tools" :key="t.name" class="trow small">
              <div class="mono">{{ t.name }}<span class="dim">({{ t.params.map(p => p.default != null ? `${p.name}=${p.default}` : p.name).join(', ') }})</span></div>
              <div class="dim">{{ t.summary }}</div>
            </div>
          </div>
          </div>
        </section>
      </div>
      <NEmpty v-if="!loading && !filtered.length" description="没有匹配的服务或工具" />
    </NSpin>
  </div>
</template>

<style scoped>
.tools-toolbar { display: flex; align-items: center; gap: 20px; margin-bottom: 18px; flex-wrap: wrap; }
.search { width: min(100%, 440px); }
.services-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); grid-auto-rows: minmax(0, 1fr); gap: 18px; height: 100%; min-height: 0; }
.svc { padding: 20px; min-width: 0; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.svc-body { flex: 1; min-height: 0; overflow: auto; padding-right: 4px; }
.svc-hd { display: flex; align-items: center; gap: 12px; background: none; border: 0; padding: 0; width: 100%; text-align: left; font: inherit; color: inherit; cursor: pointer; }
.svc-icon { width: 44px; height: 44px; border-radius: 10px; background: #EFEDE6; display: inline-flex; align-items: center; justify-content: center; flex: none; }
.svc-name { display: flex; flex-direction: column; gap: 3px; flex: 1; min-width: 0; overflow-wrap: anywhere; }
.svc-name strong { font-size: 16px; font-weight: 600; }.svc-status { white-space: nowrap; flex: none; }
.summary { margin: 14px 0; line-height: 1.7; overflow-wrap: anywhere; }
.tools { display: flex; flex-wrap: wrap; gap: 7px; align-items: flex-start; }
.tool { border: 1px solid var(--line-soft); background: #f0f2ec; color: var(--ink); border-radius: 6px; padding: 5px 8px; font-size: 12px; cursor: pointer; white-space: normal; overflow-wrap: anywhere; max-width: 100%; text-align: left; }.tool:hover { background: var(--verdigris-soft); }
.tool-tip { max-width: 420px; font-size: 12.5px; }.detail { border-top: 1px solid var(--line-soft); margin-top: 18px; padding-top: 6px; }.trow { padding: 9px 0; border-bottom: 1px dashed var(--line-soft); overflow-wrap: anywhere; }.trow > .dim { margin-top: 4px; }.footnote { margin-top: 16px; }
@media (max-width: 1050px) { .svc { padding: 14px; }.svc-hd { gap: 8px; }.svc-icon { width: 34px; height: 34px; }.svc-name strong { font-size: 14px; }.tools-toolbar { gap: 12px; } }
</style>
