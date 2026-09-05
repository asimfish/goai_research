// 面向用户的文案：把账本 / 事件流里的工程词汇翻译成产品语言。规程与代码里的英文 id 保留，只是不再裸露给读者。
import type { EventItem } from './types'
import { oneLine } from './format'

/** 9 个必需质量检查项（账本里叫 gate）的中文名 */
export const GATE_LABEL: Record<string, string> = {
  scope_confirmed: '范围确认', lit_coverage: '文献覆盖', style_bank_ready: '风格库就绪', ref_integrity: '引用完整性',
  taxonomy_ready: '分类法就绪', figures_ready: '图纸就绪', draft_complete: '稿件完成', ideas_reviewed: '想法已审', review_pass: '审稿通过',
}
export function gateLabel(id: string): string { return GATE_LABEL[id] || id }

export const CHECK_STATUS_LABEL: Record<string, string> = { PASS: '通过', WARN: '警告', FAIL: '未通过', PENDING: '待完成' }
export function checkStatus(s: string | null | undefined): string { return CHECK_STATUS_LABEL[s || 'PENDING'] || s || '待完成' }

/** 子任务 / 工作区状态 */
export const TASK_STATUS_LABEL: Record<string, string> = {
  RUNNING: '运行中', PASS: '通过', WARN: '通过（有警告）', FAIL: '失败', BLOCKED: '被阻塞', DONE: '完成', ENDED: '已结束', STOPPED: '已终止', STALE: '无新输出', PENDING: '等待',
}
export function taskStatus(group: string, raw?: string): string {
  if (raw === 'FAIL_TIMEOUT') return '超时失败'
  if (raw === 'WARN_ARTIFACT_PASS_AFTER_TIMEOUT') return '超时但产物完整'
  if (raw === 'BLOCKED_DEPENDENCY') return '前序未通过，未启动'
  if (raw === 'STOPPED') return '已终止'
  return TASK_STATUS_LABEL[group] || raw || group
}

export const SEVERITY_LABEL: Record<string, string> = { blocker: '阻断', major: '重要', minor: '轻微' }

/** 命令行 → 短标签：取第一个有意义的可执行名，去掉 /bin/bash -lc 包装 */
export function commandLabel(cmd: string | undefined): string {
  if (!cmd) return '执行命令'
  let s = cmd.replace(/^\/bin\/bash\s+-lc\s+/, '').replace(/^["']|["']$/g, '').trim()
  s = s.replace(/^(cd\s+\S+\s*&&\s*)+/, '')
  const m = s.match(/(?:\.venv\/bin\/)?python3?\s+([^\s|;&]+)|^([\w./-]+)/)
  let head = ''
  if (m && m[1]) {
    head = m[1].startsWith('-') ? 'python' : m[1].split('/').pop() || 'python'
    const sub = s.match(new RegExp(`${m[1].replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s+([a-z][\\w-]*)`))
    if (sub && !sub[1].startsWith('-')) head += ` ${sub[1]}`
  } else if (m && m[2]) {
    head = m[2].split('/').pop() || m[2]
    const sub = s.match(new RegExp(`^${m[2].replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s+([a-z][\\w-]*)`))
    if (sub) head += ` ${sub[1]}`
  }
  if (!head) head = oneLine(s, 40)
  return head.length > 60 ? head.slice(0, 59) + '…' : head
}

export interface ActivityRow { kind: string; icon: string; label: string; detail: string; ts?: number; tone: 'msg' | 'cmd' | 'mcp' | 'file' | 'web' | 'todo' | 'err' | 'info' }

/** 事件 → 一行人话（卡片用；原始命令 / JSON 只在详情抽屉里看） */
export function toActivity(ev: EventItem): ActivityRow | null {
  switch (ev.kind) {
    case 'message': return ev.text ? { kind: ev.kind, icon: '💬', label: '', detail: oneLine(ev.text, 220), ts: ev.ts, tone: 'msg' } : null
    case 'command': {
      const rc = ev.exit_code
      const st = rc == null ? (ev.status === 'in_progress' ? '进行中' : '') : rc === 0 ? '完成' : `退出码 ${rc}`
      return { kind: ev.kind, icon: '⌘', label: '执行命令', detail: `${commandLabel(ev.command)}${st ? ' · ' + st : ''}`, ts: ev.ts, tone: 'cmd' }
    }
    case 'mcp': {
      const st = ev.error ? '失败' : ev.status === 'completed' ? '完成' : ev.status === 'in_progress' ? '进行中' : (ev.status || '')
      return { kind: ev.kind, icon: '⚙', label: '调用工具', detail: `${ev.server || ''} · ${ev.tool || ''}${st ? ' · ' + st : ''}`, ts: ev.ts, tone: 'mcp' }
    }
    case 'file_change': {
      const files = (ev.changes || []).map((c) => String(c.path).split('/').pop()).filter(Boolean)
      const kinds = new Set((ev.changes || []).map((c) => c.kind))
      const verb = kinds.size === 1 && kinds.has('add') ? '新建文件' : kinds.size === 1 && kinds.has('delete') ? '删除文件' : '写入文件'
      return { kind: ev.kind, icon: '✎', label: verb, detail: files.length > 3 ? `${files.slice(0, 3).join(', ')} 等 ${files.length} 个` : files.join(', '), ts: ev.ts, tone: 'file' }
    }
    case 'web_search': return ev.query ? { kind: ev.kind, icon: '⌕', label: '检索网页', detail: oneLine(ev.query, 120), ts: ev.ts, tone: 'web' } : null
    case 'todo': {
      const items = ev.items || []
      const done = items.filter((i) => i.completed).length
      const next = items.find((i) => !i.completed)?.text
      return { kind: ev.kind, icon: '☑', label: `计划 ${done}/${items.length}`, detail: next ? `下一步：${oneLine(next, 100)}` : '全部完成', ts: ev.ts, tone: 'todo' }
    }
    case 'error': return { kind: ev.kind, icon: '⚠', label: '出错', detail: oneLine(ev.text, 200), ts: ev.ts, tone: 'err' }
    case 'usage': return null
    case 'thread': return null
    case 'status': return ev.text && ev.text !== 'started' ? { kind: ev.kind, icon: '■', label: '状态', detail: taskStatus(ev.text, ev.text), ts: ev.ts, tone: 'info' } : null
    default: return null
  }
}

/** 卡片里的“最新一句话”：优先取最近的 agent 消息 */
export function latestMessage(items: EventItem[]): string {
  for (let i = items.length - 1; i >= 0; i--) {
    const it = items[i]
    if (it.kind === 'message' && it.text) return it.text
  }
  return ''
}
