import test from 'node:test'
import assert from 'node:assert/strict'
import { EventEmitter } from 'node:events'
import { createHarnessRefresh, installHarnessRefresh } from '../../workspace/harness_refresh.mjs'

test('background refresh uses fixed read-only command and returns its pending review result', async () => {
  let command
  const spawnProcess = (program, args, options) => {
    command = { program, args, options }
    const child = new EventEmitter()
    child.stdout = new EventEmitter()
    child.stderr = new EventEmitter()
    child.kill = () => {}
    queueMicrotask(() => {
      child.stdout.emit('data', Buffer.from('{"status":"UNREVIEWED","sources":[{"diff":"+change"}]}'))
      child.emit('close', 2)
    })
    return child
  }
  const refresh = createHarnessRefresh({ python: 'python', root: 'workspace', baseline: 'baseline', spawnProcess })
  assert.equal(refresh.status().status, 'NOT_CHECKED')
  const result = await refresh.check()
  assert.equal(result.status, 'UNREVIEWED')
  assert.equal(result.sources[0].diff, '+change')
  assert.deepEqual(command.args, ['-X', 'utf8', '-m', 'scripts.workspace.harness_library', 'check', '--root', 'workspace', '--baseline', 'baseline', '--online', '--format', 'json'])
  assert.equal(command.options.shell, false)
  refresh.stop()
})

test('a failed refresh is visible and never reports a successful review', async () => {
  const spawnProcess = () => {
    const child = new EventEmitter()
    child.stdout = new EventEmitter()
    child.stderr = new EventEmitter()
    child.kill = () => {}
    queueMicrotask(() => child.emit('error', new Error('unavailable')))
    return child
  }
  const refresh = createHarnessRefresh({ python: 'python', root: 'workspace', baseline: 'baseline', spawnProcess })
  assert.equal((await refresh.check()).status, 'ERROR')
  refresh.stop()
})

test('UTF-8 source diffs survive byte boundaries', async () => {
  const spawnProcess = () => {
    const child = new EventEmitter()
    child.stdout = new EventEmitter()
    child.stderr = new EventEmitter()
    child.kill = () => {}
    const data = Buffer.from('{"status":"CHANGED","diff":"变更"}')
    const split = data.indexOf(Buffer.from('变')) + 1
    queueMicrotask(() => {
      child.stdout.emit('data', data.subarray(0, split))
      child.stdout.emit('data', data.subarray(split))
      child.emit('close', 2)
    })
    return child
  }
  const refresh = createHarnessRefresh({ python: 'python', root: 'workspace', baseline: 'baseline', spawnProcess })
  assert.equal((await refresh.check()).diff, '变更')
  refresh.stop()
})

test('host integration starts once and exposes cached read-only status', async () => {
  let definition
  let calls = 0
  let unregistered = false
  const spawnProcess = () => {
    calls++
    const child = new EventEmitter()
    child.stdout = new EventEmitter()
    child.stderr = new EventEmitter()
    child.kill = () => {}
    queueMicrotask(() => {
      child.stdout.emit('data', Buffer.from('{"status":"UNREVIEWED","sources":[]}'))
      child.emit('close', 2)
    })
    return child
  }
  const dispose = installHarnessRefresh({ tools: { register(value) { definition = value; return () => { unregistered = true } } } },
    { python: 'python', root: 'workspace', baseline: 'baseline', spawnProcess })
  assert.equal(definition.name, 'workspace_harness_status')
  const result = JSON.parse(await definition.execute({ refresh: true }))
  assert.equal(result.status, 'UNREVIEWED')
  assert.equal(calls, 1)
  dispose()
  assert.equal(unregistered, true)
})

test('a later refresh recovers after a failed check', async () => {
  let calls = 0
  const spawnProcess = () => {
    const child = new EventEmitter()
    child.stdout = new EventEmitter()
    child.stderr = new EventEmitter()
    child.kill = () => {}
    const current = ++calls
    queueMicrotask(() => {
      if (current === 1) child.emit('error', new Error('offline'))
      else {
        child.stdout.emit('data', Buffer.from('{"status":"UNREVIEWED","sources":[]}'))
        child.emit('close', 2)
      }
    })
    return child
  }
  const refresh = createHarnessRefresh({ python: 'python', root: 'workspace', baseline: 'baseline', spawnProcess })
  assert.equal((await refresh.check()).status, 'ERROR')
  assert.equal((await refresh.check()).status, 'UNREVIEWED')
  assert.equal(refresh.status().status, 'UNREVIEWED')
  refresh.stop()
})
