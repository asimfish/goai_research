<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NIcon, NSpin, useMessage } from 'naive-ui'
import { ChevronForwardOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { Role } from '../types'
import { STAGE_LABEL } from '../roles'
import { gateLabel } from '../labels'
import { renderSkill } from '../md'
import RoleBadge from '../components/RoleBadge.vue'

/** 角色技能索引与规程正文；MCP 服务及工具在独立工具页展示。 */
const router = useRouter()
const route = useRoute()
const message = useMessage()
const roles = ref<Role[]>([])
const selected = ref<string>('')
const html = ref('')
const headings = ref<string[]>([])
const loading = ref(true)

const role = computed(() => roles.value.find((r) => r.id === selected.value) || null)
async function select(id: string) {
  selected.value = id
  const r = await renderSkill((await api.skill(id)).markdown)
  if (selected.value !== id) return
  html.value = r.html
  headings.value = r.headings
}
onMounted(async () => {
  try {
    const r = await api.roles()
    roles.value = r.roles
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
  <div class="page panel-page skills-page">
    <NSpin :show="loading" class="panel-spin">
      <div class="layout">
        <aside class="sheet panel index">
          <div class="card-h" style="margin-bottom: 8px">九个角色技能</div>
          <div class="skill-list">
          <div v-for="r in roles" :key="r.id" class="idx" :class="{ on: r.id === selected }" @click="select(r.id)">
            <RoleBadge :role="r.id" :size="30" />
            <span class="nm">{{ r.label }}</span>
            <span class="dim small mono">{{ r.skill_lines }} 行</span>
          </div>
          </div>
          <div class="dim small" style="margin-top: 12px">选择角色查看技能规程。</div>
        </aside>

        <section class="sheet panel reader" v-if="role">
          <div class="r-hd">
            <RoleBadge :role="role.id" :size="44" />
            <div style="flex: 1">
              <h2>{{ role.label }} / 技能规程</h2>
              <div class="chips small">
                <span class="chip">适用阶段：{{ STAGE_LABEL[role.stage] || role.stage }}</span>
                <span class="chip">检查项目：{{ gateLabel(role.gate) }}</span>
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
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 16px; height: 100%; min-height: 0; }
.index { padding: 16px 12px 14px; display: flex; flex-direction: column; min-height: 0; overflow: hidden; box-sizing: border-box; }
.skill-list { flex: 1; min-height: 0; overflow: auto; }
.idx { display: flex; align-items: center; gap: 10px; padding: 8px 8px; border-radius: 10px; cursor: pointer; }
.idx:hover { background: #EFEDE6; } .idx.on { background: var(--verdigris-soft); }
.idx .nm { flex: 1; font-size: 14px; } .idx.on .nm { font-weight: 600; }
.reader { padding: 20px 24px; display: flex; flex-direction: column; min-height: 0; overflow: hidden; box-sizing: border-box; }
.r-hd { display: flex; align-items: flex-start; gap: 14px; border-bottom: 1px solid var(--line-soft); padding-bottom: 14px; margin-bottom: 10px; }
.r-hd h2 { margin: 0 0 6px; font-size: 22px; line-height: 30px; }
.chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { border: 1px solid var(--line); border-radius: 999px; padding: 1px 10px; color: var(--slate); }
.r-body { display: grid; grid-template-columns: minmax(0, 1fr) 180px; gap: 20px; flex: 1; min-height: 0; }
.body { min-height: 0; overflow: auto; padding-right: 14px; overscroll-behavior: contain; scrollbar-gutter: stable; }
.toc { min-height: 0; overflow: auto; border-left: 1px solid var(--line-soft); padding-left: 12px; }
.toc-item { font-size: 12.5px; padding: 3px 0; color: var(--slate); cursor: pointer; } .toc-item:hover { color: var(--ink); }
.layout > * { min-width: 0; }
@media (max-width: 1300px) { .r-body { grid-template-columns: minmax(0, 1fr); }.toc { display: none; } }
@media (max-width: 1000px) { .layout { grid-template-columns: 160px minmax(0, 1fr); }.idx .mono { display: none; }.idx { gap: 6px; padding-inline: 4px; }.reader { padding: 16px; }.r-hd { flex-wrap: wrap; }.r-hd h2 { font-size: 18px; } }
</style>
