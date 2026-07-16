#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");

const DEFAULT_HERMES_EXE = "${DATA_ROOT}/hermes\\hermes-agent\\venv\\Scripts\\hermes.exe";
const STEP_TIMEOUT_MS = Number(process.env.CLAUDE_NOTIFY_STEP_TIMEOUT_MS || 30_000);
const TOTAL_TIMEOUT_MS = Number(process.env.CLAUDE_NOTIFY_TOTAL_TIMEOUT_MS || 60_000);
const LOG_PATH = path.join(os.tmpdir(), "claude-code-notifications", "hermes-mcp-client.log");

function parseArgs(argv) {
  const result = {
    minutes: "?",
    message: "",
    messageFile: "",
    targets: [],
    selfTest: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === "--minutes" && next) {
      result.minutes = next;
      i += 1;
    } else if (arg === "--message" && next) {
      result.message = next;
      i += 1;
    } else if (arg === "--message-file" && next) {
      result.messageFile = next;
      i += 1;
    } else if (arg === "--target" && next) {
      result.targets.push(...next.split(",").map((value) => value.trim()).filter(Boolean));
      i += 1;
    } else if (arg === "--self-test") {
      result.selfTest = true;
    } else if (!arg.startsWith("--") && result.minutes === "?") {
      result.minutes = arg;
    }
  }

  if (result.targets.length === 0) {
    const envTargets = process.env.CLAUDE_NOTIFY_TARGETS || "qqbot";
    result.targets = envTargets.split(",").map((value) => value.trim()).filter(Boolean);
  }

  if (!result.message) {
    if (result.messageFile) {
      result.message = fs.readFileSync(result.messageFile, "utf8");
    } else {
      result.message = `Claude Code task completed in ${result.minutes} minute(s).`;
    }
  }

  return result;
}

function appendLog(line) {
  try {
    fs.mkdirSync(path.dirname(LOG_PATH), { recursive: true });
    fs.appendFileSync(LOG_PATH, line, "utf8");
  } catch {
    // Keep hook failures non-blocking.
  }
}

function logInfo(message) {
  appendLog(`${new Date().toISOString()} INFO ${message}\n`);
}

function logFailure(error) {
  appendLog(`${new Date().toISOString()} ERROR ${error.stack || error.message || String(error)}\n`);
}

function getToolText(result) {
  if (!result) {
    return "";
  }
  if (result.structuredContent && typeof result.structuredContent.result === "string") {
    return result.structuredContent.result;
  }
  if (Array.isArray(result.content)) {
    return result.content
      .map((item) => (item && item.type === "text" && typeof item.text === "string" ? item.text : ""))
      .filter(Boolean)
      .join("\n");
  }
  return "";
}

function parseJsonObject(text) {
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

class MCPTransport {
  constructor(proc) {
    this.proc = proc;
    this.buffer = Buffer.alloc(0);
    this.pending = new Map();
    this.nextId = 1;
    this.closed = false;

    proc.stdout.on("data", (chunk) => {
      this.buffer = Buffer.concat([this.buffer, chunk]);
      this.drain();
    });

    proc.on("close", () => {
      this.close();
    });
    proc.on("error", () => {
      this.close();
    });
  }

  drain() {
    while (!this.closed) {
      if (this.buffer[0] === 0x7b) {
        const newline = this.buffer.indexOf(Buffer.from("\n"));
        if (newline === -1) {
          break;
        }

        const line = this.buffer.subarray(0, newline).toString("utf8").trim();
        this.buffer = this.buffer.subarray(newline + 1);
        if (!line) {
          continue;
        }
        try {
          this.dispatch(JSON.parse(line));
        } catch {
          // Ignore malformed newline-delimited logs.
        }
        continue;
      }

      const delimiter = Buffer.from("\r\n\r\n");
      const headerEnd = this.buffer.indexOf(delimiter);
      if (headerEnd === -1) {
        const newline = this.buffer.indexOf(Buffer.from("\n"));
        if (newline === -1) {
          break;
        }
        this.buffer = this.buffer.subarray(newline + 1);
        continue;
      }
      const header = this.buffer.subarray(0, headerEnd).toString("ascii");
      const match = header.match(/Content-Length:\s*(\d+)/i);
      if (!match) {
        const newline = this.buffer.indexOf(Buffer.from("\n"));
        if (newline === -1) {
          break;
        }
        this.buffer = this.buffer.subarray(newline + 1);
        continue;
      }

      const length = Number(match[1]);
      const bodyStart = headerEnd + delimiter.length;
      if (this.buffer.length < bodyStart + length) {
        break;
      }

      const body = this.buffer.subarray(bodyStart, bodyStart + length).toString("utf8");
      this.buffer = this.buffer.subarray(bodyStart + length);

      try {
        this.dispatch(JSON.parse(body));
      } catch {
        // Ignore malformed frames from noisy startup logs.
      }
    }
  }

  dispatch(message) {
    if (message.method && message.id !== undefined && message.id !== null) {
      this.send({ jsonrpc: "2.0", id: message.id, result: {} });
      return;
    }

    if (message.id !== undefined && message.id !== null) {
      const resolver = this.pending.get(message.id);
      if (resolver) {
        this.pending.delete(message.id);
        resolver(message);
      }
    }
  }

  send(payload) {
    if (this.closed) {
      return;
    }
    const body = JSON.stringify(payload);
    this.proc.stdin.write(`${body}\n`);
  }

  request(method, params) {
    const id = this.nextId;
    this.nextId += 1;
    const payload = { jsonrpc: "2.0", id, method };
    if (params !== undefined) {
      payload.params = params;
    }
    this.send(payload);

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Timed out waiting for ${method}#${id}`));
      }, STEP_TIMEOUT_MS);

      this.pending.set(id, (response) => {
        clearTimeout(timer);
        if (response.error) {
          reject(new Error(response.error.message || JSON.stringify(response.error)));
        } else {
          resolve(response.result);
        }
      });
    });
  }

  notify(method, params) {
    const payload = { jsonrpc: "2.0", method };
    if (params !== undefined) {
      payload.params = params;
    }
    this.send(payload);
  }

  close() {
    if (this.closed) {
      return;
    }
    this.closed = true;
    for (const resolver of this.pending.values()) {
      resolver({ error: { message: "Connection closed" } });
    }
    this.pending.clear();
  }
}

async function resolveTarget(transport, target) {
  if (!target || target.includes(":") || target === "all") {
    return target;
  }

  const channelsResult = await transport.request("tools/call", {
    name: "channels_list",
    arguments: { platform: target },
  });
  const channelsPayload = parseJsonObject(getToolText(channelsResult));
  const channels = channelsPayload && Array.isArray(channelsPayload.channels) ? channelsPayload.channels : [];
  if (channels.length === 1 && channels[0].target) {
    const resolved = String(channels[0].target);
    logInfo(`resolved target ${target} -> ${resolved}`);
    return resolved;
  }
  if (channels.length > 1) {
    throw new Error(`Target ${target} is ambiguous; channels_list returned ${channels.length} channels`);
  }
  throw new Error(`Target ${target} was not found by channels_list`);
}

async function sendNotifications(options) {
  const hermesExe = process.env.HERMES_EXE || DEFAULT_HERMES_EXE;
  if (!fs.existsSync(hermesExe)) {
    throw new Error(`Hermes executable not found: ${hermesExe}`);
  }

  const proc = spawn(hermesExe, ["mcp", "serve"], {
    stdio: ["pipe", "pipe", "pipe"],
    env: { ...process.env },
  });
  let stderr = "";
  proc.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  const transport = new MCPTransport(proc);
  const totalTimer = setTimeout(() => {
    transport.close();
    proc.kill();
  }, TOTAL_TIMEOUT_MS);

  try {
    await transport.request("initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "claude-code-long-task-notifier", version: "2.0.0" },
    });
    transport.notify("notifications/initialized");
    logInfo("initialized hermes mcp");

    if (options.selfTest) {
      await transport.request("tools/list");
      logInfo("self-test tools/list succeeded");
      const resolvedTargets = [];
      for (const target of options.targets) {
        resolvedTargets.push(await resolveTarget(transport, target));
      }
      console.log(`Self-test OK: Hermes MCP initialized; targets=${resolvedTargets.join(",")}`);
      transport.notify("exit");
      return;
    }

    for (const target of options.targets) {
      const resolvedTarget = await resolveTarget(transport, target);
      logInfo(`sending target=${resolvedTarget} minutes=${options.minutes}`);
      await transport.request("tools/call", {
        name: "messages_send",
        arguments: {
          target: resolvedTarget,
          message: `Claude Code\n${options.message}`,
        },
      });
      logInfo(`sent target=${resolvedTarget}`);
    }

    transport.notify("exit");
  } catch (error) {
    if (stderr) {
      error.message = `${error.message}\nHermes stderr:\n${stderr.slice(-2000)}`;
    }
    throw error;
  } finally {
    clearTimeout(totalTimer);
    transport.close();
    if (!proc.killed) {
      const killTimer = setTimeout(() => proc.kill("SIGKILL"), 2000);
      proc.once("exit", () => clearTimeout(killTimer));
      proc.stdin.end();
    }
  }
}

sendNotifications(parseArgs(process.argv.slice(2))).catch((error) => {
  logFailure(error);
  process.exit(1);
});
