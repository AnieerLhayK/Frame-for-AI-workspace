// Dedicated Workspace SDK transport. The ordinary Desktop entry is unaffected.
import {spawnSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';

export const name = 'workspace-guarded-transport';
export const inject = ['tools', 'agents', 'workingDirectory', 'credentials'];

function guardResult(execution) {
  const python = process.env.DSH_GUARD_PYTHON;
  const guard = process.env.DSH_GUARD_SCRIPT;
  if (!python || !guard) return {allowed: false, reason: 'Workspace guard unavailable'};
  const result = spawnSync(python, ['-B', guard], {
    input: JSON.stringify({name: execution.name, arguments: execution.arguments}),
    encoding: 'utf8', windowsHide: true, timeout: 30000,
  });
  if (result.status !== 0) return {allowed: false, reason: 'Workspace guard unavailable'};
  try {
    const verdict = JSON.parse(result.stdout);
    return verdict && typeof verdict === 'object' ? verdict : {allowed: false, reason: 'Workspace guard unavailable'};
  } catch {
    return {allowed: false, reason: 'Workspace guard unavailable'};
  }
}

export function checkTool(execution) {
  const verdict = guardResult(execution);
  return verdict.allowed === true ? undefined : (verdict.reason || 'Workspace guard denied');
}

export async function apply(ctx) {
  const modules = process.env.DSH_WORKSPACE_MODULES;
  if (!modules || !process.env.DSH_PROJECT_ROOT) throw new Error('Workspace configuration missing');
  const load = name => import(pathToFileURL(`${modules}/@deepseek-ai/${name}/lib/index.js`).href);
  const {HarnessSdkJsonRpcServer} = await load('dsh-sdk-jsonrpc-server');
  const {JsonRpcLineTransport} = await load('dsh-sdk-protocol');
  const {defineTool} = await load('dsh-tools');
  const wire = new JsonRpcLineTransport(process.stdin, process.stdout);
  const server = new HarnessSdkJsonRpcServer(ctx, wire, {maxTokensAsSuccess: false});
  const resolveCredential = ctx.credentials.resolve.bind(ctx.credentials);
  ctx.credentials.resolve = async key => {
    const description = await ctx.credentials.describe(key);
    return description.source === 'file' ? resolveCredential(key) : undefined;
  };
  ctx.effect(() => () => {ctx.credentials.resolve = resolveCredential;}, 'workspace:managed-credentials');
  ctx.tools.guard(checkTool);
  ctx.tools.register(defineTool({
    name: 'workspace_list',
    description: 'List one project directory without recursively scanning hidden, dependency or private corpus paths.',
    parameters: {path: {type: 'string', required: true, description: 'Absolute project directory path.'}},
    output: {
      schema: {type: 'object', additionalProperties: false, properties: {
        text: {type: 'string', required: true},
      }},
      render: (_args, value) => [{type: 'text', text: value.text}],
    },
    async execute(args) {
      const result = guardResult({name: 'workspace_list', arguments: args});
      if (result.allowed !== true || !Array.isArray(result.entries)) throw new Error(result.reason || 'Workspace directory unavailable');
      return {text: JSON.stringify({entries: result.entries, truncated: result.truncated})};
    },
  }));
  wire.onRequest(async (method, params = {}) => {
    await ctx.get('loader').await();
    if (method === 'workspace/preflight') {
      const denied = checkTool({name: 'pwsh', arguments: {command: 'guard-probe'}});
      if (!denied || denied === 'Workspace guard unavailable') throw new Error('Workspace guard preflight failed');
      return {guard: true, workspace: process.env.DSH_PROJECT_ROOT};
    }
    if (!['initialize', 'session/prompt', 'session/wait', 'shutdown'].includes(method)) throw new Error('Unsupported Workspace operation');
    if (method === 'initialize' && params.cwd !== process.env.DSH_PROJECT_ROOT) throw new Error('Workspace directory mismatch');
    const result = await server.handleRequest(method, params);
    if (method === 'shutdown') setImmediate(async () => {await ctx.root.fiber.dispose(); process.exit(0);});
    return result;
  });
  ctx.effect(() => {wire.start(); return async () => {await server.shutdown(); wire.close();};}, 'workspace:stdio');
}
