# Hermes Messaging Diagnosis

Generated: 2026-06-08

Scope: `${DATA_ROOT}/hermes`, `${DATA_ROOT}/hermes\hermes-agent`, `${WORKSPACE_ROOT}`.

Sensitive values are intentionally redacted. Conclusions below are based on inspected files, CLI output, and logs.

## Post-Action Update

The original Weixin account `d6f2c80c47d9@im.bot` was stale/expired. A fresh iLink QR login produced a new bot identity:

- New Weixin iLink bot: `802846c3be7e@im.bot`
- User/home channel: `o9cq802tRNlrlhd5cfv-0DxgZmEQ@im.wechat`

After updating `.env` and restarting the gateway, Weixin DM was proven working with a `hello` message and a Hermes reply.

## Evidence Sources

- `${DATA_ROOT}/hermes\.env`
- `${DATA_ROOT}/hermes\config.yaml`
- `${DATA_ROOT}/hermes\gateway_state.json`
- `${DATA_ROOT}/hermes\channel_directory.json`
- `${DATA_ROOT}/hermes\sessions\sessions.json`
- `${DATA_ROOT}/hermes\logs\agent.log`
- `${DATA_ROOT}/hermes\logs\gateway.log`
- `${DATA_ROOT}/hermes\logs\errors.log`
- `${DATA_ROOT}/hermes\weixin\accounts\d6f2c80c47d9@im.bot.json`
- Hermes docs under `${DATA_ROOT}/hermes\hermes-agent\website\i18n\zh-Hans\docusaurus-plugin-content-docs\current\user-guide\messaging\`

## Weixin Access Scheme

Weixin uses Hermes' personal Weixin adapter through Tencent iLink Bot API.

Observed configuration before rebind:

- `WEIXIN_ACCOUNT_ID`: configured as an `@im.bot` identity.
- `WEIXIN_TOKEN`: present; redacted.
- `WEIXIN_BASE_URL`: `https://ilinkai.weixin.qq.com`
- `WEIXIN_CDN_BASE_URL`: `https://novac2c.cdn.weixin.qq.com/c2c`
- `WEIXIN_DM_POLICY`: `pairing`
- `WEIXIN_ALLOW_ALL_USERS`: `false`
- `WEIXIN_ALLOWED_USERS`: empty
- `WEIXIN_GROUP_POLICY`: `disabled`
- `WEIXIN_HOME_CHANNEL`: `o9cq802tRNlrlhd5cfv-0DxgZmEQ@im.wechat`

Hermes docs state this adapter connects an iLink bot identity, not a fully scriptable normal personal WeChat account. Reliable operation is expected mainly through DM to the iLink bot identity; ordinary WeChat group events often are not delivered by iLink.

The account file contains:

- `base_url`: `https://ilinkai.weixin.qq.com`
- `user_id`: `o9cq802tRNlrlhd5cfv-0DxgZmEQ@im.wechat`

Interpretation before rebind:

- Bot identity: `d6f2c80c47d9@im.bot`
- Home/user channel: `o9cq802tRNlrlhd5cfv-0DxgZmEQ@im.wechat`
- Current DM access mode requires pairing approval for unknown users.
- No pairing data exists yet according to `hermes pairing list`.

## QQ Access Scheme

QQ uses Hermes' QQBot adapter through the official QQ Bot API v2.

Observed configuration:

- `QQ_APP_ID`: `1904136105`
- `QQ_CLIENT_SECRET`: present; redacted.
- `QQ_ALLOW_ALL_USERS`: `false`
- `QQ_ALLOWED_USERS`: `F2113C342AE5C4EB557749876F1D0A94`
- `QQBOT_HOME_CHANNEL`: `F2113C342AE5C4EB557749876F1D0A94`

Observed channel directory:

- Platform: `qqbot`
- Chat ID: `F2113C342AE5C4EB557749876F1D0A94`
- Type: `dm`

Interpretation:

- QQBot is restricted to one approved DM user.
- The approved user and home channel are the same OpenID: `F2113C342AE5C4EB557749876F1D0A94`.
- QQBot can act as Hermes' current remote-control channel.

## Message Entry Points

QQ:

- Entry point is C2C/DM message to QQBot App ID `1904136105` from OpenID `F2113C342AE5C4EB557749876F1D0A94`.
- Hermes stores this session as `agent:main:qqbot:dm:F2113C342AE5C4EB557749876F1D0A94`.

Weixin:

- Intended entry point is DM to the iLink bot identity configured by `WEIXIN_ACCOUNT_ID`.
- The configured home/user channel is `o9cq802tRNlrlhd5cfv-0DxgZmEQ@im.wechat`.
- Current evidence does not show a successful Weixin inbound message.
- Since `WEIXIN_DM_POLICY=pairing` and no pairing data exists, a new Weixin sender should receive a pairing code first, then needs approval with `hermes pairing approve weixin <code>`.

## Current Message Route Structure

QQ route confirmed by logs:

```text
QQ C2C DM
  -> QQBot WebSocket adapter
  -> gateway.run inbound message
  -> Hermes agent session 20260608_183454_1fa24fdb
  -> DeepSeek provider / deepseek-v4-flash
  -> QQBot REST response
  -> QQ C2C DM
```

Weixin intended route:

```text
Weixin DM to iLink bot identity
  -> iLink long-polling getupdates
  -> gateway.platforms.weixin
  -> Hermes agent session
  -> DeepSeek provider / deepseek-v4-flash
  -> iLink sendmessage
  -> Weixin DM
```

Weixin route has not been proven end to end by logs.

Weixin route after rebind has been proven:

```text
Weixin DM "hello"
  -> iLink bot identity 802846c3be7e@im.bot
  -> gateway.platforms.weixin inbound
  -> Hermes agent session 20260608_192248_d68993e9
  -> DeepSeek provider / deepseek-v4-flash
  -> Weixin response sent
```

## Gateway Status

`gateway_state.json` reports:

- Gateway: `running`
- PID: `30712`
- `weixin`: `connected`
- `qqbot`: `connected`
- `email`: `retrying`, error `failed to reconnect`

This confirms adapter connectivity, but not necessarily that Weixin inbound/outbound user messaging is currently reliable.

## Key Findings

1. QQBot is genuinely configured, connected, and has real historical inbound and outbound traffic.
2. Weixin is now configured and connected to a fresh iLink bot identity, and a successful Weixin inbound/outbound DM was found after rebind.
3. Weixin Home Channel is set to a Weixin user/channel ID ending in `@im.wechat`, while the bot account itself is an `@im.bot` identity.
4. `hermes send --list` currently lists QQBot only; it does not list Weixin in the local target directory.
5. Weixin is in pairing mode, but the bound user DM succeeded after fresh QR login. `hermes pairing list` still shows no pending or approved pairing data.
