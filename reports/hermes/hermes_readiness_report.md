# Hermes Readiness Report

Generated: 2026-06-08

Post-action update:

- `terminal.cwd` is now fixed to `${WORKSPACE_ROOT}`.
- Gateway restarted successfully after the change.
- New gateway PID observed: `32488`.
- Weixin was later rebound to `802846c3be7e@im.bot`.
- Gateway restarted again with PID `35976`.
- Weixin DM `hello` reached Hermes and received a response.

## Bottom Line

Hermes is usable today as both a QQ-controlled and Weixin-DM-controlled local agent runner, now with the local tool working directory fixed to `${WORKSPACE_ROOT}`.

## Answers

### 1. Is Hermes currently usable?

Yes, with scope limits.

Confirmed:

- Gateway is running.
- DeepSeek provider works.
- QQBot is configured and connected.
- QQ inbound messages have triggered real Hermes agent turns.
- QQ outbound send test succeeded.
- Hermes has core execution tools: terminal, file, code execution, messaging, memory, skills, todo, cronjob, delegation.

Remaining limitations:

- Browser/web/vision/image generation are not fully available.
- Email is configured but IMAP auth fails.
- Ordinary Weixin group delivery is not proven and may not be supported by iLink bot identities.

### 2. Is Weixin truly usable?

Yes for direct messages after rebind.

Confirmed:

- Weixin adapter connects to iLink.
- Account is an `@im.bot` iLink bot identity.
- Home channel/user ID is configured.
- User DM `hello` reached Hermes.
- Hermes called DeepSeek and sent a Weixin response.

Not confirmed:

- Ordinary Weixin group messages.
- Long-term stability of the new iLink session over restarts/days.

Current verdict: Weixin DM is working and can be used as a remote-control channel. Group use remains risky/unproven.

### 3. Is QQ truly usable?

Yes.

Evidence:

- Historical QQ C2C inbound messages in `agent.log`.
- Agent responses sent back through QQBot.
- Active `hermes send` probe to QQBot succeeded and returned a QQBot message ID.
- Session state records active QQBot DM session.

Current verdict: QQBot is the primary working remote-control channel.

### 4. Is Hermes worth adding to the existing Agent ecosystem?

Yes.

Reason:

- It already bridges messaging into a real local agent loop.
- QQBot can remotely trigger local tools against the machine.
- It can be run from `${WORKSPACE_ROOT}` and load workspace rules.
- It complements Codex/Claude Code/OpenCode by acting as the always-on messaging gateway and orchestration shell.

Main caution:

- Do not treat Weixin as production-ready until inbound pairing and response are proven.
- Do not enable open Weixin access before confirming the bot identity and access boundaries.

## Highest-Priority Next 5 Things

1. Monitor Weixin stability across at least one gateway restart and one overnight idle period.

2. Run one QQ remote workspace probe.
   - From QQ, ask Hermes to inspect `${WORKSPACE_ROOT}` or create a harmless timestamped report under `reports\hermes\probe`.
   - Confirm output returns through QQ.

3. Install Playwright Chromium only if browser automation is needed.
   - Use a D-drive browser cache path before install.

4. Define Hermes delegation rules.
   - Decide when Hermes should act directly, when it should call Codex, when it should call Claude Code, and when it should call OpenCode.

5. Add a workspace-control Hermes skill or SOUL note so remote runs consistently follow `workspace_manifest.yaml` and `PROJECT_CONTEXT`.

## Current Primary Route

```text
QQ DM
  -> QQBot App ID 1904136105
  -> Hermes gateway
  -> Hermes agent with DeepSeek
  -> local tools / ${WORKSPACE_ROOT}
  -> QQBot response
```

## Current Weixin Route Status

```text
Weixin DM
  -> iLink bot identity 802846c3be7e@im.bot
  -> Hermes gateway connected
  -> Hermes agent with DeepSeek
  -> Weixin response
```

## Report Files

- `${WORKSPACE_ROOT}\reports\hermes\messaging_diagnosis.md`
- `${WORKSPACE_ROOT}\reports\hermes\messaging_test_report.md`
- `${WORKSPACE_ROOT}\reports\hermes\environment_recommendations.md`
- `${WORKSPACE_ROOT}\reports\hermes\workspace_integration_plan.md`
- `${WORKSPACE_ROOT}\reports\hermes\hermes_readiness_report.md`
