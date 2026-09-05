// 与 tools/console_server.py / tools/live_view.py 的 JSON 形状一一对应

export interface Role {
  id: string
  label: string
  icon: string
  name: string
  description: string
  brief: string
  stage: string
  gate: string
  server: string | null
  tools: string[]
  tools_detail: { name: string; desc: string }[]
  skill_path: string
  skill_lines: number
  exists: boolean
  skill_headings: string[]
}

export interface RolesStats { roles: number; mcp_servers: number; mcp_tools: number; gates: number; servers: string[]; stages: string[]; runs: number }

export interface Launcher {
  started: string | null
  pid: string | null
  exit: string | null
  finished: string | null
  status: string | null
  stopped: string | null
  alive: boolean
  meta: Record<string, unknown>
}

export type WsStatus = 'running' | 'done' | 'failed' | 'stopped' | 'ended' | 'empty'

export interface WorkspaceInfo {
  id: string
  path: string
  label: string
  parent: string
  topic: string
  created: string | null
  stage: string | null
  round: number | null
  max_rounds: number | null
  effort: string | null
  strictness: string | null
  gates: Record<string, string | null>
  gate_counts: Record<string, number>
  batches: number
  tasks: number
  tasks_running: number
  last_activity: number | null
  status: WsStatus
  launcher: Launcher
  final_pdf: boolean
  final_pdf_bytes: number
  receipt: { status?: string; verified_at_utc?: string; model?: string; reasoning_effort?: string } | null
  open_issues: number
  is_launchable_dir: boolean
}

export interface EventItem {
  kind: string
  item_id?: string
  status?: string | null
  ts?: number
  text?: string
  command?: string
  output?: string
  exit_code?: number | null
  changes?: { path: string; kind: string }[]
  server?: string
  tool?: string
  arguments?: string
  result?: string | null
  error?: string | null
  query?: string
  items?: { text: string; completed: boolean }[]
  usage?: Record<string, number>
}

export interface TaskSummary {
  key: string
  run_id: string
  name: string
  kind: 'parallel' | 'orchestrator'
  role: string
  status: string
  status_group: string
  exit: string | null
  process_exit: string | null
  started: number | null
  ended: number | null
  elapsed: number | null
  last_activity: number | null
  tokens_in: number | null
  tokens_cached: number | null
  tokens_out: number | null
  tokens_reasoning: number | null
  counts: Record<string, number>
  last_message: string
  current_command: string | null
  todo: { text: string; completed: boolean }[]
  thread_id: string
  expected: string[]
  dependencies: string[]
  validation: string
  final: string
  stderr: string
  prompt: string
  items_total: number
  audit_calls?: number
  recent: EventItem[]
}

export interface TaskDetail extends TaskSummary {
  items: EventItem[]
  prompt_full: string
}

export interface GateInfo { status: string | null; detail: string; round: number | null }

export interface LedgerSummary {
  topic?: string
  stage?: string
  stages?: string[]
  round?: number
  max_rounds?: number
  effort?: string
  strictness?: string
  created?: string
  gates?: Record<string, GateInfo>
  open_issues?: { id: string; severity: string; target: string; from: string; text: string }[]
  issue_counts?: Record<string, number>
  issues_total?: number
  log_tail?: string[]
  updated?: number
}

export interface AuditRow {
  ts: string
  tool: string
  duration_ms: number | null
  run_id: string | null
  ok: boolean | null
  request: string
}

export interface AuditSummary {
  total: number
  by_tool: Record<string, number>
  by_run: Record<string, number>
  recent: AuditRow[]
}

export interface RunInfo {
  run_id?: string
  backend?: string
  jobs?: number
  profile?: string
  model?: string
  sandbox?: string
  timeout?: number
  tasks_file?: string
  mcp_warning?: string
  started_at?: string
}

export interface StateResponse {
  workspace: string
  now: number
  seq: number
  runs: string[]
  run_info: Record<string, RunInfo>
  counts: Record<string, number>
  roles: string[]
  role_meta: Record<string, { icon: string; label: string }>
  tasks: TaskSummary[]
  ledger: LedgerSummary
  audit: AuditSummary
  all_runs: string[]
  workspace_info: WorkspaceInfo
}

export interface FeedEvent extends EventItem {
  seq: number
  task: string | null
  role: string | null
  name: string | null
  phase?: string
  duration_ms?: number | null
  ok?: boolean | null
  run_id?: string | null
  request?: string
}

export interface ConsoleConfig {
  repo: string
  runs_root: string
  codex_home: string
  codex_login: string | null
  codex_version: string | null
  model: string
  effort: string
  private_corpus_available: boolean
  private_corpus_roots: string | null
  public_corpus: string
  models: string[]
  efforts: string[]
}

export interface Artifacts {
  [k: string]: { path: string; bytes: number; mtime: number } | string[] | undefined
  figures_svg: string[]
  sections: string[]
  reviews: string[]
}
