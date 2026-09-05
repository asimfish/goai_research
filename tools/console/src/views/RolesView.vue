<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NCard, NEmpty, NGi, NGrid, NIcon, NSpin, NTag, NText, useMessage } from 'naive-ui'
import { CheckmarkCircleOutline, GitNetworkOutline, HardwareChipOutline, LayersOutline, PeopleOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { Role, RolesStats } from '../types'
import { STAGE_LABEL, roleVisual } from '../roles'
import { gateLabel } from '../labels'
import StageStepper from '../components/StageStepper.vue'
import RoleBadge from '../components/RoleBadge.vue'

const router = useRouter()
const message = useMessage()
const roles = ref<Role[]>([])
const stats = ref<RolesStats | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const r = await api.roles()
    roles.value = r.roles
    stats.value = r.stats
  } catch (e) {
    message.error(`加载角色失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
})

const kpis = computed(() => stats.value ? [
  { label: '角色', value: stats.value.roles, icon: PeopleOutline, sub: '每个角色一份工作规程' },
  { label: 'MCP 服务 · 工具', value: `${stats.value.mcp_servers} · ${stats.value.mcp_tools}`, icon: HardwareChipOutline, sub: stats.value.servers.join(' / ') },
  { label: '质量检查项', value: stats.value.gates, icon: CheckmarkCircleOutline, sub: '全部通过才算交付' },
  { label: '工作区', value: stats.value.runs, icon: LayersOutline, sub: '含历史与正在运行' },
] : [])
function stageName(r: Role) { const s = roleVisual(r.id).stage; return STAGE_LABEL[s] || r.stage }
function gateNames(r: Role) { return r.gate.split('·').map((g) => gateLabel(g.trim())).join(' · ') }
</script>

<template>
  <div class="page">
    <div class="page-title">
      <div>
        <h1>九个角色，一条账本驱动的回环</h1>
        <NText depth="3">SAGE-Mat 由九个专职角色组成：每个角色一份工作规程（<code>skills/&lt;role&gt;/SKILL.md</code>）和一组可用工具。编排器按阶段派活、按完成标准验收、把审稿意见路由回对应角色返工，直到全部检查通过。</NText>
      </div>
    </div>

    <NGrid cols="2 m:4" responsive="screen" :x-gap="12" :y-gap="12" style="margin-bottom: 14px">
      <NGi v-for="k in kpis" :key="k.label">
        <NCard size="small">
          <div class="kpi-row">
            <span class="kpi-icon"><NIcon :size="22"><component :is="k.icon" /></NIcon></span>
            <div><div class="kpi-value">{{ k.value }}</div><div class="kpi-label">{{ k.label }}</div></div>
          </div>
          <div class="kpi-sub dim ellipsis" :title="k.sub">{{ k.sub }}</div>
        </NCard>
      </NGi>
    </NGrid>

    <NCard size="small" style="margin-bottom: 14px" title="研究回环的阶段">
      <template #header-extra><NText depth="3" style="font-size: 12px">虚线框内为并行阶段；每个阶段有一项完成标准，审稿意见会路由回源头阶段</NText></template>
      <StageStepper :ledger="{}" :static="true" />
    </NCard>

    <NSpin :show="loading">
      <NGrid cols="1 s:2 m:3" responsive="screen" :x-gap="14" :y-gap="14">
        <NGi v-for="r in roles" :key="r.id">
          <NCard hoverable size="small" class="role-card" :style="{ '--accent': roleVisual(r.id).color }" @click="router.push(`/roles/${r.id}`)">
            <div class="role-hd">
              <RoleBadge :role="r.id" :size="40" />
              <div class="role-titles">
                <div class="role-name">{{ r.label }}</div>
                <div class="role-id mono">{{ r.id }}</div>
              </div>
            </div>
            <p class="brief">{{ r.brief }}</p>
            <div class="facts">
              <div><span class="dim">阶段</span>{{ stageName(r) }}</div>
              <div><span class="dim">完成标准</span>{{ gateNames(r) }}</div>
              <div><span class="dim">工具</span>{{ r.server ? `MCP ${r.server} · ` : '' }}{{ r.tools.length }} 个</div>
            </div>
            <div class="more">查看角色 →</div>
          </NCard>
        </NGi>
      </NGrid>
      <NEmpty v-if="!loading && !roles.length" description="没有读到 skills/ 目录" style="margin-top: 40px" />
    </NSpin>

    <NCard size="small" style="margin-top: 16px">
      <div class="cta-row">
        <NIcon :size="26" color="#8fb1ff"><GitNetworkOutline /></NIcon>
        <div style="flex: 1">
          <div style="font-weight: 600">准备好了就发起一个研究主题</div>
          <NText depth="3" style="font-size: 12.5px">一行主题即可，编排器会走完整个回环并把每一步落账；运行过程按角色实时可见，随时可终止；历史工作区可回放。</NText>
        </div>
        <NButton type="primary" @click="router.push('/history?new=1')">发起新研究</NButton>
        <NButton @click="router.push('/skills')">技能与 MCP</NButton>
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.kpi-row { display: flex; align-items: center; gap: 12px; }
.kpi-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(91,141,239,.14); color: #8fb1ff; display: inline-flex; align-items: center; justify-content: center; flex: none; }
.kpi-value { font-size: 22px; font-weight: 700; line-height: 1.1; } .kpi-label { font-size: 12px; color: #9aa3b5; } .kpi-sub { font-size: 11.5px; margin-top: 8px; }
.role-card { cursor: pointer; height: 100%; position: relative; overflow: hidden; }
.role-card::before { content: ''; position: absolute; left: 0; right: 0; top: 0; height: 3px; background: var(--accent); }
.role-hd { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.role-name { font-weight: 600; font-size: 15px; } .role-id { font-size: 11.5px; color: #8a93a6; }
.brief { margin: 0 0 10px; line-height: 1.6; font-size: 13.5px; min-height: 3.2em; }
.facts { display: flex; flex-direction: column; gap: 4px; font-size: 12.5px; }
.facts .dim { display: inline-block; width: 64px; }
.more { margin-top: 10px; font-size: 12.5px; color: #8fb1ff; }
.cta-row { display: flex; align-items: center; gap: 14px; }
</style>
