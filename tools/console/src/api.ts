import type {
  Artifacts, ConsoleConfig, FeedEvent, Role, StateResponse, TaskDetail, WorkspaceInfo,
} from './types'

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url, { cache: 'no-store' })
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`
    try { const j = await r.json(); if (j?.error) msg = j.error } catch { /* ignore */ }
    throw new Error(msg)
  }
  return r.json() as Promise<T>
}

async function post<T>(url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  })
  const j = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error((j as { error?: string }).error || `${r.status} ${r.statusText}`)
  return j as T
}

export const api = {
  config: () => get<ConsoleConfig>('/api/config'),
  roles: () => get<{ roles: Role[] }>('/api/roles'),
  skill: (id: string) => get<{ id: string; markdown: string }>(`/api/roles/${encodeURIComponent(id)}/skill`),
  workspaces: () => get<{ workspaces: WorkspaceInfo[]; now: number }>('/api/workspaces'),
  info: (id: string) => get<WorkspaceInfo>(`/api/workspaces/${id}`),
  state: (id: string, recent = 30) => get<StateResponse>(`/api/workspaces/${id}/state?recent=${recent}`),
  feed: (id: string, after: number) => get<{ seq: number; events: FeedEvent[] }>(`/api/workspaces/${id}/feed?after=${after}`),
  task: (id: string, key: string) => get<TaskDetail>(`/api/workspaces/${id}/task?key=${encodeURIComponent(key)}`),
  launcherLog: (id: string) => get<{ stdout: string; stderr: string; orchestrator_final: string }>(`/api/workspaces/${id}/launcher-log`),
  artifacts: (id: string) => get<Artifacts>(`/api/workspaces/${id}/artifacts`),
  file: (id: string, path: string) => get<{ path: string; text: string }>(`/api/workspaces/${id}/file?path=${encodeURIComponent(path)}`),
  pdfUrl: (id: string) => `/api/workspaces/${id}/pdf`,
  launch: (body: { topic: string; corpus: 'public' | 'private'; model?: string; effort?: string; slug?: string }) =>
    post<{ ok: boolean; id: string; path: string; pid: number }>('/api/runs', body),
  stop: (id: string) => post<{ ok: boolean; message: string; pid?: number }>(`/api/workspaces/${id}/stop`),
}
