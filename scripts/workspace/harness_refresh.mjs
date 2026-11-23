// Read-only refresh loop for host integrations; activation and baselines stay separate.
import { spawn } from 'node:child_process'

export function createHarnessRefresh({ python, root, baseline, spawnProcess = spawn, timeoutMs = 100000, intervalMs = 86400000 }) {
  let last = { status: 'NOT_CHECKED' }
  let pending
  let child
  let interval
  let stopped = false

  function check() {
    if (stopped) return Promise.resolve({ status: 'STOPPED' })
    if (pending) return pending
    pending = new Promise(resolve => {
      const chunks = []
      let outputBytes = 0
      let settled = false
      let timeout
      const finish = value => {
        if (settled) return
        settled = true
        clearTimeout(timeout)
        child = undefined
        last = value
        resolve(value)
      }
      try {
        child = spawnProcess(python, ['-X', 'utf8', '-m', 'scripts.workspace.harness_library', 'check',
          '--root', root, '--baseline', baseline, '--online', '--format', 'json'], {
          cwd: root, shell: false, windowsHide: true,
          env: { ...process.env, PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8', PYTHONDONTWRITEBYTECODE: '1', PYTHONPATH: root },
        })
        timeout = setTimeout(() => { child?.kill(); finish({ status: 'ERROR', message: 'Source check timed out.' }) }, timeoutMs)
        timeout.unref?.()
        child.stdout.on('data', chunk => {
          const bytes = Buffer.from(chunk)
          outputBytes += bytes.length
          if (outputBytes > 1024 * 1024) {
            child?.kill()
            finish({ status: 'ERROR', message: 'Source check output exceeded the limit.' })
          } else {
            chunks.push(bytes)
          }
        })
        child.stderr.on('data', () => {})
        child.on('error', () => finish({ status: 'ERROR', message: 'Could not start source check.' }))
        child.on('close', code => {
          try {
            const result = JSON.parse(Buffer.concat(chunks).toString('utf8'))
            if (![0, 2].includes(code) || !['UNCHANGED', 'CHANGED', 'UNREVIEWED', 'NOT_CHECKED'].includes(result.status)) throw new Error('invalid result')
            finish(result)
          } catch {
            finish({ status: 'ERROR', message: 'Source check failed or returned invalid output.' })
          }
        })
      } catch {
        finish({ status: 'ERROR', message: 'Could not start source check.' })
      }
    }).finally(() => { pending = undefined })
    return pending
  }

  return {
    check,
    status: () => last,
    start() {
      if (stopped || interval) return
      void check()
      interval = setInterval(() => { void check() }, intervalMs)
      interval.unref?.()
    },
    stop() {
      stopped = true
      clearInterval(interval)
      child?.kill()
    },
  }
}

export function installHarnessRefresh(ctx, options) {
  const refresh = createHarnessRefresh(options)
  const unregister = ctx.tools.register({
    name: 'workspace_harness_status',
    description: 'Show the latest read-only Harness source check and bounded diffs; refresh explicitly to check again. An unreviewed snapshot never authorizes updates.',
    parameters: {
      type: 'object', additionalProperties: false,
      properties: { refresh: { type: 'boolean', description: 'Run a new online source check.' } },
    },
    output: { schema: { type: 'string' }, render: (_args, value) => [{ type: 'text', text: value }] },
    async execute(args = {}) {
      const result = args.refresh === true ? await refresh.check() : refresh.status()
      const display = { ...result }
      if (Array.isArray(result.sources)) {
        display.sources = result.sources.map(row => ({ ...row, diff: (row.diff || '').slice(0, 3000),
          diff_truncated: Boolean(row.diff_truncated || (row.diff || '').length > 3000) }))
      }
      return JSON.stringify(display, null, 2)
    },
  })
  refresh.start()
  return () => {
    refresh.stop()
    if (typeof unregister === 'function') unregister()
  }
}
