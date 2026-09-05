<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NEmpty, NTag, NTooltip } from 'naive-ui'
import type { LedgerSummary } from '../types'
import { GATE_ORDER } from '../roles'
import { checkStatus, gateLabel, SEVERITY_LABEL } from '../labels'
import { statusType } from '../format'

/** 右侧“质量检查”栏：9 个必需检查项（账本 gate）+ 待处理审稿意见 */
const props = defineProps<{ ledger: LedgerSummary }>()
const rows = computed(() => {
  const gates = props.ledger.gates || {}
  const known = GATE_ORDER.map((g) => ({ id: g, ...(gates[g] || { status: null, detail: '', round: null }) }))
  const extra = Object.keys(gates).filter((g) => !GATE_ORDER.includes(g)).map((g) => ({ id: g, ...gates[g] }))
  return [...known, ...extra]
})
const passed = computed(() => rows.value.filter((r) => r.status === 'PASS' || r.status === 'WARN').length)
</script>

<template>
  <NCard size="small" class="rail">
    <template #header><span style="font-weight: 600">质量检查</span> <span class="dim" style="font-size: 12px; margin-left: 6px">{{ passed }}/{{ rows.length }} 已通过</span></template>
    <div v-if="!ledger.stage" class="dim" style="font-size: 12.5px">运行账本尚未初始化。</div>
    <div v-for="r in rows" :key="r.id" class="row">
      <div class="nm">
        <div>{{ gateLabel(r.id) }}</div>
        <div class="mono dim" style="font-size: 10.5px">{{ r.id }}{{ r.round ? ` · 第 ${r.round} 轮` : '' }}</div>
      </div>
      <NTooltip :disabled="!r.detail"><template #trigger>
        <NTag size="small" :type="statusType(r.status || 'PENDING')" :bordered="false" round>{{ checkStatus(r.status) }}</NTag>
      </template><div style="max-width: 380px">{{ r.detail }}</div></NTooltip>
    </div>
    <div class="issues">
      <div class="sub">审稿意见 <span class="dim">{{ ledger.open_issues?.length || 0 }} 条待处理 / 共 {{ ledger.issues_total || 0 }} 条</span></div>
      <div v-for="i in ledger.open_issues || []" :key="i.id" class="issue">
        <NTag size="tiny" :type="i.severity === 'blocker' ? 'error' : i.severity === 'major' ? 'warning' : 'default'" :bordered="false">{{ SEVERITY_LABEL[i.severity] || i.severity }}</NTag>
        <span class="dim">→ {{ gateLabel(i.target) === i.target ? i.target : i.target }}</span>
        <span class="txt">{{ i.text }}</span>
      </div>
      <NEmpty v-if="ledger.stage && !(ledger.open_issues || []).length" description="没有待处理的审稿意见" size="small" style="margin: 8px 0" />
    </div>
  </NCard>
</template>

<style scoped>
.row { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,.06); }
.nm { font-size: 13px; }
.issues { margin-top: 10px; }
.sub { font-size: 12.5px; font-weight: 600; margin-bottom: 4px; }
.issue { font-size: 12px; padding: 5px 0; border-bottom: 1px dashed rgba(255,255,255,.08); display: flex; gap: 6px; align-items: flex-start; flex-wrap: wrap; }
.issue .txt { flex-basis: 100%; color: #c9d1d9; }
</style>
