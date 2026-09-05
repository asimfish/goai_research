<script setup lang="ts">
import { computed } from 'vue'
import { NIcon } from 'naive-ui'
import { roleVisual } from '../roles'

const props = withDefaults(defineProps<{ role: string | null | undefined; size?: number }>(), { size: 34 })
const vis = computed(() => roleVisual(props.role))
</script>

<template>
  <span class="badge" :style="{ width: size + 'px', height: size + 'px', background: vis.color + '22', borderColor: vis.color + '66', color: vis.color }">
    <NIcon :size="Math.round(size * 0.56)"><component :is="vis.icon" /></NIcon>
  </span>
</template>

<style scoped>
.badge { display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; border: 1px solid; flex: none; }
</style>
