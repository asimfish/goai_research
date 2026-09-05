// 角色的视觉元数据（与 tools/live_view.py 的 ROLE_META 对齐），后端返回的 role_meta 只有 icon/label。
export interface RoleVisual { icon: string; label: string; color: string; stage: string }

export const ROLE_VISUAL: Record<string, RoleVisual> = {
  'goai-orchestrator': { icon: '🧭', label: '编排', color: '#f0a020', stage: 'final' },
  'goai-lit-search': { icon: '🔎', label: '文献检索', color: '#5b8def', stage: 'lit_search' },
  'goai-style-bank': { icon: '🎨', label: '风格库', color: '#a78bfa', stage: 'style_bank' },
  'goai-ref-guard': { icon: '🛡', label: '引用核查', color: '#f2726f', stage: 'ref_gate' },
  'goai-survey-writer': { icon: '✍', label: '写作', color: '#63c26b', stage: 'writing' },
  'goai-figure-studio': { icon: '🖼', label: '图纸', color: '#e0b060', stage: 'figures' },
  'goai-figure-editable': { icon: '✎', label: '图纸可编辑化', color: '#e0b060', stage: 'figures' },
  'goai-idea-forge': { icon: '💡', label: '想法生成', color: '#f5d24a', stage: 'ideas' },
  'goai-reviewer': { icon: '⚖', label: '对抗审稿', color: '#e57fb0', stage: 'review' },
  unknown: { icon: '•', label: '未识别角色', color: '#8a93a6', stage: '?' },
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
