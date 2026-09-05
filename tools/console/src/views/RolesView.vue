<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NIcon, NSpin, useMessage } from 'naive-ui'
import { AddOutline, DocumentTextOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { Role, StateResponse, WorkspaceInfo } from '../types'
import { DEFAULT_STAGES, STAGE_LABEL, roleVisual } from '../roles'
import { ago } from '../format'
import StageSpine from '../components/StageSpine.vue'
import RoleBadge from '../components/RoleBadge.vue'

const router = useRouter()
const message = useMessage()
const roles = ref<Role[]>([])
const chains = ref<{ name: string; desc: string; roles: string[] }[]>([])
const current = ref<WorkspaceInfo | null>(null)
const state = ref<StateResponse | null>(null)
const loading = ref(true)
let timer: number | undefined

async function loadCurrent() {
  const w = await api.workspaces()
  current.value = w.workspaces.find((x) => x.status === 'running') || w.workspaces.find((x) => x.topic) || null
  state.value = current.value ? await api.state(current.value.id, 0).catch(() => null) : null
}
onMounted(async () => {
  try {
    const r = await api.roles()
    roles.value = r.roles
    chains.value = r.chains
    await loadCurrent()
  } catch (e) {
    message.error(`加载失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
  timer = window.setInterval(loadCurrent, 6000)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

const byId = computed(() => Object.fromEntries(roles.value.map((r) => [r.id, r])))
const ledger = computed(() => state.value?.ledger || {})
const stageList = computed(() => { const s = ledger.value.stages; return s && s.some((x) => !DEFAULT_STAGES.includes(x)) ? s : DEFAULT_STAGES })
const stageNo = computed(() => { const idx = stageList.value.indexOf(ledger.value.stage || ''); return idx >= 0 ? idx + 1 : null })
const checks = computed(() => Object.values(ledger.value.gates || {}).filter((g) => g.status === 'PASS' || g.status === 'WARN').length)
/** 每个角色的实时状态：正在工作 / 已完成（本次运行里有通过的任务）/ 空闲 */
function roleStatus(id: string): { key: 'run' | 'ok' | 'wait'; label: string } {
  const tasks = (state.value?.tasks || []).filter((t) => t.role === id)
  if (current.value?.status === 'running' && tasks.some((t) => t.status_group === 'RUNNING')) return { key: 'run', label: '正在工作' }
  if (tasks.some((t) => t.status_group === 'PASS' || t.status_group === 'WARN')) return { key: 'ok', label: '已完成' }
  return { key: 'wait', label: '空闲' }
}
</script>

<template>
  <div class="page">
    <section class="top">
      <div class="hero">
        <h1 class="serif">让九个角色，共同写出<br>一篇可核验的综述</h1>
        <p class="dim">从一个研究主题出发，过程清楚，证据可追溯。</p>
        <div class="actions">
          <NButton type="primary" size="large" @click="router.push('/history?new=1')"><template #icon><NIcon><AddOutline /></NIcon></template>发起一项研究</NButton>
          <NButton size="large" @click="router.push('/results')"><template #icon><NIcon><DocumentTextOutline /></NIcon></template>查看最近成果</NButton>
        </div>
      </div>
      <div class="sheet panel ledger">
        <div class="card-h">共享运行账本</div>
        <template v-if="current">
          <StageSpine :ledger="ledger" :tasks="state?.tasks || []" dense />
          <div class="small dim" style="margin-top: 6px">11 个阶段，由下方三条链上的 9 个角色承担；节点下的色点是负责角色，悬停可看完成标准。</div>
          <div class="ledger-row">
            <div><span class="dim small">当前</span><span class="big">{{ stageNo ? String(stageNo).padStart(2, '0') : '—' }}</span><span class="dim"> / {{ stageList.length }}</span>
              <span class="stage-name">{{ ledger.stage ? (STAGE_LABEL[ledger.stage] || ledger.stage) : '尚未开始' }}</span></div>
            <div><span class="dim small">质量检查</span><span class="big amber">{{ checks }}</span><span class="dim"> / 9</span></div>
          </div>
          <div class="ledger-foot small">
            <span class="ellipsis" style="max-width: 360px" :title="current.topic">{{ current.topic }}</span>
            <span><span class="st-dot" :class="current.status === 'running' ? 'run' : current.status === 'done' ? 'ok' : 'wait'" />{{ current.status === 'running' ? '运行中' : current.status === 'done' ? '已交付' : current.status === 'stopped' ? '已终止' : '已结束' }}</span>
            <span class="dim">更新于 {{ ago(current.last_activity, Date.now() / 1000) }}</span>
            <NButton size="tiny" quaternary @click="router.push(`/run/${current.id}`)">打开观察 ›</NButton>
          </div>
        </template>
        <div v-else class="dim" style="padding: 20px 0">还没有研究运行。发起一项研究后，这里会显示它的阶段与质量检查。</div>
      </div>
    </section>

    <NSpin :show="loading">
      <section v-for="c in chains" :key="c.name" class="chain">
        <div class="sheet chain-label">
          <div class="card-h"><span class="st-dot ok" />{{ c.name }}</div>
          <div class="dim small">{{ c.desc }}</div>
        </div>
        <div class="chain-roles">
          <template v-for="(rid, i) in c.roles" :key="rid">
            <div class="sheet role" @click="router.push(`/roles/${rid}`)">
              <RoleBadge :role="rid" :size="48" :status="roleStatus(rid).key" />
              <div class="role-body">
                <div class="role-name">{{ roleVisual(rid).label }}</div>
                <div class="dim small verb">{{ byId[rid]?.verb }}</div>
                <div class="small status"><span class="st-dot" :class="roleStatus(rid).key" />{{ roleStatus(rid).label }}</div>
              </div>
            </div>
            <span v-if="i < c.roles.length - 1" class="link" />
          </template>
        </div>
      </section>
    </NSpin>

    <div class="sheet deliver small">
      <NIcon :size="18" color="#66737B"><DocumentTextOutline /></NIcon>
      研究最终交付：论文 PDF、TeX 源稿、经核验的参考文献与可编辑图纸；每一步都记录在共享运行账本里，可以回看。
    </div>
  </div>
</template>

<style scoped>
.top { display: grid; grid-template-columns: 5fr 7fr; gap: 24px; margin-bottom: 24px; align-items: stretch; }
.hero h1 { font-size: 34px; line-height: 44px; margin: 6px 0 10px; font-weight: 600; }
.hero p { margin: 0 0 22px; font-size: 15px; }
.actions { display: flex; gap: 12px; }
.ledger { padding: 18px 22px; }
.ledger .card-h { margin-bottom: 10px; }
.ledger-row { display: flex; gap: 40px; align-items: baseline; margin-top: 8px; }
.ledger-row .small { margin-right: 8px; }
.big { font-size: 32px; line-height: 40px; font-weight: 600; color: var(--verdigris); }
.big.amber { color: var(--amber); }
.stage-name { font-size: 18px; font-weight: 600; margin-left: 14px; }
.ledger-foot { display: flex; align-items: center; gap: 16px; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--line-soft); }
.chain { display: grid; grid-template-columns: 160px 1fr; gap: 16px; margin-bottom: 14px; }
.chain-label { padding: 14px 16px; display: flex; flex-direction: column; gap: 6px; justify-content: center; }
.chain-roles { display: flex; align-items: center; gap: 0; overflow-x: auto; }
.role { flex: 1; min-width: 200px; display: flex; gap: 14px; padding: 16px 18px; cursor: pointer; transition: box-shadow .18s; }
.role:hover { box-shadow: var(--shadow-float); }
.role-name { font-size: 15px; font-weight: 600; }
.verb { margin: 2px 0 8px; line-height: 18px; }
.status { color: var(--slate); }
.link { width: 26px; height: 1.5px; background: #C9CCC6; flex: none; }
.deliver { display: flex; align-items: center; gap: 10px; padding: 12px 18px; margin-top: 10px; color: var(--slate); }
@media (max-width: 1100px) { .top { grid-template-columns: 1fr; } .chain { grid-template-columns: 1fr; } }
</style>
