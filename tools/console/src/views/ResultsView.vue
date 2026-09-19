<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NEmpty, NIcon, NInput, NSpin, NTooltip, useMessage } from 'naive-ui'
import { CheckmarkCircleOutline, CloudDownloadOutline, DocumentTextOutline, ImagesOutline, OpenOutline, PeopleOutline, PlayCircleOutline, SearchOutline, TimeOutline } from '@vicons/ionicons5'
import { api } from '../api'
import type { Artifacts, WorkspaceInfo } from '../types'
import { bytes, dateTime, researchNumber } from '../format'
import { STAGE_LABEL } from '../roles'

/** 成果与历史回看（DESIGN.md 页面 06）：左侧历史时间线，右侧论文阅读器式预览 + 交付清单 + 可核验摘要。 */
const router = useRouter()
const route = useRoute()
const message = useMessage()
const rows = ref<WorkspaceInfo[]>([])
const tab = ref<'all' | 'done' | 'other'>('all')
const q = ref('')
const selectedId = ref<string>('')
const artifacts = ref<Artifacts | null>(null)
const loading = ref(true)
/** 预览区的两个视图：报告浏览（综述 PDF）/ 知识图谱浏览（public/knowledge/ 的逐层展开页，控制台主题）。 */
const previewMode = ref<'report' | 'graph'>((route.query.view as string) === 'graph' ? 'graph' : 'report')
const KG_URL = 'knowledge/knowledge_layers.html?theme=console&autoplay=1'

const filtered = computed(() => rows.value.filter((w) => {
  if (tab.value === 'done' && w.status !== 'done') return false
  if (tab.value === 'other' && w.status === 'done') return false
  return !q.value.trim() || (researchNumber(w.id) + w.topic + w.label).toLowerCase().includes(q.value.trim().toLowerCase())
}))
const selected = computed(() => rows.value.find((w) => w.id === selectedId.value) || null)

async function pick(id: string) {
  selectedId.value = id
  artifacts.value = await api.artifacts(id).catch(() => null)
}
onMounted(async () => {
  try {
    rows.value = (await api.workspaces()).workspaces.filter((w) => w.topic)
    const first = (route.query.id as string) || rows.value.find((w) => w.final_pdf)?.id || rows.value[0]?.id
    if (first) await pick(first)
  } catch (e) { message.error(`加载失败：${(e as Error).message}`) } finally { loading.value = false }
})
watch(() => route.query.id, (v) => { if (v) pick(String(v)) })
const summary = computed(() => artifacts.value?.summary)
function kind(w: WorkspaceInfo) { return w.status === 'done' ? 'ok' : w.status === 'running' ? 'run' : w.status === 'failed' ? 'bad' : 'wait' }
function statusText(w: WorkspaceInfo) { return w.status === 'done' ? '已交付' : w.status === 'running' ? '运行中' : w.status === 'stopped' ? '已终止' : w.status === 'failed' ? '失败' : '未完成' }
</script>

<template>
  <div class="page panel-page results-page">
    <Teleport to="#page-header-actions">
      <NButton size="small" @click="router.push('/experiments')">从研究进入材料实验 ↗</NButton>
      <NInput v-model:value="q" size="small" clearable placeholder="搜索研究主题或编号" style="width: 220px"><template #prefix><NIcon><SearchOutline /></NIcon></template></NInput>
    </Teleport>
    <NSpin :show="loading" class="panel-spin">
      <div class="layout">
        <aside class="sheet panel history">
          <div class="hd"><span class="card-h">历史研究</span>
            <div class="seg"><button :class="{ on: tab === 'all' }" @click="tab = 'all'">全部</button><button :class="{ on: tab === 'done' }" @click="tab = 'done'">已交付</button><button :class="{ on: tab === 'other' }" @click="tab = 'other'">未完成</button></div>
          </div>
          <div class="tl">
            <div v-for="w in filtered" :key="w.id" class="tl-item" :class="{ on: w.id === selectedId }" @click="pick(w.id)">
              <span class="tl-dot" :class="kind(w)"><NIcon v-if="w.status === 'done'" :size="12"><CheckmarkCircleOutline /></NIcon><NIcon v-else :size="12"><TimeOutline /></NIcon></span>
              <div class="tl-body">
                <div class="tl-title ellipsis" :title="w.topic">{{ w.topic }}</div>
                <div class="research-number">{{ researchNumber(w.id) }}</div><div class="small dim">{{ dateTime(w.created) }} · {{ statusText(w) }}<template v-if="w.stage && w.status !== 'done'"> · {{ STAGE_LABEL[w.stage] || w.stage }}</template></div>
              </div>
            </div>
            <NEmpty v-if="!filtered.length" description="没有匹配的研究" size="small" style="margin: 20px 0" />
          </div>
        </aside>

        <section class="detail" v-if="selected">
          <div class="d-hd">
            <div>
              <h2>{{ selected.topic }}</h2>
              <div class="small dim"><span class="research-number">{{ researchNumber(selected.id) }}</span> · <span class="st-dot" :class="kind(selected)" />{{ statusText(selected) }} · {{ dateTime(selected.created) }}<template v-if="selected.receipt"> · 复现回执 {{ selected.receipt.status }}</template></div>
            </div>
            <div class="d-actions">
              <NButton v-if="selected.final_pdf" type="primary" tag="a" :href="api.pdfUrl(selected.id)" target="_blank"><template #icon><NIcon><OpenOutline /></NIcon></template>打开 PDF</NButton>
              <NButton tag="a" :href="api.bundleUrl(selected.id)"><template #icon><NIcon><CloudDownloadOutline /></NIcon></template>下载全部成果</NButton>
              <NButton @click="router.push(`/run/${selected.id}`)"><template #icon><NIcon><PlayCircleOutline /></NIcon></template>回放研究过程</NButton>
            </div>
          </div>
          <div class="seg preview-switch">
            <button :class="{ on: previewMode === 'report' }" @click="previewMode = 'report'">报告浏览</button>
            <button :class="{ on: previewMode === 'graph' }" @click="previewMode = 'graph'">知识图谱浏览</button>
          </div>
          <div class="d-body">
            <div class="sheet panel preview">
              <template v-if="previewMode === 'graph'">
                <iframe class="kg-frame" :src="KG_URL" title="知识图谱 · 逐层展开" />
              </template>
              <iframe v-else-if="selected.final_pdf" :src="api.pdfUrl(selected.id) + '#toolbar=0&view=FitH'" title="综述 PDF 预览" />
              <div v-else class="no-pdf">
                <NIcon :size="40" color="#9AA6AE"><DocumentTextOutline /></NIcon>
                <div class="card-h" style="margin-top: 10px">尚未产出综述 PDF</div>
                <div class="dim small">{{ selected.status === 'running' ? '研究仍在进行，稿件完成阶段后会在这里出现。' : '这次运行没有走到稿件完成阶段；可以回放过程查看停在哪一步。' }}</div>
              </div>
            </div>
            <aside class="side">
              <div class="sheet panel">
                <div class="card-h" style="margin-bottom: 8px">交付清单</div>
                <div v-for="b in artifacts?.bundle_items || []" :key="b.path" class="dl small">
                  <span class="delivery-name"><strong>{{ b.label }}</strong><span class="dim mono ellipsis" :title="b.path">{{ b.path }}</span></span>
                  <span class="delivery-status" :class="b.exists ? 'ok' : 'dim'"><NIcon v-if="b.exists" :size="14"><CheckmarkCircleOutline /></NIcon>{{ b.exists ? '已生成' : '未生成' }}</span>
                </div>
              </div>
              <div class="sheet panel" v-if="summary">
                <div class="card-h" style="margin-bottom: 8px">可核验摘要</div>
                <div class="kv"><span class="k"><NIcon :size="16"><CheckmarkCircleOutline /></NIcon></span><span class="v">{{ summary.checks_passed }} / {{ summary.checks_total }}</span><span class="dim">结果质量检查通过</span></div>
                <div class="kv"><span class="k">“</span><span class="v">{{ summary.citations }}</span><span class="dim">条参考文献<template v-if="summary.papers">（库内 {{ summary.papers }} 篇）</template></span></div>
                <div class="kv"><span class="k"><NIcon :size="16"><ImagesOutline /></NIcon></span><span class="v">{{ summary.figures }}</span><span class="dim">张图纸</span></div>
                <div class="kv"><span class="k"><NIcon :size="16"><PeopleOutline /></NIcon></span><span class="v">{{ summary.review_rounds }}</span><span class="dim">轮审稿</span></div>
                <div class="kv" v-if="summary.pdf_pages"><span class="k"><NIcon :size="16"><DocumentTextOutline /></NIcon></span><span class="v">{{ summary.pdf_pages }}</span><span class="dim">页 · {{ summary.sections }} 个章节 · {{ bytes(selected.final_pdf_bytes) }}</span></div>
                <NTooltip><template #trigger><div class="dim small" style="margin-top: 8px">所有成果均保留版本与过程记录</div></template>账本、事件流与工具调用审计都在该工作区的 state/ 下</NTooltip>
              </div>
            </aside>
          </div>
        </section>
        <NEmpty v-else description="左侧选择一项研究" style="margin-top: 80px" />
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 16px; height: 100%; min-height: 0; }
.history { padding: 14px 12px; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 8px; flex-wrap: wrap; flex: none; }
.seg { display: inline-flex; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.seg button { border: 0; background: transparent; padding: 3px 9px; font: inherit; font-size: 12px; color: var(--slate); cursor: pointer; }
.seg button.on { background: var(--verdigris-soft); color: var(--ink); font-weight: 600; }
.tl { display: flex; flex-direction: column; flex: 1; min-height: 0; overflow: auto; overscroll-behavior: contain; }
.tl-item { display: flex; gap: 10px; padding: 10px 8px; border-radius: 10px; cursor: pointer; border: 1px solid transparent; }
.tl-item:hover { background: #F3F1EA; } .tl-item.on { border-color: var(--verdigris); background: #FBFAF7; }
.tl-dot { width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; flex: none; border: 1.5px solid #9AA6AE; color: var(--slate); background: #FBFAF7; }
.tl-dot.ok { border-color: var(--verdigris); color: var(--verdigris); } .tl-dot.run { border-color: var(--verdigris); color: var(--verdigris); } .tl-dot.warn { border-color: var(--amber); color: var(--amber); } .tl-dot.bad { border-color: var(--cinnabar); color: var(--cinnabar); }
.tl-body { min-width: 0; } .tl-title { font-weight: 600; font-size: 14px; }
.detail { min-width: 0; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.d-hd { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 14px; flex-wrap: wrap; flex: none; }
.d-hd > div:first-child { min-width: 0; flex: 1 1 320px; }
.d-hd h2 { margin: 0 0 4px; font-size: 24px; line-height: 32px; }
.d-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.d-body { display: grid; grid-template-columns: minmax(0, 1fr) 260px; gap: 16px; flex: 1; min-height: 0; }
.preview { min-height: 0; min-width: 0; overflow: auto; background: #E9E7DF; }
.preview iframe { display: block; width: 100%; height: 100%; border: 0; }
.preview .kg-frame { background: #F5F3ED; }
.preview-switch { margin: 0 0 10px; flex: none; }
.preview-switch button { padding: 4px 12px; font-size: 13px; }
.no-pdf { height: 100%; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 24px; }
.side { display: flex; flex-direction: column; gap: 12px; min-height: 0; overflow: auto; overscroll-behavior: contain; padding-right: 3px; }
.side > .panel { flex: none; }
.side .panel { padding: 14px 16px; }
.dl { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--line-soft); }
.delivery-name { display: flex; flex-direction: column; gap: 3px; min-width: 0; }.delivery-name strong { font-weight: 500; }.delivery-name .mono { font-size: 11px; }.delivery-status { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; font-size: 11px; padding: 3px 7px; border-radius: 6px; background: var(--mist); }.delivery-status.ok { background: var(--verdigris-soft); }
.ok { color: var(--verdigris); }
.kv { display: grid; grid-template-columns: 22px auto 1fr; gap: 10px; align-items: baseline; padding: 6px 0; border-bottom: 1px dashed var(--line-soft); }
.kv .k { color: var(--verdigris); display: inline-flex; align-items: center; font-size: 18px; }
.kv .v { font-size: 22px; font-weight: 600; line-height: 28px; }
@media (max-width: 1200px) { .layout { grid-template-columns: 220px minmax(0, 1fr); gap: 12px; }.d-body { grid-template-columns: minmax(0, 1fr) 220px; gap: 12px; }.d-hd h2 { font-size: 20px; line-height: 28px; }.side .panel { padding: 12px; }.seg button { padding-inline: 6px; } }
</style>
