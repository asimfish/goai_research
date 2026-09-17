import test from 'node:test'
import assert from 'node:assert/strict'
import { taskEnd, timelineRange } from '../src/taskTimeline.ts'

const start = 1_700_000_000
const task = (changes = {}) => ({ started: start, ended: start + 21_600, elapsed: 21_600, last_activity: start + 21_600, status_group: 'PASS', ...changes })

test('six-hour completed research stays six hours when viewed days later', () => {
  const tasks = [task(), task({ started: start + 3600, ended: start + 7200, elapsed: 3600 })]
  assert.deepEqual(timelineRange(tasks, start + 11 * 86400), { start, end: start + 21600, duration: 21600 })
  assert.deepEqual(timelineRange(tasks, start + 20 * 86400), timelineRange(tasks, start + 11 * 86400))
})
test('only a running task without an end extends to now', () => {
  const active = task({ ended: null, status_group: 'RUNNING' })
  assert.equal(timelineRange([active], start + 30000).duration, 30000)
  assert.equal(timelineRange([active], start + 30060).duration, 30060)
  assert.equal(taskEnd(task({ status_group: 'RUNNING' }), start + 11 * 86400), start + 21600)
})
test('historical tasks missing an end use recorded activity, elapsed or start', () => {
  const historical = task({ ended: null, status_group: 'ENDED' })
  assert.equal(taskEnd(historical, start + 11 * 86400), start + 21600)
  assert.equal(taskEnd({ ...historical, last_activity: null }, start + 11 * 86400), start + 21600)
  assert.equal(taskEnd({ ...historical, last_activity: null, elapsed: null }, start + 11 * 86400), start)
})
test('range follows selected tasks, including actual gaps and overnight execution', () => {
  const later = task({ started: start + 80000, ended: start + 90000, elapsed: 10000 })
  assert.equal(timelineRange([task(), later], start + 999999).duration, 90000)
  assert.equal(timelineRange([later], start + 999999).duration, 10000)
})
test('empty and invalid timestamps do not generate infinite chart bounds', () => {
  assert.deepEqual(timelineRange([], start), { start: 0, end: 0, duration: 1 })
  assert.deepEqual(timelineRange([task({ started: null }), task({ started: NaN })], start), { start: 0, end: 0, duration: 1 })
  assert.equal(taskEnd(task({ ended: start - 2, last_activity: null, elapsed: -2 }), start + 999999), start)
})
