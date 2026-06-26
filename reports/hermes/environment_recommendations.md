# Hermes Environment Recommendations

Generated: 2026-06-08

Basis: `hermes doctor`, `hermes status`, `hermes tools list`, inspected config and logs.

## Must Install / Configure

### None for current QQ remote-control MVP

Current QQ remote-control path already has:

- Gateway running.
- QQBot configured and connected.
- DeepSeek configured and reachable.
- Core tools enabled or available: `terminal`, `file`, `code_execution`, `memory`, `messaging`, `skills`, `todo`, `cronjob`, `delegation`, `tts`.

For the immediate goal "QQ/Weixin -> Hermes -> Workspace -> Agent execution -> reply", no missing component is strictly required for QQ.

## Recommended

### Playwright Chromium

Status:

- `hermes doctor`: `Playwright Chromium not installed`
- Impact: `browser` and `browser-cdp` are hidden/unavailable because the system dependency is not met.

Recommendation:

- Install only when browser automation is part of the expected long-running workflow.
- Use the Hermes source directory:

```powershell
cd ${DATA_ROOT}/hermes\hermes-agent
npx playwright install chromium
```

Storage note:

- Before installing, check Playwright cache location and redirect to D drive if needed, e.g. `PLAYWRIGHT_BROWSERS_PATH=${DATA_ROOT}/hermes\playwright-browsers` or another agreed D-drive cache path.

### Web Search Provider

Status:

- `web` unavailable due missing `EXA_API_KEY`, `PARALLEL_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `FIRECRAWL_API_URL`, `FIRECRAWL_GATEWAY_URL`, `TOOL_GATEWAY_DOMAIN`, `TOOL_GATEWAY_SCHEME`, `TOOL_GATEWAY_USER_TOKEN`.

Recommendation:

- Configure one search provider only if Hermes needs autonomous internet research.
- Prefer a single, cheap, explicit provider rather than adding several keys.

### GitHub Token

Status:

- `hermes doctor`: no `GITHUB_TOKEN`; GitHub API limited to 60 requests/hour.

Recommendation:

- Add a minimally scoped GitHub token if Hermes will inspect GitHub repos, issues, PRs, or install skills from GitHub frequently.
- Not required for local workspace execution.

### Weixin Pairing / Access Fix

Status:

- Weixin is connected but no inbound message proof exists.
- `WEIXIN_DM_POLICY=pairing`.
- `hermes pairing list`: no pairing data.
- Weixin outbound probe hit iLink rate limiting.

Recommendation:

- Perform a manual DM pairing test before relying on Weixin.
- Do not enable `WEIXIN_ALLOW_ALL_USERS=true` until the bot identity and receiving path are confirmed.

## Optional / Defer

### Vision

Status:

- Tool enabled in config, but doctor reports system dependency not met.

Recommendation:

- Defer unless Hermes must inspect screenshots/images sent from QQ/Weixin or local files.
- Configure only after deciding which model/provider should handle image input.

### Image Generation

Status:

- Tool enabled in config, but doctor reports system dependency not met.
- No image provider key is configured.

Recommendation:

- Defer. It is not part of remote command execution or workspace automation.

### Browserbase / Advanced Browser Tools

Status:

- `agent-browser` exists.
- Browserbase key is not configured.

Recommendation:

- Defer unless cloud browser sessions or stealth browsing are explicitly needed.
- Local Playwright Chromium is the more practical first step.

### Computer Use

Status:

- Listed but system dependency not met; Hermes doctor notes Computer Use backend is macOS-oriented.

Recommendation:

- Ignore on this Windows machine for now.

### Video Generation / Video Analysis

Status:

- Unavailable or disabled.

Recommendation:

- Ignore for the current Agent-ops workflow.

### Email

Status:

- Email is configured but repeatedly fails IMAP authentication.

Recommendation:

- Ignore unless email becomes part of the control plane.
- If needed later, fix Outlook app password/OAuth separately.

## Priority Order

1. Prove Weixin inbound DM or mark Weixin as non-primary.
2. Fix Playwright Chromium with D-drive browser cache if browser automation is needed.
3. Add GitHub token if GitHub work becomes frequent.
4. Add one web search provider if autonomous research is required.
5. Configure vision/image only after a concrete use case exists.

