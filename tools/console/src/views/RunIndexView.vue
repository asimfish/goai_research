<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NEmpty, NSpin } from 'naive-ui'
import { api } from '../api'

/** 「运行」入口：有运行中的研究就直接进入它，否则进入最近一次；一个都没有就引导去发起。 */
const router = useRouter()
const empty = ref(false)
onMounted(async () => {
  try {
    const w = (await api.workspaces()).workspaces
    const target = w.find((x) => x.status === 'running') || w.find((x) => x.topic)
    if (target) router.replace(`/run/${target.id}`)
    else empty.value = true
  } catch { empty.value = true }
})
</script>

<template>
  <div class="page">
    <NSpin :show="!empty">
      <NEmpty v-if="empty" description="还没有任何研究运行" style="margin-top: 80px">
        <template #extra><NButton type="primary" @click="router.push('/history?new=1')">发起一项研究</NButton></template>
      </NEmpty>
      <div v-else style="height: 200px" />
    </NSpin>
  </div>
</template>
