<script setup lang="ts">
import { computed } from 'vue'
import { NIcon, NTooltip } from 'naive-ui'
import { CheckmarkOutline, RefreshOutline } from '@vicons/ionicons5'
import type { LedgerSummary } from '../types'
import { GATE_ORDER } from '../roles'
import { checkStatus, gateLabel } from '../labels'

/** 九项质量检查的 3×3 印章矩阵：通过 = 实心圈勾，警告 = 琥珀叹号，未通过 = 朱砂，返工中 = 回转箭头，待完成 = 空心圈 */
const props = defineProps<{ ledger: LedgerSummary; dense?: boolean }>()
const rows = computed(() => GATE_ORDER.map((g) => {
  const info = props.ledger.gates?.[g]
  const st = info?.status || 'PENDING'
  const rework = (props.ledger.open_issues || []).some((i) => i.target && g.startsWith(i.target.split('_')[0]))
  return { id: g, status: st, detail: info?.detail || '', round: info?.round, rework: rework && st !== 'PASS' }
}))
const passed = computed(() => rows.value.filter((r) => r.status === 'PASS' || r.status === 'WARN').length)
</script>

<template>
  <div class="stamps" :class="{ dense }">
    <div class="count" v-if="!dense"><span class="big">{{ passed }}</span><span class="dim"> / {{ rows.length }} 已通过</span></div>
    <div class="grid">
      <NTooltip v-for="r in rows" :key="r.id" :disabled="!r.detail && !r.rework">
        <template #trigger>
          <div class="stamp" :class="[r.status, { rework: r.rework }]">
            <span class="mark">
              <NIcon v-if="r.status === 'PASS'" :size="dense ? 12 : 16"><CheckmarkOutline /></NIcon>
              <NIcon v-else-if="r.rework" :size="dense ? 12 : 16"><RefreshOutline /></NIcon>
              <span v-else-if="r.status === 'WARN'">!</span>
              <span v-else-if="r.status === 'FAIL'">×</span>
            </span>
            <span class="nm">{{ gateLabel(r.id) }}</span>
            <span v-if="!dense" class="st small dim">{{ r.rework ? '返工中' : checkStatus(r.status) }}</span>
          </div>
        </template>
        <div style="max-width: 400px; font-size: 12.5px"><b>{{ gateLabel(r.id) }}</b>（{{ r.id }}）· {{ checkStatus(r.status) }}{{ r.round ? ` · 第 ${r.round} 轮` : '' }}<div v-if="r.detail">{{ r.detail }}</div></div>
      </NTooltip>
    </div>
  </div>
</template>

<style scoped>
.count { margin-bottom: 10px; } .big { font-size: 32px; line-height: 40px; font-weight: 600; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.stamp { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; padding: 10px 6px; border: 1px solid var(--line); border-radius: 10px; background: #FBFAF7; text-align: center; min-height: 78px; }
.dense .stamp { min-height: 46px; padding: 6px 4px; }
.mark { width: 26px; height: 26px; border-radius: 50%; border: 1.5px solid #9AA6AE; display: inline-flex; align-items: center; justify-content: center; color: #66737B; font-weight: 700; font-size: 13px; }
.dense .mark { width: 20px; height: 20px; }
.stamp.PASS .mark { background: var(--verdigris); border-color: var(--verdigris); color: #fff; }
.stamp.WARN .mark { background: var(--amber-soft); border-color: var(--amber); color: var(--amber); }
.stamp.FAIL .mark { background: var(--cinnabar-soft); border-color: var(--cinnabar); color: var(--cinnabar); }
.stamp.rework .mark { border-color: var(--amber); color: var(--amber); background: var(--amber-soft); }
.stamp.rework { border-color: var(--amber); }
.nm { font-size: 12px; color: var(--ink); }
.dense .nm { font-size: 11px; }
</style>
