<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NBreadcrumb, NBreadcrumbItem, NButton, NCard, NEmpty, NSpin, NTabPane, NTabs, NTag, NText, useMessage,
} from 'naive-ui'
import { marked } from 'marked'
import { api } from '../api'
import type { Role, RoleTask } from '../types'
import { DEFAULT_STAGES, PARALLEL_GROUPS, STAGE_LABEL, roleVisual } from '../roles'
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
const tab = ref('skill')

const idx = computed(() => roles.value.findIndex((r) => r.id === props.id))
const prev = computed(() => (idx.value > 0 ? roles.value[idx.value - 1] : null))
const next = computed(() => (idx.value >= 0 && idx.value < roles.value.length - 1 ? roles.value[idx.value + 1] : null))

function zhDescription(d: string): string { const i = d.indexOf('— '); return i >= 0 ? d.slice(i + 2) : d }
const stage = computed(() => roleVisual(props.id).stage)
const flow = computed(() => {
  const i = DEFAULT_STAGES.indexOf(stage.value)
  if (i < 0) return DEFAULT_STAGES.slice(1)
  const group = PARALLEL_GROUPS.find((g) => g.includes(stage.value))
  const before = DEFAULT_STAGES.slice(Math.max(1, i - 2), i).filter((s) => !group?.includes(s))
  const after = DEFAULT_STAGES.slice(i + 1).filter((s) => !group?.includes(s)).slice(0, 2)
  return [...before, ...(group || [stage.value]), ...after]
})
const gateIds = computed(() => (role.value?.gate || '').split('·').map((g) => g.trim()).filter(Boolean))

async function load() {
  loading.value = true
  try {
    if (!roles.value.length) roles.value = (await api.roles()).roles
    const md = (await api.skill(props.id)).markdown.replace(/^---\n[\s\S]*?\n---\n/, '')
    html.value = await marked.parse(md)
    tasks.value = (await api.roleTasks(props.id, 30).catch(() => ({ tasks: [] }))).tasks
  } catch (e) {
    message.error(`加载角色失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => props.id, load)
</script>

<template>
  <div class="page" v-if="role">
    <NBreadcrumb style="margin-bottom: 10px">
      <NBreadcrumbItem @click="router.push('/roles')">角色</NBreadcrumbItem>
      <NBreadcrumbItem>{{ role.label }}</NBreadcrumbItem>
    </NBreadcrumb>
    <div class="hero">
      <RoleBadge :role="role.id" :size="64" />
      <div style="flex: 1; min-width: 0">
        <div class="title">{{ role.label }} <span class="mono id">{{ role.id }}</span></div>
        <div class="brief">{{ role.brief }}</div>
        <NText depth="3" style="font-size: 12.5px">{{ zhDescription(role.description) }}</NText>
      </div>
      <div class="nav">
        <NButton size="small" :disabled="!prev" @click="prev && router.push(`/roles/${prev.id}`)">‹ {{ prev ? prev.label : '上一个' }}</NButton>
        <NButton size="small" :disabled="!next" @click="next && router.push(`/roles/${next.id}`)">{{ next ? next.label : '下一个' }} ›</NButton>
      </div>
    </div>

    <div class="strip">
      <div class="cell"><div class="k">所处阶段</div><div class="v"><span class="dot" :style="{ background: roleVisual(role.id).color }" />{{ STAGE_LABEL[stage] || role.stage }} <span class="mono dim">{{ role.stage }}</span></div></div>
      <div class="cell"><div class="k">阶段完成标准</div><div class="v">{{ gateIds.map(gateLabel).join(' · ') || '—' }} <span class="mono dim">{{ role.gate }}</span></div></div>
      <div class="cell"><div class="k">MCP 服务</div><div class="v mono">{{ role.server || '—（本地脚本工具）' }}</div></div>
      <div class="cell"><div class="k">工具</div><div class="v">{{ role.tools.length }} 个</div></div>
    </div>

    <div class="flow">
      <template v-for="(s, i) in flow" :key="s">
        <span class="fs" :class="{ me: s === stage, par: PARALLEL_GROUPS.some((g) => g.includes(s)) }"><span v-if="s === stage" class="me-dot" />{{ STAGE_LABEL[s] || s }}</span>
        <span v-if="i < flow.length - 1" class="dim">{{ PARALLEL_GROUPS.some((g) => g.includes(s) && g.includes(flow[i + 1])) ? '∥' : '→' }}</span>
      </template>
      <span class="dim" style="margin-left: auto; font-size: 12px">在整条回环中的位置</span>
    </div>

    <NCard size="small" content-style="padding-top: 0">
      <NTabs v-model:value="tab" type="line" size="medium">
        <NTabPane name="skill" tab="工作规程">
          <NSpin :show="loading">
            <div class="body">
              <div class="markdown reading" v-html="html" />
              <aside class="outline">
                <div class="ot">本页目录</div>
                <div v-for="hd in role.skill_headings" :key="hd" class="oi">· {{ hd }}</div>
                <div class="ot" style="margin-top: 14px">文件</div>
                <div class="mono dim" style="font-size: 11.5px">{{ role.skill_path }} · {{ role.skill_lines }} 行</div>
              </aside>
            </div>
          </NSpin>
        </NTabPane>
        <NTabPane name="tools" :tab="`工具面（${role.tools.length}）`">
          <div class="tools">
            <div v-for="t in role.tools_detail" :key="t.name" class="tool">
              <span class="mono tn">{{ t.name }}</span>
              <span class="dim">{{ t.desc }}</span>
            </div>
          </div>
          <NText depth="3" style="font-size: 12px; display: block; margin-top: 10px">
            MCP 工具由 Codex 延迟加载：角色先用 tool_search 找到再调用；每次调用都写入工作区的 tool_calls.jsonl 并归因到任务。完整参数见「技能与 MCP」。
          </NText>
        </NTabPane>
        <NTabPane name="tasks" :tab="`近期任务（${tasks.length}）`">
          <div v-if="tasks.length" class="tasks">
            <div v-for="t in tasks" :key="t.workspace_id + t.key" class="task" @click="router.push(`/run/${t.workspace_id}`)">
              <NTag size="small" :type="statusType(t.status.split('_')[0])" :bordered="false" round>{{ taskStatus(t.status.split('_')[0], t.status) }}</NTag>
              <span class="mono tn">{{ t.name }}</span>
              <span class="dim ellipsis" style="flex: 1">{{ t.topic || t.workspace }}</span>
              <span class="dim">{{ dur(t.elapsed) }}</span>
              <span class="dim">{{ dateTime(t.started) }}</span>
            </div>
          </div>
          <NEmpty v-else description="还没有这个角色的任务记录" size="small" style="margin: 20px 0" />
        </NTabPane>
      </NTabs>
    </NCard>
  </div>
  <div class="page" v-else><NSpin :show="loading"><NEmpty v-if="!loading" description="没有这个角色" /></NSpin></div>
</template>

<style scoped>
.hero { display: flex; align-items: center; gap: 18px; margin-bottom: 14px; }
.title { font-size: 24px; font-weight: 700; }
.id { font-size: 13px; color: #8a93a6; font-weight: 500; margin-left: 8px; }
.brief { font-size: 14px; margin: 4px 0 2px; line-height: 1.55; }
.nav { display: flex; gap: 8px; flex: none; }
.strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 10px; }
.cell { background: #171a21; border: 1px solid rgba(255,255,255,.08); border-radius: 10px; padding: 10px 14px; }
.cell .k { font-size: 11.5px; color: #8a93a6; } .cell .v { font-size: 14px; margin-top: 3px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.flow { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 10px 14px; border: 1px solid rgba(255,255,255,.08); border-radius: 10px; margin-bottom: 14px; font-size: 13px; background: #171a21; }
.fs { padding: 3px 12px; border-radius: 14px; border: 1px solid rgba(255,255,255,.12); }
.fs.par { background: rgba(91,141,239,.08); } .fs.me { border-color: #5b8def; color: #8fb1ff; font-weight: 600; }
.me-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #5b8def; margin-right: 6px; }
.body { display: grid; grid-template-columns: minmax(0, 860px) 240px; gap: 24px; align-items: start; }
.reading { font-size: 14px; line-height: 1.7; }
.outline { position: sticky; top: 12px; border: 1px solid rgba(255,255,255,.08); border-radius: 10px; padding: 10px 12px; background: rgba(255,255,255,.03); }
.ot { font-size: 12px; font-weight: 600; margin-bottom: 4px; } .oi { font-size: 12px; color: #9aa3b5; padding: 2px 0; }
.tools { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 8px; }
.tool { display: flex; flex-direction: column; gap: 2px; padding: 8px 10px; border: 1px solid rgba(255,255,255,.08); border-radius: 8px; font-size: 12.5px; }
.tn { color: #c9d1d9; }
.tasks { display: flex; flex-direction: column; }
.task { display: flex; align-items: center; gap: 12px; padding: 8px 4px; border-bottom: 1px dashed rgba(255,255,255,.08); cursor: pointer; font-size: 12.5px; }
.task:hover { background: rgba(255,255,255,.03); }
@media (max-width: 1100px) { .body { grid-template-columns: 1fr; } .outline { position: static; } }
</style>
