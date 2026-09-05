<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NAlert, NButton, NCard, NDrawer, NDrawerContent, NEmpty, NGi, NGrid, NSpace, NSpin, NTag, NText, useMessage,
} from 'naive-ui'
import { marked } from 'marked'
import { api } from '../api'
import type { Role } from '../types'
import { roleVisual } from '../roles'
import PipelineStrip from '../components/PipelineStrip.vue'

const router = useRouter()
const message = useMessage()
const roles = ref<Role[]>([])
const loading = ref(true)
const drawer = ref(false)
const drawerRole = ref<Role | null>(null)
const skillHtml = ref('')

onMounted(async () => {
  try {
    roles.value = (await api.roles()).roles
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
      <h1>九个角色，一条账本驱动的回环</h1>
      <NText depth="3">每个角色 = 一份 <code>skills/&lt;role&gt;/SKILL.md</code> 提示词 + 它有权使用的 MCP 工具；编排器按账本阶段派活、按闸门验收、按 issue 路由返工。</NText>
    </div>

    <NCard size="small" style="margin-bottom: 14px" title="阶段状态机（点击角色卡查看完整 skill 规程）">
      <PipelineStrip :ledger="{}" :tasks="[]" :static="true" />
      <NText depth="3" style="font-size: 12px; display: block; margin-top: 8px">
        intake → scoping → [lit_search ∥ style_bank] → ref_gate → taxonomy → [figures ∥ writing ∥ ideas] → review →（全过）final；审稿 issue 按 target 路由回源头阶段。
        引用只允许来自过了 ref_gate 的 <code>references.bib</code>；PDF 只能由 TeX 从模板编译；每个 gate 都要账本落账，agent 自报完成不算数。
      </NText>
    </NCard>

    <NSpin :show="loading">
      <NGrid cols="1 s:2 m:3 xl:3" responsive="screen" :x-gap="14" :y-gap="14">
        <NGi v-for="r in roles" :key="r.id">
          <NCard hoverable size="small" class="role-card" :style="{ borderTop: `3px solid ${roleVisual(r.id).color}` }" @click="openSkill(r)">
            <template #header>
              <NSpace align="center" :size="8">
                <span style="font-size: 22px">{{ r.icon }}</span>
                <span style="font-weight: 600">{{ r.label }}</span>
                <NText depth="3" class="mono" style="font-size: 12px">{{ r.id }}</NText>
              </NSpace>
            </template>
            <template #header-extra>
              <NTag size="small" round :bordered="false">{{ r.skill_lines }} 行</NTag>
            </template>
            <p style="margin: 0 0 8px; line-height: 1.55">{{ r.brief }}</p>
            <NText depth="3" style="font-size: 12px; display: block; margin-bottom: 8px">{{ zhDescription(r.description) }}</NText>
            <NSpace :size="6" style="margin-bottom: 6px">
              <NTag size="small" type="info" :bordered="false">阶段 {{ r.stage }}</NTag>
              <NTag size="small" type="success" :bordered="false">闸门 {{ r.gate }}</NTag>
              <NTag v-if="r.server" size="small" type="warning" :bordered="false">MCP {{ r.server }}</NTag>
            </NSpace>
            <div class="dim" style="font-size: 12px; line-height: 1.7">
              <span v-for="t in r.tools" :key="t" class="mono tool-chip">{{ t }}</span>
            </div>
          </NCard>
        </NGi>
      </NGrid>
      <NEmpty v-if="!loading && !roles.length" description="没有读到 skills/ 目录" style="margin-top: 40px" />
    </NSpin>

    <NAlert type="info" :bordered="false" style="margin-top: 16px" title="准备好了就去发起一个研究主题">
      在「运行与历史」页点「发起新研究」：只需一行主题，编排器会走完整个状态机并把每一步落账；运行过程按角色实时可见，随时可终止。
      <NButton size="small" type="primary" style="margin-left: 12px" @click="router.push('/history')">去运行与历史</NButton>
    </NAlert>

    <NDrawer v-model:show="drawer" :width="820" placement="right">
      <NDrawerContent closable :native-scrollbar="false">
        <template #header>
          <NSpace align="center" v-if="drawerRole">
            <span style="font-size: 20px">{{ drawerRole.icon }}</span>
            <span>{{ drawerRole.label }} · {{ drawerRole.id }}</span>
            <NText depth="3" class="mono" style="font-size: 12px">{{ drawerRole.skill_path }}</NText>
          </NSpace>
        </template>
        <div class="markdown" v-html="skillHtml" />
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped>
.role-card { cursor: pointer; height: 100%; }
.tool-chip { display: inline-block; margin: 0 6px 4px 0; padding: 0 6px; border-radius: 4px; background: rgba(255,255,255,.07); font-size: 11.5px; }
</style>
