<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NEmpty, NIcon, NInput, NSpin, NTooltip, useMessage } from 'naive-ui'
import { ChevronForwardOutline, SearchOutline, ServerOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { McpServer, Role } from '../types'
import { roleVisual } from '../roles'
import { renderSkill } from '../md'
import RoleBadge from '../components/RoleBadge.vue'

/** 技能与工具（DESIGN.md 页面 05）：左侧技能索引 / 中间规程正文 / 右侧 MCP 服务与工具清单。 */
const router = useRouter()
const route = useRoute()
const message = useMessage()
const roles = ref<Role[]>([])
const servers = ref<McpServer[]>([])
const selected = ref<string>('')
const html = ref('')
const headings = ref<string[]>([])
const loading = ref(true)
const toolQuery = ref('')
const expanded = ref<string | null>(null)

const role = computed(() => roles.value.find((r) => r.id === selected.value) || null)
const relatedServers = computed(() => servers.value.filter((s) => !role.value || s.used_by.includes(role.value.id) || !role.value.server))
const filteredServers = computed(() => {
  const q = toolQuery.value.trim().toLowerCase()
  if (!q) return servers.value
  return servers.value.map((s) => ({ ...s, tools: s.tools.filter((t) => (t.name + t.summary).toLowerCase().includes(q)) })).filter((s) => s.tools.length)
})
const SERVER_LABEL: Record<string, string> = { 'goai-litsearch': '文献检索服务', 'goai-refcheck': '引用核查服务', 'goai-figure': '图纸渲染服务', 'goai-retro': '逆合成与方案服务' }

async function select(id: string) {
  selected.value = id
  const r = await renderSkill((await api.skill(id)).markdown)
  html.value = r.html
  headings.value = r.headings
}
onMounted(async () => {
  try {
    const [r, m] = await Promise.all([api.roles(), api.mcp()])
    roles.value = r.roles
    servers.value = m.servers
    await select(String(route.query.role || r.roles[1]?.id || r.roles[0]?.id))
  } catch (e) {
    message.error(`加载失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
})
watch(() => route.query.role, (v) => { if (v && v !== selected.value) select(String(v)) })
function jump(i: number) { document.getElementById(`h-${i}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }
</script>

<template>
  <div class="page">
    <div class="page-title"><div><h1>技能与工具</h1><div class="lead">九份技能规程告诉角色「怎么做」，四个 MCP 服务提供「能用什么」。规程与服务都随仓库开源。</div></div></div>
    <NSpin :show="loading">
      <div class="layout">
        <aside class="sheet panel index">
          <div class="card-h" style="margin-bottom: 8px">九个角色技能</div>
          <div v-for="r in roles" :key="r.id" class="idx" :class="{ on: r.id === selected }" @click="select(r.id)">
            <RoleBadge :role="r.id" :size="30" />
            <span class="nm">{{ r.label }}</span>
            <span class="dim small mono">{{ r.skill_lines }} 行</span>
          </div>
          <div class="dim small" style="margin-top: 12px">规程随版本更新；点角色名进入角色页可看输入 / 输出与近期任务。</div>
        </aside>

        <section class="sheet panel reader" v-if="role">
          <div class="r-hd">
            <RoleBadge :role="role.id" :size="44" />
            <div style="flex: 1">
              <h2 class="serif">{{ role.label }} / 技能规程</h2>
              <div class="chips small">
                <span class="chip">适用阶段：{{ role.stage }}</span>
                <span class="chip">完成标准：{{ role.gate }}</span>
                <span v-if="role.server" class="chip mono">{{ role.server }}</span>
              </div>
            </div>
            <NButton size="small" quaternary @click="router.push(`/roles/${role.id}`)">角色页 <NIcon><ChevronForwardOutline /></NIcon></NButton>
          </div>
          <div class="r-body">
            <div class="markdown body" v-html="html" />
            <nav class="toc">
              <div v-for="(h, i) in headings" :key="h" class="toc-item" @click="jump(i)">{{ h }}</div>
            </nav>
          </div>
        </section>

        <aside class="sheet panel services">
          <div class="card-h" style="display: flex; justify-content: space-between; align-items: center">MCP 服务 <span class="dim small">{{ servers.filter((s) => s.exists).length }} / {{ servers.length }} 在线</span></div>
          <NInput v-model:value="toolQuery" size="small" clearable placeholder="搜索工具" style="margin: 10px 0 12px"><template #prefix><NIcon><SearchOutline /></NIcon></template></NInput>
          <div v-for="s in filteredServers" :key="s.id" class="svc" :class="{ dim: role && role.server && s.id !== role.server && !relatedServers.includes(s) }">
            <div class="svc-hd" @click="expanded = expanded === s.id ? null : s.id">
              <span class="svc-icon"><NIcon :size="22"><ServerOutline /></NIcon></span>
              <div style="flex: 1; min-width: 0">
                <div class="card-h" style="font-size: 14px">{{ SERVER_LABEL[s.id] || s.id }} <span class="dim small mono">{{ s.id }}</span></div>
                <div class="dim small ellipsis">{{ s.summary.replace(/^[^—]*——\s*/, '') }}</div>
              </div>
              <span class="small"><span class="st-dot" :class="s.exists ? 'ok' : 'bad'" />{{ s.exists ? '在线' : '缺失' }}</span>
            </div>
            <div class="tools small">
              <span class="dim">工具：</span>
              <template v-for="t in s.tools" :key="t.name">
                <NTooltip><template #trigger><span class="mono tool" @click="expanded = s.id">{{ t.name }}</span></template>
                  <div style="max-width: 420px; font-size: 12.5px"><b>{{ t.name }}</b>（{{ t.params.map((p) => p.name).join(', ') || '无参数' }}）<div>{{ t.summary }}</div><div class="dim" v-if="t.used_by.length">使用者：{{ t.used_by.map((u) => roleVisual(u).label).join('、') }}</div></div>
                </NTooltip>
              </template>
            </div>
            <div v-if="expanded === s.id" class="detail">
              <div v-for="t in s.tools" :key="t.name" class="trow small">
                <div class="mono">{{ t.name }}<span class="dim">({{ t.params.map((p) => (p.default != null ? `${p.name}=${p.default}` : p.name)).join(', ') }})</span></div>
                <div class="dim">{{ t.summary }}</div>
              </div>
            </div>
          </div>
          <NEmpty v-if="!filteredServers.length" description="没有匹配的工具" size="small" />
          <div class="dim small" style="margin-top: 10px">工具由 Codex 延迟加载，角色先 tool_search 再调用；每次调用记录在运行的工具调用审计里。</div>
        </aside>
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: 240px minmax(0, 1fr) 320px; gap: 16px; align-items: start; }
.index, .services { padding: 16px 16px 14px; position: sticky; top: 16px; }
.idx { display: flex; align-items: center; gap: 10px; padding: 8px 8px; border-radius: 10px; cursor: pointer; }
.idx:hover { background: #EFEDE6; } .idx.on { background: var(--verdigris-soft); }
.idx .nm { flex: 1; font-size: 14px; } .idx.on .nm { font-weight: 600; }
.reader { padding: 22px 26px; }
.r-hd { display: flex; align-items: flex-start; gap: 14px; border-bottom: 1px solid var(--line-soft); padding-bottom: 14px; margin-bottom: 10px; }
.r-hd h2 { margin: 0 0 6px; font-size: 22px; line-height: 30px; }
.chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { border: 1px solid var(--line); border-radius: 999px; padding: 1px 10px; color: var(--slate); }
.r-body { display: grid; grid-template-columns: minmax(0, 1fr) 180px; gap: 20px; align-items: start; }
.body { max-height: calc(100vh - 300px); overflow: auto; padding-right: 8px; }
.toc { position: sticky; top: 0; border-left: 1px solid var(--line-soft); padding-left: 12px; }
.toc-item { font-size: 12.5px; padding: 3px 0; color: var(--slate); cursor: pointer; } .toc-item:hover { color: var(--ink); }
.svc { border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; background: #FBFAF7; }
.svc.dim { opacity: .6; }
.svc-hd { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.svc-icon { width: 38px; height: 38px; border-radius: 10px; background: #EFEDE6; color: var(--ink); display: inline-flex; align-items: center; justify-content: center; flex: none; }
.tools { margin-top: 8px; line-height: 20px; }
.tool { cursor: pointer; margin-right: 8px; color: var(--ink); } .tool:hover { text-decoration: underline; }
.detail { margin-top: 8px; border-top: 1px dashed var(--line-soft); padding-top: 6px; }
.trow { padding: 5px 0; border-bottom: 1px dashed var(--line-soft); }
@media (max-width: 1200px) { .layout { grid-template-columns: 220px 1fr; } .services { grid-column: 1 / -1; position: static; } }
</style>
