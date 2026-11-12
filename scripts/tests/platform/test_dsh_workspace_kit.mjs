import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'
import { apply, externalFileTools, guardDecision, taskTools, workspaceDefaults } from '../../platform/dsh_workspace_kit/index.mjs'

const root = resolve(fileURLToPath(new URL('../../../', import.meta.url)))
const leasePath = join(root, '..', 'leases', 'test.json')
const outsideWorkspace = resolve(root, '..', 'outside')

test('default workspace and lease roots are derived from the installed plugin location', () => {
  const pluginUrl = new URL('../../platform/dsh_workspace_kit/index.mjs', import.meta.url)
  const workspaceRoot = resolve(fileURLToPath(new URL('../../../', pluginUrl)))
  assert.deepEqual(workspaceDefaults(pluginUrl.href), {
    workspaceRoot,
    leaseRoot: resolve(workspaceRoot, '..', 'data', 'workspace-governance', 'leases'),
  })
})

test('host guard denies writes when the session identity is missing', () => {
  const result = guardDecision({ name: 'write', arguments: { file_path: `${root}\\README.md` } }, {
    workspaceRoot: root,
    agentId: 'deepseek-harness',
  })
  assert.match(result, /session|identity/i)
})

test('host guard denies unclassified tools and leaves known read tools available', () => {
  const exec = (name, args = {}) => ({ name, arguments: args,
    agent: { session: { id: 'session-1', header: { cwd: root } } } })
  const config = { workspaceRoot: root, agentId: 'deepseek-harness' }
  assert.match(guardDecision(exec('session_send', { session_id: 'other', message: 'hello' }), config), /not registered in the Workspace authorization policy/i)
  assert.equal(guardDecision(exec('read', { file_path: `${root}\\README.md` }), config), undefined)
  assert.equal(guardDecision(exec('web_search', { query: 'workspace docs' }), config), undefined)
})

test('host guard authorizes file writes with the matching owned TASK', () => {
  const calls = []
  const exec = {
    name: 'write',
    arguments: { file_path: `${root}\\README.md`, content: 'updated' },
    agent: { session: { id: 'session-1', header: { cwd: root } } },
  }
  const authorize = (request) => {
    calls.push(request)
    return { allowed: request.agentId === 'deepseek-harness-cli'
      && request.sessionId === 'session-1'
      && request.path === `${root}\\README.md`
      && request.taskId === 'TASK-20261112-001' }
  }
  const result = guardDecision(exec, {
    workspaceRoot: root,
    agentId: 'deepseek-harness-cli',
    activeTask: { id: 'TASK-20261112-001', agent: 'deepseek-harness-cli', sessionId: 'session-1' },
  }, authorize)
  assert.equal(result, undefined)
  assert.equal(calls.length, 1)
  assert.equal(calls[0].path, `${root}\\README.md`)
})

test('host guard directs external paths to lease-backed external file tools', () => {
  const externalRoot = mkdtempSync(join(tmpdir(), 'dsh-workspace-kit-external-'))
  try {
    const path = join(externalRoot, 'task-output.txt')
    writeFileSync(path, 'existing')
    const task = { id: 'TASK-20261112-020', agent: 'deepseek-harness-cli', sessionId: 'session-1', status: 'in_progress' }
    const exec = (name) => ({ name, arguments: { file_path: path }, agent: { session: { id: 'session-1', header: { cwd: root } } } })
    const config = { workspaceRoot: root, agentId: 'deepseek-harness-cli', activeTask: task }
    assert.match(guardDecision(exec('read'), config, () => ({ allowed: true })), /lease-backed workspace_external/i)
    assert.match(guardDecision(exec('write'), config, () => ({ allowed: true })), /lease-backed workspace_external/i)
  } finally {
    rmSync(externalRoot, { recursive: true, force: true })
  }
})

test('host guard rejects writes to another session TASK', () => {
  const exec = {
    name: 'write',
    arguments: { file_path: `${root}\\README.md`, content: 'updated' },
    agent: { session: { id: 'session-1', header: { cwd: root } } },
  }
  const result = guardDecision(exec, {
    workspaceRoot: root,
    agentId: 'deepseek-harness',
    activeTask: { id: 'TASK-20261112-002', agent: 'deepseek-harness-cli', sessionId: 'session-1' },
  }, () => ({ allowed: true }))
  assert.match(result, /TASK|owner|agent/i)
})

test('host guard accepts an exact TASK only when the profile lists that user delegation', () => {
  const exec = {
    name: 'write', arguments: { file_path: `${root}\\README.md`, content: 'delegated' },
    agent: { session: { id: 'session-1', header: { cwd: root } } },
  }
  const task = { id: 'TASK-20261112-005', agent: 'deepseek-harness', sessionId: 'owner-session', status: 'in_progress', delegated: true }
  const authorize = ({ taskId }) => ({ allowed: taskId === task.id })
  assert.equal(guardDecision(exec, { workspaceRoot: root, agentId: 'deepseek-harness', activeTask: task,
    delegatedTaskIds: [task.id] }, authorize), undefined)
  assert.match(guardDecision(exec, { workspaceRoot: root, agentId: 'deepseek-harness', activeTask: task,
    delegatedTaskIds: [] }, authorize), /TASK|owner|agent/i)
})

test('host guard binds TASK start to the configured DSH identity and session', () => {
  const exec = {
    name: 'pwsh',
    arguments: { command: 'workspace records start --task-type ai_workbench_development --operation workspace_write --owner-agent deepseek-harness --owner-session session-1' },
    agent: { session: { id: 'session-1', header: { cwd: root } } },
  }
  assert.equal(guardDecision(exec, { workspaceRoot: root, agentId: 'deepseek-harness' }), undefined)
  const wrongOwner = { ...exec, arguments: { command: exec.arguments.command.replace('deepseek-harness', 'codex') } }
  assert.match(guardDecision(wrongOwner, { workspaceRoot: root, agentId: 'deepseek-harness' }), /identity and session/i)
  const injected = { ...exec, arguments: { command: `${exec.arguments.command}; Remove-Item README.md` } }
  assert.match(guardDecision(injected, { workspaceRoot: root, agentId: 'deepseek-harness' }), /active TASK/i)
})

test('host shell cannot update another TASK through the Python CLI alias', () => {
  const config = { workspaceRoot: root, agentId: 'deepseek-harness-cli',
    activeTask: { id: 'TASK-20261112-103', agent: 'deepseek-harness-cli', sessionId: 'session-1', status: 'in_progress' } }
  const exec = { name: 'pwsh', arguments: { command: 'python -m scripts.workspace.workspace_cli records update TASK-20261112-104 --note unauthorized' },
    agent: { session: { id: 'session-1', header: { cwd: root } } } }
  assert.match(guardDecision(exec, config), /current owned TASK/i)
})

test('host guard limits Git pushes to the matching origin branch and blocks force push', () => {
  const exec = (command) => ({
    name: 'pwsh', arguments: { command },
    agent: { session: { id: 'session-1', header: { cwd: root } } },
  })
  const config = {
    workspaceRoot: root,
    agentId: 'deepseek-harness-cli',
    activeTask: { id: 'TASK-20261112-003', agent: 'deepseek-harness-cli', sessionId: 'session-1' },
    branch: 'dev',
  }
  assert.equal(guardDecision(exec('git push origin dev'), config, undefined, undefined, () => true), undefined)
  assert.match(guardDecision(exec('git push origin dev HEAD:main'), config), /single canonical push command/i)
  assert.match(guardDecision(exec('git push origin dev refs/heads/dev:refs/heads/main'), config), /single canonical push command/i)
  assert.match(guardDecision(exec('git push origin dev; git push origin HEAD:main'), config), /command chaining|single canonical push command/i)
  assert.match(guardDecision(exec('git status $(cmd.exe /c whoami)'), config), /PowerShell expressions/i)
  assert.match(guardDecision(exec('git status "$(cmd.exe /c whoami)"'), config), /PowerShell expressions/i)
  assert.match(guardDecision(exec(`git -C ${outsideWorkspace} push origin dev`), config), /Git configuration overrides|single canonical push command|Git command is not registered/i)
  assert.match(guardDecision(exec(`[IO.File]::WriteAllText('${root}\\other.txt','x')`), config), /not in the Workspace command policy|command chaining|\.NET filesystem APIs/i)
  assert.match(guardDecision(exec('git push other dev'), config), /registered push targets|single canonical push command/i)
  assert.match(guardDecision(exec('git push origin dev --force'), config), /destructive Git/i)
  assert.match(guardDecision(exec('git push origin --delete dev'), config), /bulk, delete|single canonical push command/i)
  assert.match(guardDecision(exec('git remote set-url origin https://example.invalid/repo'), config), /remotes cannot be modified/i)
  assert.match(guardDecision(exec('git fetch backup'), config), /registered origin/i)
  assert.match(guardDecision(exec('git pull origin dev'), config), /implicit pull|Git command is not registered/i)
  assert.match(guardDecision(exec('git push origin dev'), { ...config, branch: 'main' }), /current dev branch/i)
  assert.match(guardDecision(exec('git push origin dev'), config), /dev push requires strict TASK scope/i)
  assert.equal(guardDecision(exec('git push origin dev'), config, undefined, undefined, () => true), undefined)
  assert.match(guardDecision(exec('git push origin main'), { ...config, branch: 'main' }, undefined, () => false), /main push requires/i)
  assert.match(guardDecision(exec('git branch -f main dev'), config), /read-only branch listing|Git command is not registered/i)
  assert.match(guardDecision(exec('git update-ref refs/heads/main HEAD'), config), /Git command is not registered/i)
  assert.match(guardDecision(exec('git fetch origin dev main'), config), /only the registered origin remote/i)
  assert.match(guardDecision(exec('git merge --ff-only dev HEAD'), { ...config, branch: 'main' }, undefined, () => true), /canonical ff-only dev merge/i)
  assert.match(guardDecision(exec('git add README.md'), config), /Workspace authority check is unavailable/i)
  assert.match(guardDecision(exec('git add .'), config, () => ({ allowed: true })), /explicit non-wildcard/i)
  assert.equal(guardDecision(exec('git add README.md'), config, () => ({ allowed: true })), undefined)
  assert.match(guardDecision(exec('git commit -m "change"'), config, undefined, undefined, () => false), /strict TASK scope/i)
})

test('host guard denies shell access outside the Workspace sandbox', () => {
  const exec = {
    name: 'pwsh', arguments: { command: 'Get-ChildItem' },
    agent: { session: { id: 'session-1', header: { cwd: resolve(root, '..', 'data') } } },
  }
  assert.match(guardDecision(exec, { workspaceRoot: root, agentId: 'deepseek-harness' }), /working directory/i)
})

test('host plugin fails initialization when the DSH host guard API is unavailable', () => {
  assert.throws(() => apply({ tools: {} }, { agentId: 'deepseek-harness' }), /guard API is unavailable/i)
})

test('host plugin registers valid schema and starts an owned TASK from the current session', async () => {
  const tools = new Map()
  let guard
  const calls = []
  apply({ tools: {
    register: (definition) => tools.set(definition.name, definition),
    guard: (handler) => { guard = handler },
  } }, {
    workspaceRoot: root,
    agentId: 'deepseek-harness-cli',
    runWorkspaceCli: (_cfg, args) => {
      calls.push(args)
      return { ok: true, text: '{"task_id":"TASK-20261112-004"}' }
    },
  })
  assert.equal(typeof guard, 'function')
  const sessionExec = (name, arguments_ = {}) => ({ name, arguments: arguments_,
    agent: { session: { id: 'session-cli', header: { cwd: root } } } })
  assert.equal(guard(sessionExec('workspace_task_start', { task_type: 'ai_workbench_development' })), undefined)
  assert.equal(guard(sessionExec('workspace_task_status')), undefined)
  assert.equal(guard(sessionExec('workspace_task_update', { note: 'validation running' })), undefined)
  assert.equal(guard(sessionExec('workspace_external_write', { file_path: `${root}\\README.md`, content: 'x' })), undefined)
  for (const name of ['workspace_task_update', 'workspace_external_read', 'workspace_external_write', 'workspace_external_list']) {
    assert.ok(tools.has(name), `${name} is registered`)
  }
  for (const definition of tools.values()) {
    assert.equal(definition.parameters.type, 'object')
    assert.ok(Array.isArray(definition.parameters.required))
  }
  const result = await tools.get('workspace_task_start').execute({ task_type: 'ai_workbench_development', bindings: ['package=ai-workbench'] }, {
    agent: { session: { id: 'session-cli' } },
  })
  assert.equal(result, '{"task_id":"TASK-20261112-004"}')
  assert.deepEqual(calls[0], ['records', 'start', '--task-type', 'ai_workbench_development', '--operation', 'workspace_write',
    '--owner-agent', 'deepseek-harness-cli', '--owner-session', 'session-cli', '--bind', 'package=ai-workbench'])
  const denied = await tools.get('workspace_task_start').execute({ task_type: 'ai_workbench_development' }, {})
  assert.match(denied, /session identity/i)
})

test('TASK status, validation and successful finalization stay bound to the owned TASK', async () => {
  const calls = []
  const task = { id: 'TASK-20261112-020', type: 'dsh_desktop_integration', agent: 'deepseek-harness-cli',
    sessionId: 'session-lifecycle', status: 'in_progress', bindings: ['package=workspace'] }
  const definitions = new Map(taskTools({ workspaceRoot: root, agentId: task.agent, delegatedTaskIds: [] }, (_cfg, args) => {
    calls.push(args)
    return { ok: true, text: 'PASS' }
  }, () => task).map((definition) => [definition.name, definition]))
  const invocation = { agent: { session: { id: task.sessionId } } }
  assert.equal(await definitions.get('workspace_task_status').execute({}, invocation), JSON.stringify(task))
  assert.match(await definitions.get('workspace_task_finalize').execute({ status: 'successful', validation: 'not_run',
    usability: 'usable', human_edit_rounds: 0 }, invocation), /require passed validation/i)
  assert.equal(calls.length, 0)
  assert.equal(await definitions.get('workspace_task_validate').execute({}, invocation), 'TASK validation passed.\nPASS')
  assert.equal(await definitions.get('workspace_task_finalize').execute({ status: 'successful', validation: 'passed',
    usability: 'usable', human_edit_rounds: 0 }, invocation), 'PASS')
  assert.deepEqual(calls.slice(-3), [
    ['changes', 'verify', task.type, '--agent', task.agent, '--strict', '--bind', 'package=workspace'],
    ['workflow', 'check', task.type, '--record-id', task.id, '--agent', task.agent, '--strict', '--bind', 'package=workspace'],
    ['records', 'finalize', task.id, '--status', 'successful', '--validation', 'passed', '--usability', 'usable', '--human-edit-rounds', '0'],
  ])
})

test('TASK updates persist progress and validation evidence only for the owned active TASK', async () => {
  const calls = []
  const task = { id: 'TASK-20261112-101', type: 'ai_workbench_development', agent: 'deepseek-harness-cli',
    sessionId: 'session-101', status: 'in_progress', bindings: ['package=workspace'] }
  const definitions = new Map(taskTools({ workspaceRoot: root, agentId: task.agent }, (_cfg, args) => {
    calls.push(args)
    return { ok: true, text: 'updated' }
  }, () => task).map((definition) => [definition.name, definition]))
  const update = definitions.get('workspace_task_update')
  assert.ok(update, 'the shared host guard exposes an owned TASK update operation')
  assert.equal(await update.execute({ note: 'CLI acceptance started', validation: 'passed',
    command: ['git status --short --branch'], evidence: ['headless CLI returned exit code 0'] },
  { agent: { session: { id: task.sessionId } } }), 'updated')
  assert.deepEqual(calls, [[
    'records', 'update', task.id, '--note', 'CLI acceptance started', '--validation', 'passed',
    '--command', 'git status --short --branch', '--evidence', 'headless CLI returned exit code 0',
  ]])
})

test('external TASK start requires a validated identity-matched lease and binds its exact root', async (context) => {
  const calls = []
  const fixture = mkdtempSync(join(tmpdir(), 'dsh-external-task-'))
  context.after(() => rmSync(fixture, { recursive: true, force: true }))
  const externalRoot = join(fixture, 'target')
  const leaseRoot = join(fixture, 'leases')
  mkdirSync(externalRoot)
  mkdirSync(leaseRoot)
  const lease = join(leaseRoot, 'dsh-test.json')
  writeFileSync(lease, JSON.stringify({ agent: 'deepseek-harness-cli', status: 'active',
    capabilities: ['environment_write'], path_scopes: [externalRoot] }))
  const definitions = new Map(taskTools({ workspaceRoot: root, agentId: 'deepseek-harness-cli',
    leaseRoot }, (_cfg, args) => {
    calls.push(args)
    if (args[0] === 'agent') return { ok: true, text: JSON.stringify({ status: 'PASS', active: true, agent: 'deepseek-harness-cli' }) }
    return { ok: true, text: 'TASK-20261112-021' }
  }, () => undefined).map((definition) => [definition.name, definition]))
  const start = definitions.get('workspace_task_start')
  const result = await start.execute({ task_type: 'dsh_desktop_integration', operation: 'external_write',
    external_root: externalRoot, external_lease: lease }, { agent: { session: { id: 'external-session' } } })
  assert.equal(result, 'TASK-20261112-021')
  assert.deepEqual(calls[0], ['agent', 'lease', 'validate', lease, '--format', 'json'])
  assert.deepEqual(calls[1], ['records', 'start', '--task-type', 'dsh_desktop_integration', '--operation', 'external_write',
    '--owner-agent', 'deepseek-harness-cli', '--owner-session', 'external-session', '--bind', `external-root=${externalRoot}`,
    '--bind', `external-lease=${lease}`])
  const exactFile = join(externalRoot, 'cordis.patch.yml')
  writeFileSync(exactFile, 'profile: test')
  writeFileSync(lease, JSON.stringify({ agent: 'deepseek-harness-cli', status: 'active',
    capabilities: ['environment_write'], path_scopes: [exactFile] }))
  assert.equal(await start.execute({ task_type: 'dsh_desktop_integration', operation: 'external_write',
    external_root: externalRoot, external_lease: lease }, { agent: { session: { id: 'exact-file-session' } } }), 'TASK-20261112-021')
  assert.deepEqual(calls[3], ['records', 'start', '--task-type', 'dsh_desktop_integration', '--operation', 'external_write',
    '--owner-agent', 'deepseek-harness-cli', '--owner-session', 'exact-file-session', '--bind', `external-root=${externalRoot}`,
    '--bind', `external-lease=${lease}`])
  writeFileSync(lease, JSON.stringify({ agent: 'deepseek-harness', status: 'active',
    capabilities: ['environment_write'], path_scopes: [externalRoot] }))
  const deniedStart = taskTools({ workspaceRoot: root, agentId: 'deepseek-harness-cli', leaseRoot },
    (_cfg, args) => { calls.push(args); return { ok: true, text: 'unexpected' } }, () => undefined)
    .find((definition) => definition.name === 'workspace_task_start')
  assert.match(await deniedStart.execute({ task_type: 'dsh_desktop_integration', operation: 'external_write',
    external_root: externalRoot, external_lease: lease }, { agent: { session: { id: 'external-session' } } }), /match this DSH identity/u)
  assert.equal(calls.length, 4, 'invalid lease is rejected before TASK registration')
})

test('external file tools recheck the TASK and lease for each read and write', async () => {
  const externalRoot = mkdtempSync(join(tmpdir(), 'dsh-external-tools-'))
  try {
    const task = { id: 'TASK-20261112-021', type: 'dsh_desktop_integration', agent: 'deepseek-harness-cli',
      sessionId: 'external-session', status: 'in_progress', operation: 'external_write',
      bindings: [`external-root=${externalRoot}`, `external-lease=${leasePath}`] }
    const calls = []
    const definitions = new Map(externalFileTools({ workspaceRoot: root, agentId: task.agent },
      (request) => { calls.push(request); return { allowed: request.taskId === task.id } }, () => task)
      .map((definition) => [definition.name, definition]))
    const invocation = { agent: { session: { id: task.sessionId } } }
    const target = join(externalRoot, 'note.txt')
    assert.equal(await definitions.get('workspace_external_write').execute({ file_path: target, content: 'scoped result' }, invocation), 'Wrote 13 characters.')
    assert.equal(await definitions.get('workspace_external_read').execute({ file_path: target }, invocation), 'scoped result')
    assert.deepEqual(calls.map(({ taskId, leasePath, path, operation }) => ({ taskId, leasePath, path, operation })), [
      { taskId: task.id, leasePath, path: target, operation: 'write' },
      { taskId: task.id, leasePath, path: target, operation: 'write' },
      { taskId: task.id, leasePath, path: target, operation: 'write' },
    ])
    const denied = externalFileTools({ workspaceRoot: root, agentId: task.agent }, () => ({ allowed: false, reason: 'lease path mismatch' }), () => task)
    await assert.rejects(denied.find((tool) => tool.name === 'workspace_external_write')
      .execute({ file_path: join(externalRoot, 'denied.txt'), content: 'no' }, invocation), /lease path mismatch/u)
    assert.equal(existsSync(join(externalRoot, 'denied.txt')), false)
  } finally {
    rmSync(externalRoot, { recursive: true, force: true })
  }
})

test('external directory listings omit hidden, protected and dependency entries', async () => {
  const externalRoot = mkdtempSync(join(tmpdir(), 'dsh-external-list-'))
  try {
    for (const name of ['.hidden', '.env', 'credentials.json', 'node_modules', 'private-corpus', 'visible.txt']) {
      const target = join(externalRoot, name)
      if (name === 'node_modules' || name === 'private-corpus') mkdirSync(target)
      else writeFileSync(target, 'entry')
    }
    const task = { id: 'TASK-20261112-021', agent: 'deepseek-harness-cli', sessionId: 'external-session',
      status: 'in_progress', operation: 'external_write',
      bindings: [`external-root=${externalRoot}`, `external-lease=${leasePath}`] }
    const list = externalFileTools({ workspaceRoot: root, agentId: task.agent },
      () => ({ allowed: true }), () => task).find((tool) => tool.name === 'workspace_external_list')
    const entries = JSON.parse(await list.execute({ path: externalRoot },
      { agent: { session: { id: task.sessionId } } }))
    assert.deepEqual(entries.map(({ name }) => name), ['visible.txt'])
  } finally {
    rmSync(externalRoot, { recursive: true, force: true })
  }
})

test('Git gate pushes dev and ff-only main only to a local bare origin after preflight', (context) => {
  const fixture = mkdtempSync(join(tmpdir(), 'dsh-workspace-git-'))
  context.after(() => rmSync(fixture, { recursive: true, force: true }))
  const remote = join(fixture, 'remote.git')
  const repo = join(fixture, 'repo')
  const stdio = 'inherit'
  mkdirSync(repo)
  const git = (cwd, ...args) => {
    const result = spawnSync('git', ['-C', cwd, ...args], { encoding: 'utf8', windowsHide: true, stdio })
    assert.equal(result.status, 0, result.stderr || result.error?.message)
    return result.stdout?.trim()
  }
  const init = spawnSync('git', ['init', '--bare', '-q', remote], { encoding: 'utf8', windowsHide: true, stdio })
  assert.equal(init.status, 0, init.stderr || init.error?.message)
  const initRepo = spawnSync('git', ['init', '-q', '-b', 'dev', repo], { encoding: 'utf8', windowsHide: true, stdio })
  assert.equal(initRepo.status, 0, initRepo.stderr || initRepo.error?.message)
  git(repo, 'config', 'user.name', 'DSH fixture')
  git(repo, 'config', 'user.email', 'dsh-fixture@example.invalid')
  writeFileSync(join(repo, 'source.txt'), 'dev\n')
  git(repo, 'add', 'source.txt')
  git(repo, 'commit', '-m', 'fixture base')
  git(repo, 'remote', 'add', 'origin', remote)
  const task = { id: 'TASK-20261112-006', agent: 'deepseek-harness-cli', sessionId: 'session-1', status: 'in_progress' }
  const shell = (command) => ({ name: 'pwsh', arguments: { command }, agent: { session: { id: 'session-1', header: { cwd: repo } } } })
  const config = { workspaceRoot: fixture, agentId: task.agent, activeTask: task, branch: 'dev' }
  assert.equal(guardDecision(shell('git push origin dev'), config, undefined, undefined, () => true), undefined)
  git(repo, 'push', 'origin', 'dev')
  writeFileSync(join(repo, 'source.txt'), 'main advances\n')
  git(repo, 'add', 'source.txt')
  git(repo, 'commit', '-m', 'dev advance')
  git(repo, 'branch', 'main', 'HEAD~1')
  git(repo, 'checkout', 'main')
  const mainDenied = { ...config, branch: 'main' }
  assert.match(guardDecision(shell('git merge --ff-only dev'), mainDenied), /preflight/i)
  assert.equal(guardDecision(shell('git merge --ff-only dev'), mainDenied, undefined, () => true), undefined)
  git(repo, 'merge', '--ff-only', 'dev')
  assert.match(guardDecision(shell('git push origin main'), mainDenied), /preflight/i)
  assert.equal(guardDecision(shell('git push origin main'), mainDenied, undefined, () => true), undefined)
  git(repo, 'push', 'origin', 'main')
  assert.equal(readFileSync(join(remote, 'refs', 'heads', 'main'), 'utf8').trim(),
    readFileSync(join(repo, '.git', 'refs', 'heads', 'main'), 'utf8').trim())
  assert.match(guardDecision(shell('git push unregistered dev'), config), /registered push targets|single canonical push command/i)
})
