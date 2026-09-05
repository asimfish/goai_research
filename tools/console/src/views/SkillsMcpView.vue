<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NAlert, NCard, NGi, NGrid, NIcon, NSpin, NTag, NText, NTooltip, useMessage } from 'naive-ui'
import { ServerOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { McpServer, Role } from '../types'
import { roleVisual } from '../roles'

const router = useRouter()
const message = useMessage()
const roles = ref<Role[]>([])
const servers = ref<McpServer[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [r, m] = await Promise.all([api.roles(), api.mcp()])
    roles.value = r.roles
    servers.value = m.servers
  } catch (e) {
    message.error(`加载失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
})
function roleLabel(id: string) { return roleVisual(id).label }
function sig(t: { params: { name: string; default: string | null }[] }) {
  return t.params.map((p) => (p.default != null ? `${p.name}=${p.default}` : p.name)).join(', ')
}
</script>

<template>
  <div class="page">
    <div class="page-title">
      <div>
        <h1>技能与 MCP 服务</h1>
        <NText depth="3">九份技能规程告诉角色「怎么做」，四个 MCP 服务提供「能用什么」。规程是 <code>skills/&lt;role&gt;/SKILL.md</code>，服务是 <code>server/*.py</code>，两者都随仓库开源。</NText>
      </div>
    </div>

    <NSpin :show="loading">
      <div class="sec-title">技能 <NTag size="small" round :bordered="false">{{ roles.length }}</NTag> <span class="dim" style="font-size: 12px">skills/</span></div>
      <NGrid cols="1 s:2 m:3" responsive="screen" :x-gap="12" :y-gap="12" style="margin-bottom: 20px">
        <NGi v-for="r in roles" :key="r.id">
          <NCard size="small" hoverable class="skill" @click="router.push(`/roles/${r.id}`)">
            <div class="sk-hd">
              <span class="dot" :style="{ background: roleVisual(r.id).color }" />
              <span style="font-weight: 600">{{ r.label }}</span>
              <span class="mono dim" style="font-size: 11.5px">{{ r.id }}</span>
              <NTag size="tiny" round :bordered="false" style="margin-left: auto">{{ r.skill_lines }} 行</NTag>
            </div>
            <div class="mono dim" style="font-size: 11.5px; margin: 4px 0 6px">{{ r.skill_path }}</div>
            <div class="dim" style="font-size: 12px; line-height: 1.6">{{ r.skill_headings.slice(0, 5).join(' · ') }}</div>
            <div style="margin-top: 8px; font-size: 12.5px; color: #8fb1ff">查看规程 →</div>
          </NCard>
        </NGi>
      </NGrid>

      <div class="sec-title">MCP 服务 <NTag size="small" round :bordered="false">{{ servers.length }}</NTag> <span class="dim" style="font-size: 12px">server/</span></div>
      <NAlert type="info" :bordered="false" style="margin-bottom: 12px">
        Codex 延迟加载 MCP 工具：角色开场看不到这些工具，需要先 <code>tool_search</code> 再调用（每个子任务的提示词末尾已附说明）。
        所有调用由服务端写入工作区的 <code>state/tool_calls.jsonl</code>，并按 <code>run_id=批次/任务</code> 归因到角色。
      </NAlert>
      <NCard v-for="s in servers" :key="s.id" size="small" class="server" style="margin-bottom: 12px">
        <template #header>
          <div class="sv-hd">
            <span class="sv-icon"><NIcon :size="20"><ServerOutline /></NIcon></span>
            <div>
              <div><span style="font-weight: 600">{{ s.id }}</span> <span class="dim">· {{ s.tools.length }} 个工具</span></div>
              <div class="mono dim" style="font-size: 11.5px">python {{ s.file }}</div>
            </div>
            <div class="dim" style="font-size: 12.5px; margin-left: 14px; flex: 1">{{ s.summary.replace(/^[^—]*——\s*/, '') }}</div>
            <div class="users"><span class="dim" style="font-size: 12px">使用者</span>
              <NTag v-for="rid in s.used_by" :key="rid" size="small" :bordered="false" round style="cursor: pointer" @click="router.push(`/roles/${rid}`)">
                <span class="dot" :style="{ background: roleVisual(rid).color, marginRight: '6px' }" />{{ roleLabel(rid) }}
              </NTag>
            </div>
          </div>
        </template>
        <table class="tools">
          <thead><tr><th style="width: 200px">工具</th><th>参数</th><th style="width: 38%">说明</th><th style="width: 130px">使用角色</th></tr></thead>
          <tbody>
            <tr v-for="t in s.tools" :key="t.name">
              <td class="mono tn">{{ t.name }}</td>
              <td class="mono params">{{ sig(t) || '—' }}</td>
              <td>
                <NTooltip :disabled="t.doc.split('\n').length < 2"><template #trigger><span>{{ t.summary }}</span></template>
                  <pre style="max-width: 520px; white-space: pre-wrap; font-size: 12px; margin: 0">{{ t.doc }}</pre></NTooltip>
              </td>
              <td><span v-for="rid in t.used_by" :key="rid" class="user"><span class="dot" :style="{ background: roleVisual(rid).color }" />{{ roleLabel(rid) }}</span><span v-if="!t.used_by.length" class="dim">—</span></td>
            </tr>
          </tbody>
        </table>
      </NCard>
    </NSpin>
  </div>
</template>

<style scoped>
.sec-title { font-size: 15px; font-weight: 600; margin: 4px 0 10px; display: flex; align-items: center; gap: 8px; }
.skill { cursor: pointer; height: 100%; }
.sk-hd { display: flex; align-items: center; gap: 8px; }
.dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; flex: none; }
.sv-hd { display: flex; align-items: center; gap: 12px; }
.sv-icon { width: 36px; height: 36px; border-radius: 9px; background: rgba(167,139,250,.16); color: #c4b5fd; display: inline-flex; align-items: center; justify-content: center; flex: none; }
.users { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.tools { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.tools th { text-align: left; color: #8a93a6; font-weight: 500; font-size: 12px; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,.1); }
.tools td { padding: 7px 8px; border-bottom: 1px dashed rgba(255,255,255,.07); vertical-align: top; }
.tn { color: #c9d1d9; } .params { color: #9aa3b5; font-size: 11.5px; word-break: break-word; }
.user { display: inline-flex; align-items: center; gap: 5px; margin-right: 8px; font-size: 12px; }
</style>
