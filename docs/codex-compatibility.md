# Codex Compatibility

Agent Reach currently optimizes for Windows-based Codex setups.

| Surface | Status | Notes |
| --- | --- | --- |
| Native Windows PowerShell | Supported | Primary target |
| Codex skill install | Supported | Uses `CODEX_HOME/skills` or `~/.codex/skills` |
| Codex plugin manifest | Supported | Repo-local in checkouts, inline export in tool installs |
| MCP wiring for Exa | Supported | Repo-local in checkouts, inline export in tool installs |
| Python SDK | Supported | `AgentReachClient` works after install into the caller project environment |
| Read-only collect CLI | Supported | `agent-reach collect --json` |
| Core-based doctor exit policy | Supported | `doctor --json` exits on core readiness by default, reports optional gaps under `summary.advisory_not_ready`, and surfaces partial probe coverage under `summary.probe_attention`; use `--exit-policy all` for strict mode |
| Evidence ledger validation | Supported | `ledger validate --json` checks saved JSONL artifacts, and `ledger append --json` can add a captured CollectionResult later |
| macOS/Linux installer automation | Not first-class | Use `install --safe` for guidance only |
| Full workflow orchestration | Deferred | Scheduling, ranking, summarization, and publishing stay downstream, and large-scale research remains explicit caller opt-in |
| Expanded optional channel surface | Supported | `searxng`, `crawl4ai`, `hacker_news`, `mcp_registry`, `reddit`, and optional `twitter` are exposed through the channel registry; readiness still depends on runtime config or optional backends |
