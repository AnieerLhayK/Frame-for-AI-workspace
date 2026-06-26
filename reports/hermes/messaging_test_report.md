# Hermes Messaging Test Report

Generated: 2026-06-08

Post-action update:

- Weixin was rebound to a new iLink bot identity: `802846c3be7e@im.bot`.
- Gateway was restarted and connected with account prefix `802846c3`.
- A user DM `hello` reached Hermes and received a Weixin response.

## Test Summary

| Channel | Direction | Result | Evidence |
|---|---|---|---|
| QQBot | QQ -> Hermes | Pass, based on real historical inbound logs | `agent.log` lines around 18:35-18:52 |
| QQBot | Hermes -> QQ | Pass, actively tested | `hermes send --to qqbot:F2113C342AE5C4EB557749876F1D0A94 --json ...` |
| Weixin | Weixin -> Hermes | Pass after rebind | `gateway.log` and `agent.log` around 19:22 |
| Weixin | Hermes -> Weixin | Pass after rebind | `response ready: platform=weixin` and `[Weixin] Sending response` |

## Active Tests Executed

### QQBot Outbound Probe

Command:

```powershell
hermes send --to qqbot:F2113C342AE5C4EB557749876F1D0A94 --json "[Hermes diagnostic] QQ outbound probe from Codex at 2026-06-08. No action required."
```

Result:

```json
{
  "success": true,
  "platform": "qqbot",
  "chat_id": "F2113C342AE5C4EB557749876F1D0A94",
  "message_id": "ROBOT1.0_...",
  "note": "Sent to qqbot home channel (chat_id: F2113C342AE5C4EB557749876F1D0A94)",
  "mirrored": true
}
```

Conclusion: Hermes can send to the configured QQBot DM target.

### Weixin Outbound Probe

Command:

```powershell
hermes send --to weixin --json "[Hermes diagnostic] Weixin outbound probe from Codex at 2026-06-08. No action required."
```

Result:

```json
{
  "error": "Weixin send failed: iLink sendmessage rate limited: ret=-2 errcode=None errmsg=rate limited"
}
```

Relevant log lines:

- `agent.log`: `[Weixin] rate limited for o9cq802t; backing off 3.0s before retry`
- `agent.log`: `[Weixin] send failed to=o9cq802t: iLink sendmessage rate limited: ret=-2 errcode=None errmsg=rate limited`
- `errors.log`: same rate-limit warnings and final error.

Conclusion before rebind: Weixin adapter reached iLink send path but iLink refused delivery due to rate limiting.

### Weixin Rebind And Inbound Probe

Action:

- Generated a fresh iLink QR code.
- User scanned and confirmed it from WeChat.
- New iLink bot account returned: `802846c3be7e@im.bot`.
- New credentials were written to `${DATA_ROOT}/hermes\.env` and `${DATA_ROOT}/hermes\weixin\accounts\802846c3be7e@im.bot.json`.
- Gateway was restarted.

Sensitive raw QR/login status was moved out of the Git workspace to:

```text
D:\Backup\migration\hermes-weixin-rebind\
```

Observed evidence:

- `gateway.log`: `[Weixin] Connected account=802846c3 base=https://ilinkai.weixin.qq.com`
- `gateway.log`: `inbound message: platform=weixin ... msg='hello'`
- `agent.log`: `conversation turn ... provider=deepseek platform=weixin ... msg='hello'`
- `gateway.log`: `response ready: platform=weixin ... time=6.0s api_calls=1 response=35 chars`
- `gateway.log`: `[Weixin] Sending response (35 chars) to o9cq802tRNlrlhd5cfv-0DxgZmEQ@im.wechat`

Conclusion after rebind: Weixin -> Hermes -> DeepSeek -> Weixin is proven working.

## Passive Verification From Logs

QQBot inbound examples:

- 2026-06-08 18:35:10: `conversation turn ... platform=qqbot ... msg='你可以讲话吗？'`
- 2026-06-08 18:37:11: `[QQBot:1904136105] C2C message ...`
- 2026-06-08 18:37:11: `inbound message: platform=qqbot user=F2113C342AE5C4EB557749876F1D0A94 ...`
- 2026-06-08 18:43:38: inbound QQ message asking for D drive status.
- 2026-06-08 18:44:00: inbound QQ message asking for C drive status.
- 2026-06-08 18:52:03: response ready and sent to QQBot.

This proves that QQ -> Hermes -> Agent -> QQ worked before this report.

Weixin evidence before rebind:

- 2026-06-08 18:31:46: `[Weixin] Connected account=d6f2c80c base=https://ilinkai.weixin.qq.com`
- No successful `platform=weixin` inbound message found in inspected logs.
- Active outbound probe failed due to iLink rate limiting.

Weixin evidence after rebind:

- 2026-06-08 19:22:44: `[Weixin] Connected account=802846c3 base=https://ilinkai.weixin.qq.com`
- 2026-06-08 19:22:48: inbound Weixin DM `hello`.
- 2026-06-08 19:22:54: Weixin response ready and sent.

## Logs Checked

- `${DATA_ROOT}/hermes\logs\agent.log`
- `${DATA_ROOT}/hermes\logs\gateway.log`
- `${DATA_ROOT}/hermes\logs\errors.log`

## Minimal Manual Inbound Test Status

QQ:

1. Send a short DM to the QQBot from the approved QQ account: `Hermes QQ inbound test 2026-06-08`.
2. Watch `${DATA_ROOT}/hermes\logs\agent.log` for `platform=qqbot`.
3. Expected result: a new `inbound message` log and a response sent to the same OpenID.

Weixin:

- Completed after rebind.
- User sent `hello` to the new ClawBot / iLink bot.
- Hermes logged the inbound DM and sent a response.

Current blocker: none for Weixin DM. Ordinary WeChat group delivery remains unproven and is likely constrained by iLink bot limitations.
