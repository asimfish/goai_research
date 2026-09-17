import type { TaskSummary } from './types'

type TimelineTask = Pick<TaskSummary, 'started' | 'ended' | 'elapsed' | 'last_activity' | 'status_group'>
const valid = (value: number | null): value is number => value !== null && Number.isFinite(value)

export function taskEnd(task: TimelineTask, now: number): number {
  const start = valid(task.started) ? task.started : 0
  if (valid(task.ended) && task.ended >= start) return task.ended
  if (task.status_group === 'RUNNING') return Math.max(start, now)
  // Incomplete historical records must not grow with the wall clock.
  if (valid(task.last_activity) && task.last_activity >= start) return task.last_activity
  if (valid(task.elapsed) && task.elapsed >= 0) return start + task.elapsed
  return start
}

export function timelineRange(tasks: TimelineTask[], now: number) {
  const timed = tasks.filter(t => valid(t.started))
  if (!timed.length) return { start: 0, end: 0, duration: 1 }
  const start = Math.min(...timed.map(t => t.started!))
  const end = Math.max(...timed.map(t => taskEnd(t, now)))
  return { start, end, duration: Math.max(1, end - start) }
}
