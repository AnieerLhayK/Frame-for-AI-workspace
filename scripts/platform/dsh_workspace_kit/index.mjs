/**
 * Workspace authorization gate shared by DSH Desktop and headless CLI.
 * Workspace writes use native sandboxed file tools; external writes go through
 * lease-backed tools that recheck Workspace authority on every invocation.
 */
import { isAbsolute, relative, resolve, sep, dirname, basename, join } from 'node:path'
import { randomUUID } from 'node:crypto'
import { existsSync, lstatSync, readdirSync, readFileSync, realpathSync, statSync, writeFileSync, renameSync, unlinkSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

export const name = 'workspace-kit'
export const inject = ['tools']

export function workspaceDefaults(moduleUrl = import.meta.url) {
  const workspaceRoot = resolve(fileURLToPath(new URL('../../../', moduleUrl)))
  return {
    workspaceRoot,
    leaseRoot: resolve(workspaceRoot, '..', 'data', 'workspace-governance', 'leases'),
  }
}

const DEFAULTS = workspaceDefaults()
const ROOT = DEFAULTS.workspaceRoot

function defaultLeaseRoot(workspaceRoot) {
  return resolve(workspaceRoot, '..', 'data', 'workspace-governance', 'leases')
}
const AGENTS = new Set(['deepseek-harness', 'deepseek-harness-cli'])
const SHELL_TOOLS = new Set(['pwsh', 'bash'])
const FILE_WRITES = new Set(['write', 'edit'])
const FILE_READS = new Set(['read', 'workspace_list'])
const TASK_TOOLS = new Set(['workspace_task_start', 'workspace_task_status', 'workspace_task_update', 'workspace_task_validate', 'workspace_task_finalize'])
const EXTERNAL_FILE_TOOLS = new Set(['workspace_external_read', 'workspace_external_write', 'workspace_external_list'])
const GIT_COMMANDS = new Set(['add', 'branch', 'commit', 'config', 'diff', 'fetch', 'log', 'merge', 'push', 'remote', 'rev-parse', 'show', 'status', 'ls-files'])
const SAFE_TOOLS = new Set([
  'ask_user_question', 'audit_query', 'exit_plan_mode', 'get_goal', 'glob', 'grep', 'job_list', 'job_output',
  'load_workspace_dependencies', 'present', 'read_image', 'session_list', 'skill', 'web_fetch', 'web_search',
])
const FORBIDDEN_PARTS = new Set([
  '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'build', 'dist', 'coverage',
  '.pytest_cache', '.ruff_cache', 'memory', 'memories', 'personal-archive',
  'personal_archive', 'raw', 'raw-corpus', 'raw_corpus', 'corpus', 'private-corpus',
  'private_corpus',
])
const CREDENTIAL_NAMES = new Set(['.npmrc', '.pypirc', 'credentials.json', 'credentials.yaml', 'credentials.yml'])

function clean(value) {
  return typeof value === 'string' ? value.trim() : ''
}

function inside(root, candidate) {
  const rel = relative(resolve(root), resolve(candidate))
  return rel === '' || (!rel.startsWith(`..${sep}`) && rel !== '..' && !isAbsolute(rel))
}

function deny(message) {
  return `workspace-kit guard: ${message}`
}

function commandText(exec) {
  const args = exec?.arguments
  return typeof args?.command === 'string' ? args.command : typeof args?.cmd === 'string' ? args.cmd : ''
}

function shellWords(value) {
  return [...value.matchAll(/"([^"]*)"|'([^']*)'|(\S+)/gu)].map((match) => match[1] ?? match[2] ?? match[3])
}

function ownedTask(task, agentId, sessionId) {
  return Boolean(task && task.status !== 'closed' && task.agent === agentId && task.sessionId === sessionId
    && /^TASK-\d{8}-\d{3,}$/u.test(task.id || ''))
}

function authorizedTask(task, agentId, sessionId, delegatedTaskIds = []) {
  return ownedTask(task, agentId, sessionId)
    || Boolean(task?.delegated === true && task.agent === agentId && task.status === 'in_progress'
      && delegatedTaskIds.includes(task.id) && /^TASK-\d{8}-\d{3,}$/u.test(task.id || ''))
}

function pathArgument(name, args) {
  return name === 'workspace_list' ? args.path : args.file_path ?? args.path
}

function validateWorkspacePath(root, raw, toolName) {
  if (!isAbsolute(raw)) return 'file tools require an absolute Workspace path'
  const target = resolve(raw)
  const inWorkspace = inside(root, target)
  let parent = target
  while (!existsSync(parent)) {
    const next = resolve(parent, '..')
    if (next === parent) return 'file target cannot be resolved safely'
    parent = next
  }
  try {
    const realParent = realpathSync(parent)
    if (inWorkspace && !inside(root, realParent)) return 'linked file target is outside the Workspace sandbox'
    if (!inWorkspace && inside(root, realParent)) return 'external file target resolves back into the Workspace'
    for (let item = target; ; item = resolve(item, '..')) {
      if (existsSync(item) && lstatSync(item).isSymbolicLink()) return 'linked file paths are prohibited'
      if ((inWorkspace && resolve(item) === resolve(root)) || resolve(item, '..') === resolve(item)) break
    }
    if (existsSync(target) && statSync(target).nlink > 1) return 'hard-linked file targets are protected'
  } catch {
    return 'file target identity cannot be verified'
  }
  const parts = target.split(/[\\/]+/u).filter(Boolean)
  if (parts.some((part) => FORBIDDEN_PARTS.has(part.toLowerCase()))) return 'runtime, private corpus and dependency paths are protected'
  const leaf = (parts.at(-1) || '').toLowerCase()
  if (leaf === '.env' || leaf.startsWith('.env.') || CREDENTIAL_NAMES.has(leaf)) return 'credential and environment files are protected'
  if (target.replace(/^[a-z]:/iu, '').includes(':')) return 'alternate data streams are prohibited'
  return undefined
}

function bindingValue(task, name) {
  const prefix = `${name}=`
  return (task?.bindings || []).find((value) => typeof value === 'string' && value.startsWith(prefix))?.slice(prefix.length) || ''
}

function leaseHasScopeWithinRoot(lease, root) {
  const normalizedRoot = resolve(root).toLowerCase()
  return Array.isArray(lease?.path_scopes) && lease.path_scopes.some((scope) => {
    if (typeof scope !== 'string') return false
    const scopedPath = scope.endsWith('/**') || scope.endsWith('\\**') ? scope.slice(0, -3) : scope
    if (!isAbsolute(scopedPath)) return false
    const normalizedScope = resolve(scopedPath).toLowerCase()
    return inside(normalizedRoot, normalizedScope) || inside(normalizedScope, normalizedRoot)
  })
}

function validateExternalLease(cfg, agentId, root, leasePath) {
  if (!isAbsolute(root) || inside(cfg.workspaceRoot, root)) return 'external_root must be an absolute path outside the Workspace'
  if (!isAbsolute(leasePath) || !inside(cfg.leaseRoot, leasePath)) return 'external_lease must be inside the configured Workspace lease store'
  try {
    if (lstatSync(leasePath).isSymbolicLink() || !lstatSync(leasePath).isFile()) return 'external_lease must be a regular file, not a link'
    if (resolve(realpathSync(leasePath)).toLowerCase() !== resolve(leasePath).toLowerCase()) return 'external_lease path cannot traverse a link or junction'
    const lease = JSON.parse(readFileSync(leasePath, 'utf8'))
    if (lease.agent !== agentId || lease.status !== 'active' || !leaseHasScopeWithinRoot(lease, root)) {
      return 'external_lease must be active, match this DSH identity, and scope a path within the external_root'
    }
    if (!Array.isArray(lease.capabilities) || !lease.capabilities.includes('environment_write')) {
      return 'external_lease must grant environment_write'
    }
    if (!existsSync(root) || !statSync(root).isDirectory() || lstatSync(root).isSymbolicLink()) {
      return 'external_root must be an existing, physical directory'
    }
    if (resolve(realpathSync(root)).toLowerCase() !== resolve(root).toLowerCase()) return 'external_root path cannot traverse a link or junction'
  } catch {
    return 'external root or lease cannot be verified safely'
  }
  return undefined
}

function authorizeExternalPath({ cfg, task, agentId, sessionId, path, authorize }) {
  const root = bindingValue(task, 'external-root')
  const leasePath = bindingValue(task, 'external-lease')
  if (!ownedTask(task, agentId, sessionId) || task?.operation !== 'external_write' || !root || !leasePath) {
    return { allowed: false, reason: 'an owned external_write TASK with an exact lease and external root is required' }
  }
  if (!inside(root, path) || inside(cfg.workspaceRoot, path)) return { allowed: false, reason: 'external file path must stay inside the TASK external root' }
  const pathError = validateWorkspacePath(cfg.workspaceRoot, path, 'write')
  if (pathError) return { allowed: false, reason: pathError }
  if (typeof authorize !== 'function') return { allowed: false, reason: 'Workspace authority check is unavailable' }
  return authorize({ agentId, sessionId, taskId: task.id, path: resolve(path), operation: 'write', leasePath })
}

export function externalFileTools(config, authorize = cliCheck, findTask = activeTask) {
  const workspaceRoot = clean(config.workspaceRoot) || ROOT
  const cfg = { ...config, workspaceRoot,
    leaseRoot: clean(config.leaseRoot) || defaultLeaseRoot(workspaceRoot) }
  const definitions = [
    {
      ...toolText('workspace_external_read', 'Read a text file under the exact external root of the current lease-backed external_write TASK.', {
        file_path: { type: 'string', minLength: 1, description: 'Absolute path inside the active TASK external root.' },
      }, ['file_path']),
      async execute(args = {}, invocation) {
        const sessionId = clean(invocation?.agent?.session?.id)
        const task = sessionId ? findTask(cfg.workspaceRoot, cfg.agentId, sessionId, cfg.delegatedTaskIds) : undefined
        const path = clean(args.file_path)
        const check = authorizeExternalPath({ cfg, task, agentId: cfg.agentId, sessionId, path,
          authorize: (request) => authorize(request, cfg) })
        if (!check?.allowed) throw new Error(`workspace external read denied: ${check?.reason || 'Workspace authority denied'}`)
        if (!lstatSync(path).isFile()) throw new Error('workspace external read denied: target must be a regular file')
        const size = statSync(path).size
        if (size > 1_000_000) throw new Error('workspace external read denied: files over 1 MB are not supported')
        return readFileSync(path, 'utf8')
      },
    },
    {
      ...toolText('workspace_external_write', 'Write or replace one text file under the exact external root of the current lease-backed external_write TASK. Parent directories must already exist.', {
        file_path: { type: 'string', minLength: 1, description: 'Absolute path inside the active TASK external root.' },
        content: { type: 'string', maxLength: 1_000_000, description: 'Complete replacement file content, up to 1 MB.' },
      }, ['file_path', 'content']),
      async execute(args = {}, invocation) {
        const sessionId = clean(invocation?.agent?.session?.id)
        const task = sessionId ? findTask(cfg.workspaceRoot, cfg.agentId, sessionId, cfg.delegatedTaskIds) : undefined
        const path = clean(args.file_path)
        if (typeof args.content !== 'string' || args.content.length > 1_000_000) throw new Error('workspace external write denied: content must be text no larger than 1 MB')
        const check = authorizeExternalPath({ cfg, task, agentId: cfg.agentId, sessionId, path,
          authorize: (request) => authorize(request, cfg) })
        if (!check?.allowed) throw new Error(`workspace external write denied: ${check?.reason || 'Workspace authority denied'}`)
        const targetStat = existsSync(path) ? lstatSync(path) : undefined
        if (targetStat?.isSymbolicLink() || (targetStat?.isFile() && statSync(path).nlink > 1)) {
          throw new Error('workspace external write denied: linked or hard-linked targets are prohibited')
        }
        if (targetStat && !targetStat.isFile()) throw new Error('workspace external write denied: target must be a regular file')
        const parent = dirname(path)
        if (!existsSync(parent) || !statSync(parent).isDirectory()) throw new Error('workspace external write denied: parent directory must already exist')
        const temp = join(parent, `.${basename(path)}.${randomUUID()}.workspace-kit.tmp`)
        try {
          writeFileSync(temp, args.content, { flag: 'wx', encoding: 'utf8' })
          const finalCheck = authorizeExternalPath({ cfg, task, agentId: cfg.agentId, sessionId, path,
            authorize: (request) => authorize(request, cfg) })
          if (!finalCheck?.allowed) throw new Error(`Workspace authority changed: ${finalCheck?.reason || 'denied'}`)
          const latest = existsSync(path) ? lstatSync(path) : undefined
          if (latest?.isSymbolicLink() || (latest?.isFile() && statSync(path).nlink > 1) || (latest && !latest.isFile())) {
            throw new Error('target identity changed during write')
          }
          renameSync(temp, path)
        } catch (error) {
          if (existsSync(temp)) unlinkSync(temp)
          throw new Error(`workspace external write failed: ${error.message}`)
        }
        return `Wrote ${args.content.length} characters.`
      },
    },
    {
      ...toolText('workspace_external_list', 'List direct entries under the exact external root of the current lease-backed external_write TASK. Listing is nonrecursive and capped at 100 entries.', {
        path: { type: 'string', minLength: 1, description: 'Absolute directory inside the active TASK external root.' },
      }, ['path']),
      async execute(args = {}, invocation) {
        const sessionId = clean(invocation?.agent?.session?.id)
        const task = sessionId ? findTask(cfg.workspaceRoot, cfg.agentId, sessionId, cfg.delegatedTaskIds) : undefined
        const path = clean(args.path)
        const check = authorizeExternalPath({ cfg, task, agentId: cfg.agentId, sessionId, path,
          authorize: (request) => authorize(request, cfg) })
        if (!check?.allowed) throw new Error(`workspace external list denied: ${check?.reason || 'Workspace authority denied'}`)
        if (!statSync(path).isDirectory()) throw new Error('workspace external list denied: path must be a directory')
        return JSON.stringify(readdirSync(path, { withFileTypes: true })
          .filter((entry) => !isRestrictedDirectoryEntry(entry.name))
          .slice(0, 100)
          .map((entry) => ({ name: entry.name, type: entry.isDirectory() ? 'directory' : entry.isFile() ? 'file' : 'other' })))
      },
    },
  ]
  return definitions
}

function validateShell(exec, root, task, agentId, sessionId, preflight, devPreflight, authorize, branch, delegatedTaskIds) {
  const command = commandText(exec)
  if (!command) return deny('shell request has no command')
  const normalized = command.replace(/\//g, '\\').replace(/\s+/g, ' ').trim().toLowerCase()
  const cwd = clean(exec?.agent?.session?.header?.cwd)
  if (!cwd || !inside(root, cwd)) return deny('shell working directory must be inside the Workspace')
  const start = /^(?:workspace|python\s+-m\s+scripts\.workspace\.workspace_cli)\s+records\s+start\s+--task-type\s+[a-z0-9_-]+\s+--operation\s+workspace_write\s+--owner-agent\s+["']?([a-z0-9_-]+)["']?\s+--owner-session\s+["']?([^"'\s;&|]+)["']?\s*$/iu.exec(command.trim())
  if (start) {
    if (start[1] !== agentId || start[2] !== sessionId) return deny('TASK start must bind the current DSH identity and session')
    return undefined
  }
  if (!authorizedTask(task, agentId, sessionId, delegatedTaskIds)) return deny('an active TASK owned by this DSH session is required')
  if (/[$`]/u.test(command)) return deny('PowerShell expressions and command chaining are disabled')
  const commandWithoutQuotedStrings = command.replace(/"(?:[^"]|"")*"|'(?:[^']|'')*'/gu, '""')
  if (/[;&|(){}\r\n]/u.test(commandWithoutQuotedStrings)) return deny('PowerShell expressions and command chaining are disabled')
  if (!/^(?:git\b|workspace\b|python\s+-m\s+(?:scripts\.workspace\.(?:workspace_cli|merge_safety)|scripts\.validation\.[a-z0-9_.-]+|pytest|unittest)\b|node\s+--test\b|get-(?:content|childitem|location|date)\b|test-path\b|resolve-path\b|select-string\b|rg\b)/iu.test(command.trim())) {
    return deny('shell command is not in the Workspace command policy')
  }
  const gitCommand = /^git\s+([a-z-]+)\b/iu.exec(normalized)
  if (gitCommand && !GIT_COMMANDS.has(gitCommand[1])) {
    return deny(`Git command is not registered in the Workspace policy: ${gitCommand[1]}`)
  }
  const branchList = /^git\s+branch(?:\s+(.+))?$/iu.exec(command.trim())
  if (branchList && branchList[1] && !/^(?:--show-current|--list(?:\s+[^-].*)?|--all|--remotes|--verbose|--no-color)$/iu.test(branchList[1])) {
    return deny('only read-only branch listing is allowed')
  }
  const remote = /^git\s+remote(?:\s+(.+))?$/iu.exec(command.trim())
  if (remote && remote[1] && /^(?:add|set-url|remove|rename|prune)\b/iu.test(remote[1])) return deny('registered Git remotes cannot be modified')
  if (remote && remote[1] && !/^(?:-v|--verbose)$/iu.test(remote[1])) return deny('only read-only remote listing is allowed')
  if (/\bgit\s+(?:reset|restore)\b|\bgit\s+checkout\s+--\b|\bgit\s+commit\b[^\n]*\s--amend\b/iu.test(normalized)) {
    return deny('Git reset, restore and history-rewriting commits are prohibited')
  }
  if (/\b(?:remove-item|remove-itemproperty|clear-content|set-content|add-content|out-file|move-item|copy-item|rename-item|new-item|start-process|invoke-webrequest|invoke-restmethod|format-volume|diskpart|reg\s+add)\b|\b(?:python|node|pwsh|powershell|cmd(?:\.exe)?)\s+(?:-c|-e|\/c)\b|(?:^|\s)>{1,2}\s*[^=]/iu.test(command)) {
    return deny('shell filesystem and host configuration writes are disabled; use guarded Workspace file tools')
  }
  if (/\[(?:system\.)?io\.(?:file|directory|filestream)\]|(?:system\.)?io\.(?:file|directory|filestream)::|::(?:writeall|appendall|delete|move|copy|create|openwrite)\w*/iu.test(command)) {
    return deny('PowerShell .NET filesystem APIs are disabled; use guarded Workspace file tools')
  }
  if (/\b(?:reset\s+--hard|clean\s+-[a-z]*[fx]|push\s+[^\n]*(?:--force\b|-f\b|--force-with-lease)|checkout\s+--\s+\.|restore\s+--worktree\s+\.)/iu.test(normalized)) {
    return deny('destructive Git operations are prohibited')
  }
  if (/\bgit\s+(?:switch|checkout)\b/iu.test(normalized)) return deny('branch switching is prohibited in the shared worktree')
  if (/\bgit\s+(?:rebase|cherry-pick|revert)\b|\bgit\s+branch\s+(?:--(?:delete|move|force|copy)|-(?:d|D|m|M|f|c))\b/iu.test(normalized)) {
    return deny('history rewrite and shared branch deletion or rename are prohibited')
  }
  if (/\bgit\s+-c\b|\b--config-env\b/iu.test(normalized)) return deny('per-command Git configuration overrides are prohibited')
  if (/\bgit\s+config\b/iu.test(normalized)
    && !/\bgit\s+config\s+(?:--get|--get-regexp|--list|--show-origin|-l)\b/iu.test(normalized)) {
    return deny('Git configuration changes are prohibited')
  }
  if (/\bgit\s+remote\s+(?:add|set-url|remove|rename|prune)\b/iu.test(normalized)) {
    return deny('registered Git remotes cannot be modified')
  }
  const fetch = normalized.match(/\bgit\s+fetch\b([^\n;&|]*)/u)
  if (fetch) {
    const fields = fetch[1].split(/\s+/u).filter(Boolean).filter((item) => !item.startsWith('-'))
    if (fields[0] !== 'origin' || fields.length !== 1) return deny('only the registered origin remote may be fetched')
  }
  if (/\bgit\s+pull\b/iu.test(normalized)) return deny('implicit pull/merge is disabled; use the registered merge preflight')
  const add = /^git\s+add(?:\s+(.+))?$/iu.exec(command.trim())
  if (add) {
    const words = shellWords(add[1] || '').filter((word) => word !== '--')
    if (!words.length || words.some((word) => word.startsWith('-') || /[*?\[\]]/u.test(word) || ['.', '..'].includes(word))) {
      return deny('git add requires explicit non-wildcard Workspace file paths')
    }
    if (typeof authorize !== 'function') return deny('Workspace authority check is unavailable for git add')
    for (const word of words) {
      const path = resolve(cwd, word)
      const pathError = validateWorkspacePath(root, path, 'write')
      if (pathError) return deny(pathError)
      const check = authorize({ agentId, sessionId, taskId: task.id, path, operation: 'write' })
      if (!check?.allowed) return deny(check?.reason || 'Workspace TASK or path authority denied for git add')
    }
  }
  if (/^git\s+commit\b/iu.test(command.trim())) {
    if ((branch || gitBranch(cwd)) !== 'dev') return deny('Git commits are allowed only on dev')
    if (!devPreflight(task, agentId)) return deny('Git commit requires strict TASK scope and workflow validation')
  }
  const push = normalized.match(/\bgit\s+push\b([^\n;&|]*)/u)
  if (push) {
    if (!/^git\s+push\s+origin\s+(?:dev|main)$/u.test(normalized)) {
      return deny('push must be a single canonical push command to one registered branch target')
    }
    if (/--(?:delete|mirror|all|tags|repo)(?:=|\s|$)|(?:^|\s)-d(?:\s|$)/u.test(push[1])) return deny('bulk, delete and alternate-repository pushes are prohibited')
    const fields = push[1].split(/\s+/u).filter(Boolean).filter((item) => !item.startsWith('-'))
    if (fields[0] !== 'origin' || !['dev', 'main'].includes(fields[1])) return deny('only origin/dev and origin/main are registered push targets')
    if (fields.length !== 2) return deny('a push command may specify only one registered branch target')
    const actualBranch = branch || gitBranch(cwd)
    if (actualBranch !== fields[1]) return deny(`push target must match the current ${fields[1]} branch`)
    if (fields[1] === 'main' && !preflight(task, agentId)) return deny('main push requires the registered merge preflight and audit-close evidence')
    if (fields[1] === 'dev' && !devPreflight(task, agentId)) return deny('dev push requires strict TASK scope and workflow validation')
  }
  if (/\bgit\s+merge\b/iu.test(normalized)) {
    const ffMain = /^git\s+merge\s+--ff-only\s+dev$/u.test(normalized)
    if (!ffMain || (branch || gitBranch(cwd)) !== 'main' || !preflight(task, agentId)) {
      return deny('main integration requires the canonical ff-only dev merge after merge preflight')
    }
  }
  const taskMutation = /^(?:workspace|python\s+-m\s+scripts\.workspace\.workspace_cli)\s+records\s+(?:update|finalize|report-usage)\s+["']?([^\s"';&|]+)/iu.exec(command.trim())
  if (taskMutation && taskMutation[1].toLowerCase() !== task.id.toLowerCase()) {
    return deny('TASK lifecycle commands must target the current owned TASK')
  }
  return undefined
}

function gitBranch(cwd) {
  const result = spawnSync('git', ['-C', cwd, 'branch', '--show-current'], {
    encoding: 'utf8', windowsHide: true, timeout: 10000, maxBuffer: 1024 * 1024,
  })
  return result.status === 0 ? clean(result.stdout) : ''
}

function activeTask(root, agentId, sessionId, delegatedTaskIds = []) {
  const recordsRoot = resolve(root, 'PROJECT_CONTEXT', 'tasks', 'records')
  const matches = []
  let budget = 1200
  const walk = (directory, depth) => {
    if (depth > 4 || budget <= 0) return
    let entries
    try { entries = readdirSync(directory, { withFileTypes: true }) } catch { return }
    for (const entry of entries) {
      if (budget <= 0) break
      const path = resolve(directory, entry.name)
      if (entry.isDirectory()) walk(path, depth + 1)
      else if (entry.isFile() && entry.name.endsWith('.json')) {
        budget -= 1
        try {
          const record = JSON.parse(readFileSync(path, 'utf8'))
          if (record.status === 'in_progress' && record.owner?.kind === 'workspace_session' && record.owner.agent === agentId) {
            const ownerSession = record.owner.session_id
            const delegated = ownerSession !== sessionId && delegatedTaskIds.includes(record.task_id)
            if (ownerSession === sessionId || delegated) matches.push({ id: record.task_id, type: record.task_type,
              agent: agentId, sessionId: ownerSession, status: record.status, delegated,
              operation: Array.isArray(record.registration?.operations) ? record.registration.operations[0] : 'workspace_write',
              bindings: Array.isArray(record.owner.bindings) ? record.owner.bindings : [] })
          }
        } catch { /* unreadable records never grant authority */ }
      }
    }
  }
  walk(recordsRoot, 0)
  const owned = matches.filter((task) => !task.delegated)
  if (owned.length === 1) return owned[0]
  if (owned.length > 1) return { ambiguous: true }
  const delegated = matches.filter((task) => task.delegated && delegatedTaskIds.includes(task.id))
  if (delegated.length > 1) return { ambiguous: true }
  return delegated[0]
}

function cliCheck(request, cfg) {
  const python = clean(cfg.python) || process.env.DSH_WORKSPACE_PYTHON || 'python'
  const args = ['-m', 'scripts.workspace.workspace_cli', 'agent', 'check',
    '--agent', request.agentId, '--operation', 'write', '--path', request.path,
    '--record-id', request.taskId]
  if (request.leasePath) args.push('--lease', request.leasePath)
  args.push('--format', 'json')
  const result = spawnSync(python, args, {
    cwd: cfg.workspaceRoot,
    encoding: 'utf8',
    windowsHide: true,
    timeout: 20000,
    maxBuffer: 2 * 1024 * 1024,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1', PYTHONPATH: cfg.workspaceRoot },
  })
  if (result.error || result.status !== 0) return { allowed: false, reason: 'Workspace agent check failed closed' }
  try {
    const decision = JSON.parse(result.stdout)
    return { allowed: decision.status === 'ALLOW', reason: decision.reason }
  } catch {
    return { allowed: false, reason: 'Workspace agent check returned invalid JSON' }
  }
}

function runWorkspaceCli(cfg, args) {
  const python = clean(cfg.python) || process.env.DSH_WORKSPACE_PYTHON || 'python'
  const result = spawnSync(python, ['-m', 'scripts.workspace.workspace_cli', ...args], {
    cwd: cfg.workspaceRoot, encoding: 'utf8', windowsHide: true, timeout: 120000,
    maxBuffer: 4 * 1024 * 1024,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1', PYTHONPATH: cfg.workspaceRoot },
  })
  if (result.error) return { ok: false, text: result.error.message }
  return { ok: result.status === 0, text: `${result.stdout || ''}${result.stderr || ''}`.trim() || '(no output)' }
}

function toolText(name, description, properties = {}, required = []) {
  return {
    name, description,
    parameters: { type: 'object', additionalProperties: false, properties, required },
    output: { schema: { type: 'string' }, render: (_args, value) => [{ type: 'text', text: value }] },
  }
}

function isRestrictedDirectoryEntry(name) {
  const normalized = name.toLowerCase()
  return normalized.startsWith('.') || FORBIDDEN_PARTS.has(normalized) || CREDENTIAL_NAMES.has(normalized)
    || normalized === '.env' || normalized.startsWith('.env.')
}

export function taskTools(cfg, execute = runWorkspaceCli, findTask = activeTask) {
  return [
    {
      ...toolText('workspace_task_start', 'Create one active Workspace TASK owned by this DSH identity and session. Choose its exact registered task type before writing.', {
        task_type: { type: 'string', minLength: 1, description: 'Exact registered Workspace task id.' },
        operation: { type: 'string', enum: ['workspace_write', 'external_write'], description: 'Use external_write only with a validated exact-root lease.' },
        external_root: { type: 'string', minLength: 1, description: 'Existing physical directory outside Workspace, required for external_write.' },
        external_lease: { type: 'string', minLength: 1, description: 'Active environment_write lease file, required for external_write.' },
        bindings: { type: 'array', items: { type: 'string', pattern: '^[a-zA-Z0-9_-]+=\\S.*$' }, description: 'Exact registered task bindings as name=value strings.' },
      }, ['task_type']),
      async execute(args = {}, invocation) {
        const sessionId = clean(invocation?.agent?.session?.id)
        if (!sessionId) return 'TASK start denied: DSH session identity is unavailable.'
        if (findTask(cfg.workspaceRoot, cfg.agentId, sessionId, cfg.delegatedTaskIds)) return 'TASK start denied: finalize the active owned TASK first.'
        const taskType = clean(args.task_type)
        if (!/^[a-z0-9][a-z0-9_-]*$/iu.test(taskType)) return 'TASK start denied: task_type must be an exact registered id.'
        const bindings = Array.isArray(args.bindings) ? args.bindings : []
        if (bindings.some((item) => typeof item !== 'string' || !/^[a-zA-Z0-9_-]+=\S.*$/u.test(item))) {
          return 'TASK start denied: every binding must be an exact name=value string.'
        }
        const operation = clean(args.operation) || 'workspace_write'
        if (!['workspace_write', 'external_write'].includes(operation)) return 'TASK start denied: unsupported operation.'
        if (operation === 'external_write' && bindings.some((item) => /^(?:external-root|external-lease)=/iu.test(item))) {
          return 'TASK start denied: external_root and external_lease are reserved bindings.'
        }
        const command = ['records', 'start', '--task-type', taskType, '--operation', operation,
          '--owner-agent', cfg.agentId, '--owner-session', sessionId]
        if (operation === 'external_write') {
          const externalRoot = clean(args.external_root)
          const leasePath = clean(args.external_lease)
          const leaseRoot = clean(cfg.leaseRoot) || defaultLeaseRoot(cfg.workspaceRoot)
          const leaseError = validateExternalLease({ workspaceRoot: cfg.workspaceRoot, leaseRoot }, cfg.agentId, externalRoot, leasePath)
          if (leaseError) return `TASK start denied: ${leaseError}.`
          const validation = execute(cfg, ['agent', 'lease', 'validate', leasePath, '--format', 'json'])
          if (!validation.ok) return `TASK start denied: lease validation failed. ${validation.text}`
          let leaseResult
          try { leaseResult = JSON.parse(validation.text) } catch { return 'TASK start denied: lease validator returned invalid JSON.' }
          if (leaseResult.status !== 'PASS' || leaseResult.active !== true) return 'TASK start denied: lease is not valid and active.'
          command.push('--bind', `external-root=${externalRoot}`, '--bind', `external-lease=${leasePath}`)
        } else if (args.external_root || args.external_lease) {
          return 'TASK start denied: external_root and external_lease require external_write.'
        }
        for (const binding of bindings) command.push('--bind', binding)
        const result = execute(cfg, command)
        return result.ok ? result.text : `TASK start failed: ${result.text}`
      },
    },
    {
      ...toolText('workspace_task_status', 'Show the active Workspace TASK owned by this DSH identity and session.'),
      async execute(_args = {}, invocation) {
        const sessionId = clean(invocation?.agent?.session?.id)
        const task = sessionId ? findTask(cfg.workspaceRoot, cfg.agentId, sessionId, cfg.delegatedTaskIds) : undefined
        return task?.ambiguous ? 'Multiple active TASKs match this DSH session. Finalize or close them before writing.'
          : task ? JSON.stringify(task) : 'No active TASK is owned by this DSH session.'
      },
    },
    {
      ...toolText('workspace_task_update', 'Record progress or validation evidence on the active Workspace TASK owned by this DSH session.', {
        note: { type: 'string', minLength: 1, maxLength: 4000, description: 'One progress note to append.' },
        validation: { type: 'string', enum: ['not_run', 'passed', 'failed', 'blocked'], description: 'Current validation outcome.' },
        command: { type: 'array', maxItems: 20, items: { type: 'string', minLength: 1, maxLength: 4000 }, description: 'Validation commands to append.' },
        evidence: { type: 'array', maxItems: 20, items: { type: 'string', minLength: 1, maxLength: 4000 }, description: 'Validation evidence references to append.' },
      }),
      async execute(args = {}, invocation) {
        const sessionId = clean(invocation?.agent?.session?.id)
        const task = sessionId ? findTask(cfg.workspaceRoot, cfg.agentId, sessionId, cfg.delegatedTaskIds) : undefined
        if (!task || task.ambiguous || !ownedTask(task, cfg.agentId, sessionId)) {
          return 'TASK update denied: exactly one active TASK owned by this DSH session is required.'
        }
        const note = clean(args.note)
        const commands = Array.isArray(args.command) ? args.command : []
        const evidence = Array.isArray(args.evidence) ? args.evidence : []
        const validation = clean(args.validation)
        if ((args.note !== undefined && (!note || note.length > 4000))
          || (validation && !['not_run', 'passed', 'failed', 'blocked'].includes(validation))
          || [commands, evidence].some((items) => items.length > 20
            || items.some((item) => typeof item !== 'string' || !item.trim() || item.length > 4000))
          || !(note || validation || commands.length || evidence.length)) {
          return 'TASK update denied: provide bounded progress or validation fields.'
        }
        const command = ['records', 'update', task.id]
        if (note) command.push('--note', note)
        if (validation) command.push('--validation', validation)
        for (const item of commands) command.push('--command', item)
        for (const item of evidence) command.push('--evidence', item)
        const result = execute(cfg, command)
        return result.ok ? result.text : `TASK update failed: ${result.text}`
      },
    },
    {
      ...toolText('workspace_task_validate', 'Run strict Workspace change-scope and workflow checks for this DSH session’s active TASK.'),
      async execute(_args = {}, invocation) {
        const sessionId = clean(invocation?.agent?.session?.id)
        const task = sessionId ? findTask(cfg.workspaceRoot, cfg.agentId, sessionId, cfg.delegatedTaskIds) : undefined
        if (!task || task.ambiguous) return 'TASK validation denied: exactly one active owned or explicitly delegated TASK is required.'
        const bindings = task.bindings.flatMap((binding) => ['--bind', binding])
        const scope = execute(cfg, ['changes', 'verify', task.type, '--agent', cfg.agentId, '--strict', ...bindings])
        if (!scope.ok) return `TASK change-scope validation failed:\n${scope.text}`
        const workflow = execute(cfg, ['workflow', 'check', task.type, '--record-id', task.id, '--agent', cfg.agentId, '--strict', ...bindings])
        return workflow.ok ? `TASK validation passed.\n${workflow.text}` : `TASK workflow validation failed:\n${workflow.text}`
      },
    },
    {
      ...toolText('workspace_task_finalize', 'Finalize only this DSH session’s active Workspace TASK after checks have been recorded.', {
        status: { type: 'string', enum: ['successful', 'failed', 'cancelled'] },
        validation: { type: 'string', enum: ['passed', 'failed', 'blocked', 'not_run'] },
        usability: { type: 'string', enum: ['usable', 'limited', 'unusable', 'unknown'] },
        human_edit_rounds: { type: 'integer', minimum: 0 },
      }, ['status', 'validation', 'usability', 'human_edit_rounds']),
      async execute(args = {}, invocation) {
        const sessionId = clean(invocation?.agent?.session?.id)
        const task = sessionId ? findTask(cfg.workspaceRoot, cfg.agentId, sessionId, cfg.delegatedTaskIds) : undefined
        if (!task || task.ambiguous) return 'TASK finalization denied: exactly one active owned or explicitly delegated TASK is required.'
        if (args.status === 'successful') {
          if (args.validation !== 'passed') return 'TASK finalization denied: successful TASKs require passed validation.'
          const bindings = task.bindings.flatMap((binding) => ['--bind', binding])
          const scope = execute(cfg, ['changes', 'verify', task.type, '--agent', cfg.agentId, '--strict', ...bindings])
          if (!scope.ok) return `TASK finalization denied: strict change-scope validation failed.\n${scope.text}`
          const workflow = execute(cfg, ['workflow', 'check', task.type, '--record-id', task.id, '--agent', cfg.agentId, '--strict', ...bindings])
          if (!workflow.ok) return `TASK finalization denied: strict workflow check failed.\n${workflow.text}`
        }
        const result = execute(cfg, ['records', 'finalize', task.id, '--status', args.status,
          '--validation', args.validation, '--usability', args.usability,
          '--human-edit-rounds', String(args.human_edit_rounds)])
        return result.ok ? result.text : `TASK finalization failed: ${result.text}`
      },
    },
  ]
}

function mainPushPreflight(task, agentId, cfg) {
  if (!authorizedTask(task, agentId, task?.delegated ? '' : task?.sessionId, cfg.delegatedTaskIds)) return false
  const python = clean(cfg.python) || process.env.DSH_WORKSPACE_PYTHON || 'python'
  const result = spawnSync(python, ['-m', 'scripts.workspace.merge_safety', 'main', '--head', 'main',
    '--agent', agentId, '--record-id', task.id, '--for-push', '--format', 'json'], {
    cwd: cfg.workspaceRoot, encoding: 'utf8', windowsHide: true, timeout: 120000,
    maxBuffer: 4 * 1024 * 1024,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1', PYTHONPATH: cfg.workspaceRoot },
  })
  if (result.error || result.status !== 0) return false
  try { return JSON.parse(result.stdout).status === 'PASS' } catch { return false }
}

function devPushPreflight(task, agentId, cfg) {
  if (!authorizedTask(task, agentId, task?.delegated ? '' : task?.sessionId, cfg.delegatedTaskIds)) return false
  const python = clean(cfg.python) || process.env.DSH_WORKSPACE_PYTHON || 'python'
  const bindings = (task.bindings || []).flatMap((binding) => ['--bind', binding])
  const env = { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1', PYTHONPATH: cfg.workspaceRoot }
  const verify = spawnSync(python, ['-m', 'scripts.workspace.workspace_cli', 'changes', 'verify', task.type,
    '--agent', agentId, '--strict', ...bindings], {
    cwd: cfg.workspaceRoot, encoding: 'utf8', windowsHide: true, timeout: 120000,
    maxBuffer: 4 * 1024 * 1024, env,
  })
  if (verify.error || verify.status !== 0) return false
  const workflow = spawnSync(python, ['-m', 'scripts.workspace.workspace_cli', 'workflow', 'check', task.type,
    '--record-id', task.id, '--agent', agentId, '--strict', ...bindings], {
    cwd: cfg.workspaceRoot, encoding: 'utf8', windowsHide: true, timeout: 120000,
    maxBuffer: 4 * 1024 * 1024, env,
  })
  return !workflow.error && workflow.status === 0
}

/** Public host-tool seam. `authorize` returns `{allowed: boolean, reason?: string}`. */
export function guardDecision(exec, config = {}, authorize, preflight = () => false, devPreflight = () => false) {
  const root = clean(config.workspaceRoot) || ROOT
  const agentId = clean(config.agentId)
  const sessionId = clean(exec?.agent?.session?.id)
  if (!AGENTS.has(agentId)) return deny('DSH agent identity is missing or unregistered')
  if (!sessionId) return deny('DSH session identity is missing')

  const name = clean(exec?.name).toLowerCase()
  if (SHELL_TOOLS.has(name)) return validateShell(exec, root, config.activeTask, agentId, sessionId,
    preflight, devPreflight, authorize, config.branch, config.delegatedTaskIds)
  if (FILE_READS.has(name) || FILE_WRITES.has(name)) {
    const raw = clean(pathArgument(name, exec?.arguments || {}))
    if (!raw) return deny('file path is required')
    const pathError = validateWorkspacePath(root, raw, name)
    if (pathError) return deny(pathError)
    const externalPath = !inside(root, resolve(raw))
    if (externalPath) return deny('native DSH file tools are Workspace-only; use lease-backed workspace_external_* tools')
    if (FILE_WRITES.has(name)) {
      const task = config.activeTask
      if (!authorizedTask(task, agentId, sessionId, config.delegatedTaskIds)) return deny('an active TASK owned by this DSH session is required')
      if (typeof authorize !== 'function') return deny('Workspace authority check is unavailable')
      const check = authorize({ agentId, sessionId, taskId: task.id, path: resolve(raw), operation: 'write' })
      if (!check?.allowed) return deny(check?.reason || 'Workspace TASK or path authority denied')
    }
    return undefined
  }
  if (!name) return deny('tool identity is missing')
  // These registered tools enforce session, TASK, path and lease authority in their own execute handlers.
  if (TASK_TOOLS.has(name) || EXTERNAL_FILE_TOOLS.has(name)) return undefined
  return SAFE_TOOLS.has(name) ? undefined : deny(`tool ${name} is not registered in the Workspace authorization policy`)
}

export function apply(ctx, config = {}) {
  const delegatedTaskIds = Array.isArray(config.delegatedTaskIds)
    ? [...new Set(config.delegatedTaskIds.filter((value) => typeof value === 'string' && /^TASK-\d{8}-\d{3,}$/u.test(value)))]
    : []
  const workspaceRoot = clean(config.workspaceRoot) || ROOT
  const cfg = { ...config, delegatedTaskIds, workspaceRoot,
    leaseRoot: clean(config.leaseRoot) || defaultLeaseRoot(workspaceRoot) }
  try {
    if (!AGENTS.has(clean(cfg.agentId))) throw new Error('agentId must be deepseek-harness or deepseek-harness-cli')
    if (typeof ctx?.tools?.guard !== 'function') throw new Error('host tool guard API is unavailable')
    if (typeof ctx?.tools?.register !== 'function') throw new Error('host tool registration API is unavailable')
    const execute = typeof cfg.runWorkspaceCli === 'function' ? cfg.runWorkspaceCli : runWorkspaceCli
    for (const tool of taskTools(cfg, execute)) ctx.tools.register(tool)
    for (const tool of externalFileTools(cfg, (request) => cliCheck(request, cfg), activeTask)) ctx.tools.register(tool)
    ctx.tools.guard((exec) => {
      const sessionId = clean(exec?.agent?.session?.id)
      const currentTask = activeTask(cfg.workspaceRoot, clean(cfg.agentId), sessionId, cfg.delegatedTaskIds)
      return guardDecision(exec, { ...cfg, activeTask: currentTask }, (request) => cliCheck(request, cfg),
        (task, agentId) => mainPushPreflight(task, agentId, cfg),
        (task, agentId) => devPushPreflight(task, agentId, cfg))
    })
  } catch (error) {
    throw new Error(`workspace-kit authorization guard failed to initialize: ${error.message}`)
  }
}
