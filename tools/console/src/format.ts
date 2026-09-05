export function dur(sec: number | null | undefined): string {
  if (sec == null) return '—'
  const s = Math.max(0, Math.floor(sec))
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60
  if (h) return `${h}h${String(m).padStart(2, '0')}m`
  if (m) return `${m}m${String(x).padStart(2, '0')}s`
  return `${x}s`
}

export function tok(n: number | null | undefined): string {
  if (!n) return '0'
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}k`
  return String(n)
}

export function hms(ts: number | null | undefined): string {
  if (!ts) return ''
  return new Date(ts * 1000).toLocaleTimeString('zh-CN', { hour12: false })
}

export function dateTime(ts: number | string | null | undefined): string {
  if (!ts) return '—'
  const d = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts)
  if (Number.isNaN(d.getTime())) return String(ts)
  return d.toLocaleString('zh-CN', { hour12: false, month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export function ago(ts: number | null | undefined, now: number): string {
  if (!ts) return '—'
  const s = Math.max(0, now - ts)
  if (s < 60) return `${Math.floor(s)} 秒前`
  if (s < 3600) return `${Math.floor(s / 60)} 分钟前`
  if (s < 86400) return `${Math.floor(s / 3600)} 小时前`
  return `${Math.floor(s / 86400)} 天前`
}

export function bytes(n: number): string {
  if (n >= 1 << 20) return `${(n / (1 << 20)).toFixed(1)} MB`
  if (n >= 1 << 10) return `${(n / (1 << 10)).toFixed(0)} KB`
  return `${n} B`
}

export function clip(s: string | null | undefined, n: number): string {
  if (!s) return ''
  return s.length > n ? s.slice(0, n - 1) + '…' : s
}

export function oneLine(s: string | null | undefined, n = 160): string {
  return clip((s || '').replace(/\s+/g, ' ').trim(), n)
}

/** 状态组 → Naive UI tag type */
export function statusType(group: string): 'success' | 'warning' | 'error' | 'info' | 'default' {
  switch (group) {
    case 'PASS': case 'DONE': case 'done': return 'success'
    case 'WARN': return 'warning'
    case 'FAIL': case 'failed': case 'BLOCKED': return 'error'
    case 'RUNNING': case 'running': return 'info'
    case 'ENDED': case 'ended': case 'stopped': return 'default'
    default: return 'default'
  }
}

export const WS_STATUS_LABEL: Record<string, string> = {
  running: '运行中', done: '已完成', failed: '失败', stopped: '已终止', ended: '已结束', empty: '空',
}
