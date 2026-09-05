<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NAlert, NCard, NDescriptions, NDescriptionsItem, NSpin, NTag, NText } from 'naive-ui'
import { api } from '../api'
import type { ConsoleConfig } from '../types'

const config = ref<ConsoleConfig | null>(null)
const error = ref('')
onMounted(async () => {
  try { config.value = await api.config() } catch (e) { error.value = (e as Error).message }
})
</script>

<template>
  <div class="page">
    <div class="page-title">
      <h1>设置</h1>
      <NText depth="3">控制台是只读观察 + 启停的薄层；模型、语料、账本规则都由仓库脚本与 <code>skills/</code> 决定，这里只显示服务端当前生效的配置。</NText>
    </div>
    <NAlert v-if="error" type="error" :bordered="false">{{ error }}</NAlert>
    <NSpin :show="!config && !error">
      <NCard v-if="config" size="small" title="服务端配置（tools/console_server.py 启动参数）">
        <NDescriptions label-placement="left" :column="1" size="small" bordered>
          <NDescriptionsItem label="仓库"><span class="mono">{{ config.repo }}</span></NDescriptionsItem>
          <NDescriptionsItem label="新运行目录"><span class="mono">{{ config.runs_root }}</span><NText depth="3">（--runs-root；每次发起新建 &lt;时间戳&gt;_&lt;后缀&gt;）</NText></NDescriptionsItem>
          <NDescriptionsItem label="CODEX_HOME"><span class="mono">{{ config.codex_home }}</span> <NTag size="small" :type="(config.codex_login || '').includes('Logged in') ? 'success' : 'warning'" :bordered="false">{{ config.codex_login || '未探测' }}</NTag> <NTag size="small" :bordered="false">{{ config.codex_version || '?' }}</NTag></NDescriptionsItem>
          <NDescriptionsItem label="默认模型 / 推理强度"><span class="mono">{{ config.model }} / {{ config.effort }}</span><NText depth="3">（--model / --effort，发起时可改）</NText></NDescriptionsItem>
          <NDescriptionsItem label="公开精简语料"><span class="mono">{{ config.public_corpus }}</span></NDescriptionsItem>
          <NDescriptionsItem label="私有全库语料">
            <template v-if="config.private_corpus_available"><span class="mono">{{ config.private_corpus_roots }}</span> <NTag size="small" type="success" :bordered="false">可用</NTag></template>
            <template v-else><NText depth="3">未配置：启动服务时加 <code>--private-corpus-env &lt;KEY=VALUE 文件&gt;</code>（模板 <code>configs/private_corpus.env.example</code>）</NText></template>
          </NDescriptionsItem>
          <NDescriptionsItem label="可选模型"><span class="mono">{{ config.models.join(' · ') }}</span></NDescriptionsItem>
        </NDescriptions>
      </NCard>
    </NSpin>
    <NCard size="small" title="怎么改" style="margin-top: 14px">
      <ul style="margin: 0; padding-left: 18px; line-height: 1.8; font-size: 13px">
        <li>换 Codex 账号 / 模型默认值：重启服务时改 <code>--codex-home</code> / <code>--model</code> / <code>--effort</code>（5090 上是 <code>~/goai_console.sh</code>）。</li>
        <li>挂入更多历史工作区：<code>--workspace-glob "&lt;含 state/ 的目录 glob&gt;"</code>，可重复。</li>
        <li>角色的提示词就是 <code>skills/&lt;role&gt;/SKILL.md</code>，改完刷新「角色说明」即可；运行规程见 <code>docs/LOOP_PROTOCOL.md</code>，操作手册见 <code>docs/RUNBOOK.md</code>。</li>
        <li>终端里看同样的数据：<code>python3 tools/live_view.py --follow</code>。</li>
      </ul>
    </NCard>
  </div>
</template>
