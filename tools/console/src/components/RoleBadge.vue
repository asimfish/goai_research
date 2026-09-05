<script setup lang="ts">
import { computed } from 'vue'
import { NIcon } from 'naive-ui'
import { roleVisual } from '../roles'

/** 角色符号：统一的单线图标 + 墨蓝细圈，角色色只作右下角小圆点（DESIGN.md「不拟人化，角色色只作边标或小圆点」） */
const props = withDefaults(defineProps<{ role: string | null | undefined; size?: number; status?: 'run' | 'ok' | 'wait' | 'warn' | 'bad' | null }>(), { size: 40, status: null })
const vis = computed(() => roleVisual(props.role))
</script>

<template>
  <span class="glyph" :style="{ width: size + 'px', height: size + 'px' }">
    <NIcon :size="Math.round(size * 0.5)" color="#172B3A"><component :is="vis.icon" /></NIcon>
    <span class="rdot" :style="{ background: vis.color, width: Math.max(6, size * 0.16) + 'px', height: Math.max(6, size * 0.16) + 'px' }" />
    <span v-if="status" class="sdot" :class="status" />
  </span>
</template>

<style scoped>
.glyph { position: relative; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; border: 1.5px solid #172B3A; background: #FBFAF7; flex: none; }
.rdot { position: absolute; right: -1px; bottom: -1px; border-radius: 50%; border: 2px solid #FBFAF7; }
.sdot { position: absolute; left: -2px; top: -2px; width: 9px; height: 9px; border-radius: 50%; border: 2px solid #FBFAF7; }
.sdot.run { background: #2D7468; animation: breathe 1.8s ease-in-out infinite; } .sdot.ok { background: #2D7468; } .sdot.wait { background: #C9CCC6; } .sdot.warn { background: #B98032; } .sdot.bad { background: #A94D45; }
@keyframes breathe { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
</style>
