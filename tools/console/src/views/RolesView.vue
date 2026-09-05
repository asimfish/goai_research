<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton, NCard, NDrawer, NDrawerContent, NEmpty, NGi, NGrid, NIcon, NSpace, NSpin, NTag, NText, useMessage,
} from 'naive-ui'
import { CheckmarkCircleOutline, GitNetworkOutline, HardwareChipOutline, LayersOutline, PeopleOutline } from '@vicons/ionicons5'
import { marked } from 'marked'
import { api } from '../api'
import type { Role, RolesStats } from '../types'
import { DEFAULT_STAGES, PARALLEL_GROUPS, STAGE_LABEL, roleVisual } from '../roles'
import PipelineStrip from '../components/PipelineStrip.vue'
import RoleBadge from '../components/RoleBadge.vue'

const router = useRouter()
const message = useMessage()
const roles = ref<Role[]>([])
const stats = ref<RolesStats | null>(null)
const loading = ref(true)
const drawer = ref(false)
const drawerRole = ref<Role | null>(null)
const skillHtml = ref('')

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

/** frontmatter 里的英文触发句去掉，只留中文说明 */
function zhDescription(d: string): string {
  const i = d.indexOf('— ')
  return i >= 0 ? d.slice(i + 2) : d
}

const kpis = computed(() => stats.value ? [
  { label: '角色', value: stats.value.roles, icon: PeopleOutline, sub: '每个 = 一份 SKILL.md' },
  { label: 'MCP 服务 · 工具', value: `${stats.value.mcp_servers} · ${stats.value.mcp_tools}`, icon: HardwareChipOutline, sub: stats.value.servers.join(' / ') },
  { label: '闸门', value: stats.value.gates, icon: CheckmarkCircleOutline, sub: 'check-done 机械放行' },
  { label: '工作区', value: stats.value.runs, icon: LayersOutline, sub: '含历史与正在运行' },
] : [])

/** 角色在状态机中的位置（抽屉里的迷你流程） */
function neighbourhood(role: Role) {
  const stage = roleVisual(role.id).stage
  const idx = DEFAULT_STAGES.indexOf(stage)
  if (idx < 0) return DEFAULT_STAGES.slice(1, 5)
  const group = PARALLEL_GROUPS.find((g) => g.includes(stage))
  const before = DEFAULT_STAGES.slice(Math.max(1, idx - 1), idx).filter((s) => !group?.includes(s))
  const after = DEFAULT_STAGES.slice(idx + 1).filter((s) => !group?.includes(s)).slice(0, 1)
  return [...before, ...(group || [stage]), ...after]
}

const flow = computed(() => (drawerRole.value ? neighbourhood(drawerRole.value) : []))
const myStage = computed(() => (drawerRole.value ? roleVisual(drawerRole.value.id).stage : ''))

async function openSkill(r: Role) {
  drawerRole.value = r
  drawer.value = true
  skillHtml.value = '<p class="dim">加载中…</p>'
  try {
    const md = (await api.skill(r.id)).markdown.replace(/^---\n[\s\S]*?\n---\n/, '')
    skillHtml.value = await marked.parse(md)
  } catch (e) {
    skillHtml.value = `<p>读取失败：${(e as Error).message}</p>`
  }
}
</script>

<template>
  <div class="page">
    <div class="page-title">
      <div>
        <h1>九个角色，一条账本驱动的回环</h1>
        <NText depth="3">SAGE-Mat 由九个专职角色组成：每个角色 = 一份 <code>skills/&lt;role&gt;/SKILL.md</code> 提示词 + 它有权使用的 MCP 工具。编排器按账本阶段派活、按闸门验收、按 issue 路由返工，直到 <code>check-done</code> 机械放行。</NText>
      </div>
    </div>

    <NGrid cols="2 m:4" responsive="screen" :x-gap="12" :y-gap="12" style="margin-bottom: 14px">
      <NGi v-for="k in kpis" :key="k.label">
        <NCard size="small" class="kpi">
          <div class="kpi-row">
            <span class="kpi-icon"><NIcon :size="22"><component :is="k.icon" /></NIcon></span>
            <div><div class="kpi-value">{{ k.value }}</div><div class="kpi-label">{{ k.label }}</div></div>
          </div>
          <div class="kpi-sub dim ellipsis" :title="k.sub">{{ k.sub }}</div>
        </NCard>
      </NGi>
    </NGrid>

    <NCard size="small" style="margin-bottom: 14px" title="阶段状态机">
      <template #header-extra><NText depth="3" style="font-size: 12px">∥ = 并行段 · 审稿 issue 按 target 路由回源头阶段 · 点角色卡看完整规程</NText></template>
      <PipelineStrip :ledger="{}" :tasks="[]" :static="true" />
    </NCard>

    <NSpin :show="loading">
      <NGrid cols="1 s:2 m:3" responsive="screen" :x-gap="14" :y-gap="14">
        <NGi v-for="r in roles" :key="r.id">
          <NCard hoverable size="small" class="role-card" :style="{ '--accent': roleVisual(r.id).color }" @click="openSkill(r)">
            <div class="role-hd">
              <RoleBadge :role="r.id" :size="40" />
              <div class="role-titles">
                <div class="role-name">{{ r.label }}</div>
                <div class="role-id mono">{{ r.id }}</div>
              </div>
              <NTag size="small" round :bordered="false" class="lines">{{ r.skill_lines }} 行</NTag>
            </div>
            <p class="brief">{{ r.brief }}</p>
            <NText depth="3" class="desc">{{ zhDescription(r.description) }}</NText>
            <NSpace :size="6" style="margin: 10px 0 8px">
              <NTag size="small" type="info" :bordered="false">阶段 {{ r.stage }}</NTag>
              <NTag size="small" type="success" :bordered="false">闸门 {{ r.gate }}</NTag>
              <NTag v-if="r.server" size="small" type="warning" :bordered="false">MCP {{ r.server }}</NTag>
            </NSpace>
            <div class="tools">
              <span v-for="t in r.tools" :key="t" class="mono tool-chip">{{ t }}</span>
            </div>
          </NCard>
        </NGi>
      </NGrid>
      <NEmpty v-if="!loading && !roles.length" description="没有读到 skills/ 目录" style="margin-top: 40px" />
    </NSpin>

    <NCard size="small" class="cta" style="margin-top: 16px">
      <div class="cta-row">
        <NIcon :size="26" color="#8fb1ff"><GitNetworkOutline /></NIcon>
        <div style="flex: 1">
          <div style="font-weight: 600">准备好了就发起一个研究主题</div>
          <NText depth="3" style="font-size: 12.5px">一行主题即可，编排器会走完整个状态机并把每一步落账；运行过程按角色实时可见，随时可终止；历史工作区可回放。</NText>
        </div>
        <NButton type="primary" @click="router.push('/history?new=1')">发起新研究</NButton>
        <NButton @click="router.push('/history')">运行与历史</NButton>
      </div>
    </NCard>

    <NDrawer v-model:show="drawer" :width="960" placement="right">
      <NDrawerContent closable :native-scrollbar="false" v-if="drawerRole">
        <template #header>
          <div class="dr-hd">
            <RoleBadge :role="drawerRole.id" :size="44" />
            <div>
              <div style="font-size: 17px; font-weight: 600">{{ drawerRole.label }} · <span class="mono" style="font-weight: 500">{{ drawerRole.id }}</span></div>
              <div class="dim mono" style="font-size: 12px">{{ drawerRole.skill_path }} · {{ drawerRole.skill_lines }} 行</div>
            </div>
          </div>
        </template>
        <div class="card-strip">
          <div class="cell"><div class="k">阶段</div><div class="v mono">{{ drawerRole.stage }}</div></div>
          <div class="cell"><div class="k">出口闸门</div><div class="v mono">{{ drawerRole.gate }}</div></div>
          <div class="cell"><div class="k">MCP server</div><div class="v mono">{{ drawerRole.server || '—（本地工具）' }}</div></div>
          <div class="cell"><div class="k">工具</div><div class="v">{{ drawerRole.tools.length }} 个</div></div>
        </div>
        <div class="mini-flow">
          <template v-for="(s, i) in flow" :key="s">
            <span class="mini-stage" :class="{ me: myStage === s, par: PARALLEL_GROUPS.some((g) => g.includes(s)) }">
              <span v-if="myStage === s" class="me-dot" />{{ STAGE_LABEL[s] || s }}
            </span>
            <span v-if="i < flow.length - 1" class="dim">{{ PARALLEL_GROUPS.some((g) => g.includes(s) && g.includes(flow[i + 1])) ? '∥' : '→' }}</span>
          </template>
        </div>
        <div class="dr-body">
          <div class="markdown" v-html="skillHtml" />
          <aside class="dr-side">
            <div class="side-title">工具面 <span class="dim">{{ drawerRole.tools_detail.length }} 项</span></div>
            <div v-for="t in drawerRole.tools_detail" :key="t.name" class="tool-row">
              <span class="mono tool-name">{{ t.name }}</span>
              <span class="dim tool-desc">{{ t.desc }}</span>
            </div>
            <div class="side-title" style="margin-top: 16px">章节</div>
            <div v-for="hd in drawerRole.skill_headings" :key="hd" class="dim" style="font-size: 12px; padding: 2px 0">· {{ hd }}</div>
          </aside>
        </div>
        <template #footer>
          <NSpace justify="end">
            <NButton @click="router.push('/history')">在运行中查看该角色</NButton>
            <NButton type="primary" @click="drawer = false">关闭</NButton>
          </NSpace>
        </template>
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped>
.kpi-row { display: flex; align-items: center; gap: 12px; }
.kpi-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(91,141,239,.14); color: #8fb1ff; display: inline-flex; align-items: center; justify-content: center; flex: none; }
.kpi-value { font-size: 22px; font-weight: 700; line-height: 1.1; }
.kpi-label { font-size: 12px; color: #9aa3b5; }
.kpi-sub { font-size: 11.5px; margin-top: 8px; }
.role-card { cursor: pointer; height: 100%; position: relative; overflow: hidden; }
.role-card::before { content: ''; position: absolute; left: 0; right: 0; top: 0; height: 3px; background: var(--accent); }
.role-hd { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.role-titles { flex: 1; min-width: 0; }
.role-name { font-weight: 600; font-size: 15px; }
.role-id { font-size: 11.5px; color: #8a93a6; }
.brief { margin: 0 0 6px; line-height: 1.55; font-size: 13px; }
.desc { font-size: 12px; display: block; line-height: 1.55; }
.tools { line-height: 1.8; }
.tool-chip { display: inline-block; margin: 0 6px 4px 0; padding: 0 6px; border-radius: 4px; background: rgba(255,255,255,.07); font-size: 11.5px; color: #c9d1d9; }
.cta-row { display: flex; align-items: center; gap: 14px; }
.dr-hd { display: flex; align-items: center; gap: 14px; }
.card-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px; }
.cell { background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08); border-radius: 8px; padding: 8px 12px; }
.cell .k { font-size: 11px; color: #8a93a6; } .cell .v { font-size: 13.5px; margin-top: 2px; }
.mini-flow { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 8px 12px; border: 1px solid rgba(255,255,255,.08); border-radius: 8px; margin-bottom: 14px; font-size: 12.5px; }
.mini-stage { padding: 2px 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,.12); }
.mini-stage.par { background: rgba(91,141,239,.08); }
.mini-stage.me { border-color: #5b8def; color: #8fb1ff; font-weight: 600; }
.me-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #5b8def; margin-right: 6px; }
.dr-body { display: grid; grid-template-columns: 1fr 300px; gap: 18px; align-items: start; }
.dr-side { position: sticky; top: 0; background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.08); border-radius: 8px; padding: 10px 12px; }
.side-title { font-size: 12px; font-weight: 600; margin-bottom: 6px; }
.tool-row { display: flex; flex-direction: column; padding: 4px 0; border-bottom: 1px dashed rgba(255,255,255,.08); }
.tool-name { font-size: 12px; color: #c9d1d9; } .tool-desc { font-size: 11.5px; }
</style>
