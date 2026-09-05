// 角色的视觉元数据（与 tools/live_view.py 的 ROLE_META 对齐）。图标用 ionicons 线性图标，不依赖系统 emoji 字体。
import type { Component } from 'vue'
import {
  BrushOutline, BulbOutline, ColorPaletteOutline, CompassOutline, CreateOutline, EllipseOutline, ImageOutline,
  ScaleOutline, SearchOutline, ShieldCheckmarkOutline,
} from '@vicons/ionicons5'

export interface RoleVisual { icon: Component; glyph: string; label: string; color: string; stage: string }

export const ROLE_VISUAL: Record<string, RoleVisual> = {
  'goai-orchestrator': { icon: CompassOutline, glyph: '🧭', label: '编排', color: '#f0a020', stage: 'final' },
  'goai-lit-search': { icon: SearchOutline, glyph: '🔎', label: '文献检索', color: '#5b8def', stage: 'lit_search' },
  'goai-style-bank': { icon: ColorPaletteOutline, glyph: '🎨', label: '风格库', color: '#a78bfa', stage: 'style_bank' },
  'goai-ref-guard': { icon: ShieldCheckmarkOutline, glyph: '🛡', label: '引用核查', color: '#f2726f', stage: 'ref_gate' },
  'goai-survey-writer': { icon: CreateOutline, glyph: '✍', label: '写作', color: '#63c26b', stage: 'writing' },
  'goai-figure-studio': { icon: ImageOutline, glyph: '🖼', label: '图纸', color: '#e0b060', stage: 'figures' },
  'goai-figure-editable': { icon: BrushOutline, glyph: '✎', label: '图纸可编辑化', color: '#d9a441', stage: 'figures' },
  'goai-idea-forge': { icon: BulbOutline, glyph: '💡', label: '想法生成', color: '#f5d24a', stage: 'ideas' },
  'goai-reviewer': { icon: ScaleOutline, glyph: '⚖', label: '对抗审稿', color: '#e57fb0', stage: 'review' },
  unknown: { icon: EllipseOutline, glyph: '•', label: '未识别角色', color: '#8a93a6', stage: '?' },
}

export const ROLE_ORDER = Object.keys(ROLE_VISUAL).filter((k) => k !== 'unknown')

export function roleVisual(id: string | null | undefined): RoleVisual {
  return ROLE_VISUAL[id || ''] || ROLE_VISUAL.unknown
}

export const DEFAULT_STAGES = ['intake', 'scoping', 'lit_search', 'style_bank', 'ref_gate', 'taxonomy', 'figures', 'writing', 'ideas', 'review', 'final']

export const STAGE_GATE: Record<string, string> = {
  scoping: 'scope_confirmed', lit_search: 'lit_coverage', style_bank: 'style_bank_ready', ref_gate: 'ref_integrity',
  taxonomy: 'taxonomy_ready', figures: 'figures_ready', writing: 'draft_complete', ideas: 'ideas_reviewed', review: 'review_pass',
}

export const STAGE_LABEL: Record<string, string> = {
  intake: '接收', scoping: '定范围', lit_search: '文献检索', style_bank: '风格库', ref_gate: '引用核查', taxonomy: '分类法',
  figures: '图纸', writing: '写作', ideas: '想法', review: '审稿', final: '交付',
}

export const PARALLEL_GROUPS: string[][] = [['lit_search', 'style_bank'], ['figures', 'writing', 'ideas']]

/** 账本的 9 个必需闸门，按阶段顺序（历史表的分段进度条用） */
export const GATE_ORDER = ['scope_confirmed', 'lit_coverage', 'style_bank_ready', 'ref_integrity', 'taxonomy_ready', 'figures_ready', 'draft_complete', 'ideas_reviewed', 'review_pass']
