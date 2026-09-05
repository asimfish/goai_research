<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import {
  NConfigProvider, NDialogProvider, NGlobalStyle, NLayout, NLayoutContent, NLayoutHeader, NMenu,
  NMessageProvider, NNotificationProvider, NSpace, NTag, NTooltip, darkTheme, zhCN, dateZhCN,
} from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import { api } from './api'
import type { ConsoleConfig } from './types'

const route = useRoute()
const config = ref<ConsoleConfig | null>(null)
const running = ref(0)

const menu: MenuOption[] = [
  { label: () => h(RouterLink, { to: '/roles' }, { default: () => '角色说明' }), key: 'roles' },
  { label: () => h(RouterLink, { to: '/history' }, { default: () => '运行与历史' }), key: 'history' },
]
const activeKey = computed(() => (route.name === 'run' ? 'history' : String(route.name || 'roles')))

async function refresh() {
  try {
    const [c, w] = await Promise.all([api.config(), api.workspaces()])
    config.value = c
    running.value = w.workspaces.filter((x) => x.status === 'running').length
  } catch { /* 头部信息只是提示，失败不打断页面 */ }
}
onMounted(() => { refresh(); setInterval(refresh, 10000) })

const themeOverrides = {
  common: { primaryColor: '#5b8def', primaryColorHover: '#7aa2f7', primaryColorPressed: '#4a7ad8', borderRadius: '8px', fontSize: '13px' },
}
</script>

<template>
  <NConfigProvider :theme="darkTheme" :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <NGlobalStyle />
    <NMessageProvider><NDialogProvider><NNotificationProvider>
      <NLayout style="height: 100vh">
        <NLayoutHeader bordered style="height: 54px; display: flex; align-items: center; padding: 0 20px; gap: 22px">
          <RouterLink to="/roles" style="text-decoration: none; color: inherit; display: flex; align-items: baseline; gap: 8px">
            <span style="font-size: 17px; font-weight: 700; letter-spacing: .02em">goai research</span>
            <span class="dim" style="font-size: 12px">SAGE-Mat 多智能体综述控制台</span>
          </RouterLink>
          <NMenu mode="horizontal" :options="menu" :value="activeKey" style="flex: 1" />
          <NSpace align="center" :size="8" v-if="config">
            <NTooltip><template #trigger>
              <NTag size="small" :type="running ? 'info' : 'default'" round>{{ running ? `${running} 个运行中` : '无运行' }}</NTag>
            </template>由控制台或脚本启动、进程仍存活的工作区数</NTooltip>
            <NTooltip><template #trigger>
              <NTag size="small" :type="(config.codex_login || '').includes('Logged in') ? 'success' : 'warning'" round>
                codex {{ config.codex_version?.replace('codex-cli ', '') || '?' }}
              </NTag>
            </template>CODEX_HOME={{ config.codex_home }} · {{ config.codex_login || '未探测' }} · 模型 {{ config.model }} / {{ config.effort }}</NTooltip>
            <NTooltip><template #trigger>
              <NTag size="small" :type="config.private_corpus_available ? 'success' : 'default'" round>
                {{ config.private_corpus_available ? '私有全库可用' : '仅公开精简语料' }}
              </NTag>
            </template>{{ config.private_corpus_roots || config.public_corpus }}</NTooltip>
          </NSpace>
        </NLayoutHeader>
        <NLayoutContent content-style="height: calc(100vh - 54px); overflow: auto">
          <RouterView />
        </NLayoutContent>
      </NLayout>
    </NNotificationProvider></NDialogProvider></NMessageProvider>
  </NConfigProvider>
</template>
