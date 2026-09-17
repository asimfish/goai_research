export type Bucket = 'input' | 'output' | 'cache_read' | 'cache_write'
export interface CostTotal {
  tokens: Record<Bucket, number>
  currencies: Record<string, { total: string; model: string; tools: string; token_costs: Record<Bucket, string> }>
  records: number; usage_records: number; mcp_calls: number; missing_usage: number
  unpriced_records: number; mcp_duration_ms: number; warnings: Record<string, number>
  status: 'partial' | 'estimated' | 'complete'
  conversation_count?: number | null; reply_count?: number | null; turn_count?: number | null
}
export interface CostReport {
  summary: CostTotal; generated_at: string; price_config: string
  duplicates_ignored: number
  researches: (CostTotal & { id: string })[]; sessions: (CostTotal & { id: string })[]
  tasks: (CostTotal & { id: string })[]; models: (CostTotal & { id: string })[]
}
export interface PricingConfig {
  schema: string; version: string; currency: string; unit_tokens: number; note?: string
  models: Record<string, { aliases?: string[]; rates: Record<Bucket, string>; [key: string]: unknown }>
  [key: string]: unknown
}
export const buckets: Bucket[] = ['input', 'output', 'cache_read', 'cache_write']
export const bucketLabel = { input: 'Input · 普通输入', output: 'Output · 输出', cache_read: 'Cache read · 缓存读取', cache_write: 'Cache write · 缓存写入' }
export const warningLabel: Record<string, string> = {
  usage_not_reported: '会话没有返回完整用量，未按零计价',
  model_price_missing: '模型没有配置价格', tool_price_missing: '工具服务费尚未配置',
  tool_duration_missing: '按时间计费的工具缺少时长',
  current_tariff_for_historical_usage: '历史记录按当前价格表折算',
  service_tier_assumed_standard: '原日志未记录服务档位，按 Standard 折算',
  aggregate_context_unknown_standard_context_rates: '只有会话累计量，无法判断逐请求长上下文加价',
  cache_read_not_reported: '原始用量没有单列缓存读取', cache_write_not_reported: '原始用量没有单列缓存写入',
  service_tier_price_missing: '服务档位没有配置价格', peak_time_unknown: '缺少时间，无法选择峰谷价格',
  aggregate_peak_time_assumed: '累计用量按记录时间的峰谷档位折算',
  mcp_attribution_missing: '历史 MCP 审计缺少会话归属', invalid_trace_line: '用量日志有无法解析的记录',
  tool_usage_recording_failed: '工具内部模型的用量保存失败', invalid_usage_receipt: '用量收据格式不完整',
  duplicate_event_conflict: '副本对同一调用记录了不同计价信息，金额待核对',
}
export function costText(value?: CostTotal) {
  if (!value || !Object.keys(value.currencies).length) return '—'
  return Object.entries(value.currencies).map(([currency, v]) => `${currency} ${Number(v.total).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 8 })}`).join(' + ')
}
