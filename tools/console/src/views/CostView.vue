<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { NAlert, NButton, NCollapse, NCollapseItem, NInput, NSelect, NTabPane, NTabs, NTag, useMessage } from 'naive-ui'
import { api } from '../api'
import type { WorkspaceInfo } from '../types'
import { bucketLabel, buckets, costText, warningLabel } from '../billing'
import type { CostReport, PricingConfig } from '../billing'

const route = useRoute(), message = useMessage()
const selected = ref(typeof route.query.research === 'string' ? route.query.research : '')
const workspaces = ref<WorkspaceInfo[]>([]), report = ref<CostReport | null>(null)
const error = ref(''), busy = ref(false), activeTab = ref('researches')
const prices = ref<PricingConfig | null>(null), revision = ref(''), rawPrices = ref(''), newModel = ref('')
let timer: number | undefined
let pendingRefresh = false
const options = computed(() => [{ label: '全部研究与后续调用', value: '' }, ...workspaces.value.map(w => ({ label: w.topic || w.label, value: w.id }))])
const rows = computed(() => report.value ? report.value[activeTab.value as 'researches' | 'sessions' | 'tasks'] : [])
const summary = computed(() => report.value?.summary)
const names = computed(() => Object.fromEntries(workspaces.value.map(w => [w.id, w.topic || w.label])))
async function refresh() {
  if (busy.value) { pendingRefresh = true; return }
  busy.value = true
  const selection = selected.value
  try {
    const result = await api.costs(selection || undefined)
    if (selection === selected.value) report.value = result
    error.value = ''
  } catch (e) { error.value = String(e) } finally { busy.value = false }
  if (pendingRefresh) { pendingRefresh = false; void refresh() }
}
async function loadPrices() {
  const result = await api.prices()
  for (const entry of Object.values(result.config.models)) for (const key of buckets) entry.rates[key] = String(entry.rates[key])
  prices.value = result.config; revision.value = result.revision
  rawPrices.value = JSON.stringify(result.config, null, 2)
}
async function savePrices(raw = false) {
  try {
    const config = raw ? JSON.parse(rawPrices.value) as PricingConfig : prices.value!
    config.version = new Date().toISOString()
    await api.savePrices(config, revision.value); await loadPrices(); await refresh()
    message.success('价格表已保存；已有研究的价格快照保持不变')
  } catch (e) { message.error(String(e)) }
}
function addModel() {
  const name = newModel.value.trim()
  if (!prices.value || !name || prices.value.models[name]) return
  prices.value.models[name] = { aliases: [], rates: { input: '0', output: '0', cache_read: '0', cache_write: '0' } }
  newModel.value = ''
}
function download() {
  const blob = new Blob([JSON.stringify(report.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob), a = document.createElement('a'); a.href = url; a.download = 'usage-cost.json'; a.click(); URL.revokeObjectURL(url)
}
onMounted(async () => {
  try { workspaces.value = (await api.workspaces()).workspaces; await loadPrices(); await refresh() }
  catch (e) { error.value = String(e) }
  timer = window.setInterval(refresh, 10000)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="page costs">
    <div class="heading"><div><h1>算力 / 费用统计</h1><p class="dim">研究启动、模型会话与后续 MCP 调用，使用同一份费用记录。</p></div><NButton :loading="busy" @click="refresh">刷新</NButton><NButton :disabled="!report" @click="download">导出 JSON</NButton></div>
    <NSelect v-model:value="selected" :options="options" filterable @update:value="refresh" style="max-width: 700px; margin-bottom: 18px" />
    <NAlert v-if="error" type="error">{{ error }}</NAlert>
    <template v-if="summary">
      <div class="cards">
        <section class="sheet"><div class="dim">已计金额</div><strong data-testid="cost-total">{{ costText(summary) }}</strong><NTag size="small" :type="summary.status === 'partial' ? 'warning' : 'info'">{{ summary.status === 'partial' ? '部分用量或单价缺失' : summary.status === 'estimated' ? '按配置费率折算' : '计价完整' }}</NTag></section>
        <section class="sheet"><div class="dim">有用量回执</div><strong>{{ summary.usage_records }}</strong><span class="dim">{{ summary.missing_usage }} 条缺少完整用量</span></section>
        <section class="sheet"><div class="dim">MCP 调用</div><strong>{{ summary.mcp_calls }}</strong><span class="dim">已知工具耗时 {{ (summary.mcp_duration_ms / 1000).toFixed(2) }} 秒</span></section>
      </div>
      <div class="sheet panel">
        <h2>四类用量与费用</h2>
        <table><thead><tr><th>计费项</th><th>实际 token</th><th v-for="(_, currency) in summary.currencies" :key="currency">{{ currency }}</th></tr></thead>
          <tbody><tr v-for="key in buckets" :key="key"><td>{{ bucketLabel[key] }}</td><td class="mono">{{ summary.tokens[key].toLocaleString() }}</td><td v-for="(value, currency) in summary.currencies" :key="currency" class="mono">{{ value.token_costs[key] }}</td></tr>
            <tr><td>MCP 工具服务费</td><td>按工具配置计费</td><td v-for="(value, currency) in summary.currencies" :key="currency" class="mono">{{ value.tools }}</td></tr></tbody></table>
        <p class="dim small">普通输入已扣除缓存读取与写入；推理 token 已含在输出中。MCP 返回内容引起的模型用量已在模型回执内，不再次按调用次数收 token 费。本机 MCP 默认无额外服务费。</p>
      </div>
      <div class="sheet panel">
        <NTabs v-model:value="activeTab" type="line">
          <NTabPane name="researches"><template #tab>单次研究</template></NTabPane>
          <NTabPane name="sessions"><template #tab>单个会话</template></NTabPane>
          <NTabPane name="tasks"><template #tab>整轮任务</template></NTabPane>
        </NTabs>
        <p class="dim small" v-if="activeTab === 'tasks'">同一整轮任务编号可以包含多个研究和后续调用；未指定时，一次研究及其全部子任务归为一轮。</p>
        <div class="scroll"><table><thead><tr><th>名称 / 编号</th><th>Input</th><th>Output</th><th>Cache read</th><th>Cache write</th><th>MCP</th><th>已计金额</th><th>缺少计价</th></tr></thead><tbody>
          <tr v-for="row in rows" :key="row.id"><td :title="row.id">{{ activeTab === 'researches' ? (names[row.id] || row.id) : row.id }}</td><td v-for="key in buckets" :key="key" class="mono">{{ row.tokens[key].toLocaleString() }}</td><td>{{ row.mcp_calls }}</td><td class="mono">{{ costText(row) }}</td><td>{{ row.unpriced_records }}</td></tr>
        </tbody></table></div>
      </div>
      <NCollapse class="sheet panel"><NCollapseItem title="统计完整性与计价依据" name="coverage">
        <p>按实际用量和所选价格表计算，金额不等同于订阅账户或第三方服务商账单。缺少回执的失败会话会保留在统计中。</p>
        <p v-if="report?.duplicates_ignored">已排除 {{ report.duplicates_ignored }} 条来自副本或回放目录的重复记录。</p>
        <ul><li v-for="(count, key) in summary.warnings" :key="key">{{ warningLabel[key] || key }}：{{ count }} 条</li></ul>
        <p class="dim small">更新于 {{ report?.generated_at }} · {{ report?.price_config }}</p>
      </NCollapseItem></NCollapse>
    </template>
    <div class="sheet panel" v-if="prices">
      <div class="heading"><h2>价格表 · {{ prices.currency }} / 百万 token</h2><NButton type="primary" @click="savePrices(false)">保存价格</NButton></div>
      <p class="dim small">新研究保存启动时的价格快照。历史记录没有快照时，按当前价格折算；修改下表会更新这些历史记录的折算结果。</p>
      <div class="scroll"><table><thead><tr><th>模型</th><th v-for="key in buckets" :key="key">{{ bucketLabel[key] }}</th></tr></thead><tbody><tr v-for="(entry, model) in prices.models" :key="model"><td>{{ model }}<div class="dim small">{{ entry.aliases?.join(' / ') }}</div></td><td v-for="key in buckets" :key="key"><NInput v-model:value="entry.rates[key]" size="small" :input-props="{ 'aria-label': `${model} ${key}` }" /></td></tr></tbody></table></div>
      <div class="add"><NInput v-model:value="newModel" placeholder="新增模型 ID" style="max-width: 280px" /><NButton @click="addModel">添加模型</NButton></div>
      <NCollapse><NCollapseItem title="高级配置：别名、服务档位、峰谷价与 MCP 服务费" name="json"><NInput v-model:value="rawPrices" type="textarea" :autosize="{ minRows: 8, maxRows: 20 }" /><NButton style="margin-top: 12px" @click="savePrices(true)">保存高级配置</NButton></NCollapseItem></NCollapse>
    </div>
  </div>
</template>

<style scoped>
.heading { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }.heading > :first-child { flex: 1; }.heading h1, .heading h2 { margin: 0; }.heading p { margin: 6px 0 0; }
.cards { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 16px; margin-bottom: 18px; }.cards section { padding: 20px; display: flex; flex-direction: column; align-items: flex-start; gap: 9px; }.cards strong { font-size: 25px; font-variant-numeric: tabular-nums; }
.panel { padding: 22px; margin-bottom: 18px; }.panel h2 { font-size: 18px; }.scroll { overflow-x: auto; }table { width: 100%; border-collapse: collapse; font-size: 13px; }th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--line); }th { color: var(--slate); font-weight: 500; }td:first-child { max-width: 330px; overflow-wrap: anywhere; }td.mono { white-space: nowrap; }.add { display: flex; gap: 10px; margin: 16px 0; }
@media (max-width: 900px) { .cards { grid-template-columns: 1fr; }.heading { flex-wrap: wrap; } }
@media (max-width: 700px) {
  .costs { padding: 20px 16px; }.heading > :first-child { flex-basis: 100%; }.panel { box-sizing: border-box; }
  .heading h1 { font-size: 24px; }.panel { padding: 16px; }.cards strong { font-size: 22px; }
  .panel > table { display: block; overflow-x: auto; }.add { flex-wrap: wrap; }
}
</style>
