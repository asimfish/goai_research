<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NEmpty, NSpin, NTag, useMessage } from 'naive-ui'
import { renderSkill } from '../md'
import { api } from '../api'
import type { Role, RoleTask } from '../types'
import { STAGE_LABEL, roleVisual } from '../roles'
import { gateLabel, taskStatus } from '../labels'
import { dateTime, dur, statusType } from '../format'
import RoleBadge from '../components/RoleBadge.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()
const message = useMessage()
const roles = ref<Role[]>([])
const role = computed(() => roles.value.find((r) => r.id === props.id) || null)
const html = ref('')
const tasks = ref<RoleTask[]>([])
const loading = ref(true)
const activeHeading = ref('')
const reader = ref<HTMLElement | null>(null)

function zhDescription(d: string): string { const i = d.indexOf('— '); return i >= 0 ? d.slice(i + 2) : d }
const stage = computed(() => roleVisual(props.id).stage)
const gateIds = computed(() => (role.value?.gate || '').split('·').map((g) => g.trim()).filter(Boolean))
const mdHeadings = ref<string[]>([])
const headings = computed(() => mdHeadings.value.length ? mdHeadings.value : (role.value?.skill_headings || []))

async function load() {
  loading.value = true
  try {
    if (!roles.value.length) roles.value = (await api.roles()).roles
    const r = await renderSkill((await api.skill(props.id)).markdown)
    html.value = r.html
    mdHeadings.value = r.headings
    tasks.value = (await api.roleTasks(props.id, 12).catch(() => ({ tasks: [] }))).tasks
  } catch (e) {
    message.error(`加载角色失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => props.id, load)
function jump(i: number) {
  const el = reader.value?.querySelector(`#h-${i}`) as HTMLElement | null
  el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  activeHeading.value = headings.value[i]
}
</script>

<template>
  <div class="page" v-if="role">
    <div class="crumbs small dim"><a @click="router.push('/roles')">角色总览</a> <span>/</span> <span class="ink">{{ role.label }}</span></div>
    <div class="layout">
      <aside class="identity">
        <div class="sheet id-card">
          <div class="dim small">角色 {{ String(role.index).padStart(2, '0') }}</div>
          <RoleBadge :role="role.id" :size="92" style="margin: 14px auto 12px" />
          <div class="name serif">{{ role.label }}</div>
          <div class="verb dim">{{ role.verb }}</div>
        </div>
        <div class="sheet bound"><div class="bt">输入</div><div class="dim small">{{ role.inputs.join('、') || '—' }}</div></div>
        <div class="sheet bound"><div class="bt">输出</div><div class="dim small">{{ role.outputs.join('、') || '—' }}</div></div>
        <div class="sheet bound wont"><div class="bt">不会做什么</div><div class="dim small">{{ role.wont.join('；') || '—' }}</div></div>
        <div class="sheet bound flow">
          <div v-if="role.upstream" class="nb" @click="router.push(`/roles/${role.upstream}`)"><span class="dim small">上游</span><RoleBadge :role="role.upstream" :size="24" /> {{ roleVisual(role.upstream).label }}</div>
          <div class="arrow dim">↓</div>
          <div class="nb me"><RoleBadge :role="role.id" :size="24" /> {{ role.label }} <span class="dim small">· {{ STAGE_LABEL[stage] || role.stage }}</span></div>
          <div class="arrow dim">↓</div>
          <div v-if="role.downstream" class="nb" @click="router.push(`/roles/${role.downstream}`)"><span class="dim small">下游</span><RoleBadge :role="role.downstream" :size="24" /> {{ roleVisual(role.downstream).label }}</div>
        </div>
      </aside>

      <section class="protocol">
        <div class="sheet panel reader-wrap">
          <div class="reader-hd">
            <div>
              <h2 class="serif">技能规程 <span class="mono dim">{{ role.skill_path }}</span></h2>
              <div class="dim small">{{ zhDescription(role.description) }}</div>
            </div>
            <div class="facts small">
              <span><span class="dim">阶段</span> {{ STAGE_LABEL[stage] || role.stage }}</span>
              <span><span class="dim">完成标准</span> {{ gateIds.map(gateLabel).join(' · ') || '—' }}</span>
              <span v-if="role.server"><span class="dim">MCP 服务</span> <span class="mono">{{ role.server }}</span></span>
              <span><span class="dim">工具</span> {{ role.tools.length }} 个</span>
            </div>
          </div>
          <NSpin :show="loading">
            <div class="reader">
              <div ref="reader" class="markdown body" v-html="html" />
              <nav class="toc">
                <div v-for="(h, i) in headings" :key="h" class="toc-item" :class="{ on: activeHeading === h }" @click="jump(i)">{{ h }}</div>
                <div class="toc-tools">
                  <div class="dim small" style="margin: 14px 0 6px">工具面</div>
                  <div v-for="t in role.tools_detail" :key="t.name" class="tool small"><span class="mono">{{ t.name }}</span><span class="dim">{{ t.desc }}</span></div>
                </div>
              </nav>
            </div>
          </NSpin>
        </div>

        <div class="sheet recent">
          <div class="card-h" style="margin-bottom: 8px">最近工作记录 <span class="dim small">跨所有工作区，最近 {{ tasks.length }} 次</span></div>
          <div v-if="tasks.length" class="rows">
            <div v-for="t in tasks" :key="t.workspace_id + t.key" class="row" @click="router.push(`/run/${t.workspace_id}`)">
              <span class="dim small mono" style="width: 120px">{{ dateTime(t.started) }}</span>
              <span class="ellipsis" style="flex: 1">{{ t.topic || t.workspace }} <span class="dim mono small">· {{ t.name }}</span></span>
              <span class="dim small">{{ dur(t.elapsed) }}</span>
              <NTag size="small" round :bordered="false" :type="statusType(t.status.split('_')[0])">{{ taskStatus(t.status.split('_')[0], t.status) }}</NTag>
              <NButton size="tiny" quaternary>查看证据 ›</NButton>
            </div>
          </div>
          <NEmpty v-else description="还没有这个角色的工作记录" size="small" style="margin: 14px 0" />
        </div>
      </section>
    </div>
  </div>
  <div class="page" v-else><NSpin :show="loading"><NEmpty v-if="!loading" description="没有这个角色" /></NSpin></div>
</template>

<style scoped>
.crumbs { margin-bottom: 14px; display: flex; gap: 8px; } .crumbs a { cursor: pointer; color: var(--slate); } .crumbs a:hover { color: var(--ink); } .ink { color: var(--ink); }
.layout { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 20px; align-items: start; }
.identity { display: flex; flex-direction: column; gap: 10px; position: sticky; top: 16px; }
.id-card { padding: 18px 20px 20px; text-align: center; }
.name { font-size: 26px; line-height: 34px; font-weight: 600; }
.verb { margin-top: 4px; font-size: 13.5px; line-height: 20px; }
.bound { padding: 12px 16px; } .bt { font-weight: 600; font-size: 13px; margin-bottom: 4px; }
.bound.wont .bt::before { content: '⊘ '; color: var(--cinnabar); }
.flow { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
.nb { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 4px 6px; border-radius: 8px; } .nb:hover { background: #EFEDE6; } .nb.me { cursor: default; font-weight: 600; }
.arrow { padding-left: 14px; line-height: 14px; }
.reader-wrap { padding: 22px 26px; }
.reader-hd { display: flex; justify-content: space-between; gap: 20px; align-items: flex-start; border-bottom: 1px solid var(--line-soft); padding-bottom: 14px; margin-bottom: 8px; }
.reader-hd h2 { margin: 0 0 4px; font-size: 22px; line-height: 30px; }
.reader-hd h2 .mono { font-size: 12px; margin-left: 8px; font-weight: 400; }
.facts { display: flex; flex-direction: column; gap: 4px; text-align: right; white-space: nowrap; }
.facts .dim { margin-right: 6px; }
.reader { display: grid; grid-template-columns: minmax(0, 1fr) 260px; gap: 26px; align-items: start; }
.body { max-height: calc(100vh - 300px); overflow: auto; padding-right: 8px; }
.toc { position: sticky; top: 0; border-left: 1px solid var(--line-soft); padding-left: 14px; }
.toc-item { font-size: 13px; padding: 4px 0; color: var(--slate); cursor: pointer; border-left: 2px solid transparent; margin-left: -15px; padding-left: 13px; }
.toc-item:hover, .toc-item.on { color: var(--ink); border-left-color: var(--verdigris); }
.tool { display: flex; flex-direction: column; padding: 4px 0; border-bottom: 1px dashed var(--line-soft); }
.recent { margin-top: 16px; padding: 14px 18px; }
.rows { display: flex; flex-direction: column; }
.row { display: flex; align-items: center; gap: 14px; padding: 9px 4px; border-bottom: 1px dashed var(--line-soft); cursor: pointer; font-size: 13.5px; }
.row:hover { background: #F3F1EA; }
@media (max-width: 1100px) { .layout { grid-template-columns: 1fr; } .identity { position: static; } .reader { grid-template-columns: 1fr; } .toc { display: none; } }
</style>
