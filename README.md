# Agent Reach

Windows-first research integration tooling with a stable JSON CLI and an optional Python SDK for downstream projects.

Agent Reach is intentionally narrow. It is designed to help other tools collect information safely and predictably, not to own scheduling, ranking, summarization, or posting. In practice this fork does four jobs:

- bootstrap the Windows-friendly toolchain needed for research workflows
- expose a stable registry of supported channels
- provide readiness diagnostics and integration exports
- offer a thin read-only collection surface for external apps, bots, and CI jobs

## Supported channels

- `web` via Jina Reader
- `exa_search` via Exa MCP and `mcporter`
- `github` via `gh`
- `hatena_bookmark` via Hatena Bookmark public APIs
- `bluesky` via the Bluesky AppView API
- `qiita` via Qiita API v2
- `youtube` via `yt-dlp`
- `rss` via `feedparser`
- optional `twitter` via `twitter-cli`

## Install

```powershell
uv tool install .
agent-reach install --env=auto
```

This install path guarantees the `agent-reach` CLI. It does not make `import agent_reach` available to arbitrary Python environments.

After pulling updates from a source checkout, refresh the installed CLI with:

```powershell
uv tool install --force .
agent-reach version
```

After pushing a specific remote ref and wanting that exact build globally, refresh with:

```powershell
uv tool install --force git+<remote-url>@<ref>
agent-reach skill --install
agent-reach version
```

Preview the Windows commands without changing anything:

```powershell
agent-reach install --env=auto --safe
agent-reach install --env=auto --dry-run --json
```

Optional Twitter/X support:

```powershell
agent-reach install --env=auto --channels=twitter
agent-reach configure twitter-cookies "auth_token=...; ct0=..."
agent-reach doctor --json --probe
```

Treat `twitter status` as an authentication check, not proof that live search works. `agent-reach doctor --json --probe` now validates both a live user lookup and a live search before calling Twitter/X ready.

## Public surfaces

CLI JSON:

```powershell
agent-reach collect --channel github --operation read --input "openai/openai-python" --json
agent-reach collect --channel exa_search --operation search --input "latest gpt-5.4 release notes" --limit 3 --json
agent-reach collect --channel bluesky --operation search --input "OpenAI" --limit 3 --json
agent-reach collect --channel hatena_bookmark --operation read --input "https://example.com" --limit 5 --json
agent-reach collect --channel qiita --operation search --input "python user:Qiita" --limit 3 --json
agent-reach collect --channel twitter --operation user_posts --input "openai" --limit 10 --json
```

Persist raw evidence for larger runs:

```powershell
agent-reach collect --channel exa_search --operation search --input "AI agent tooling" --limit 10 --json --save .agent-reach/evidence.jsonl --run-id 2026-04-10-agent-tooling
agent-reach plan candidates --input .agent-reach/evidence.jsonl --by url --limit 20 --json
```

Collection output may include diagnostic-only `extras.source_hints` on supported sources and `meta.text_length`, `meta.link_count`, and `meta.extraction_warning` for `web read`. These fields are conservative hints, not ranking, scoring, summarization, or publishing policy. `collect --max-text-chars N` only changes human text-mode snippets; JSON output and saved evidence stay full fidelity.

Python SDK, when Agent Reach is installed into the caller Python environment:

```powershell
uv pip install -e .
```

```python
from agent_reach import AgentReachClient

client = AgentReachClient()
result = client.github.read("openai/openai-python")
print(result["items"][0]["title"])
print(client.qiita.search("python user:Qiita", limit=3)["items"][0]["url"])
```

Discovery and diagnostics:

```powershell
agent-reach channels --json
agent-reach doctor --json
agent-reach doctor --json --probe
agent-reach export-integration --client codex --format json
agent-reach check-update --json
```

These are the supported machine-readable entry points for external projects. They are designed so bots, GitHub Actions, and other codebases do not need to scrape README text or SKILL.md.

## Typical downstream use

- GitHub Actions and other arbitrary projects call `agent-reach collect --json`
- Python apps and Discord bots call `AgentReachClient` after adding Agent Reach to the host Python environment
- setup tooling calls `agent-reach channels --json`, `doctor --json`, and `export-integration`

External projects do not need to vendor this repo. For GitHub Actions, use `iwachacha/Agent-Reach/.github/actions/setup-agent-reach@main`; for local Codex, install the CLI and global skill once with `uv tool install --force git+https://github.com/iwachacha/Agent-Reach.git` and `agent-reach skill --install`.

For larger research runs, use bounded fan-out: start with a few small `exa_search` queries, save raw `CollectionResult` envelopes with `--save .agent-reach/evidence.jsonl`, use `agent-reach plan candidates` for no-model URL or ID dedupe, then deep-read only selected URLs with `web`. Keep ranking, summarization, scheduling, Discord publishing, and state in the downstream project; Agent Reach should remain the collection layer.

Agent Reach normalizes results into `items`, keeps the backend-native payload in `raw`, and never prompts interactively during collection.

Reusable examples live under `examples/` and `.github/workflows/agent-reach-smoke.yml`. They collect raw JSON/JSONL and candidate artifacts for downstream automation; they do not own Discord posting, ranking, scheduling, or project state.

## Caller-Control Policy

- Agent Reach does not choose investigation scope, routes, source mix, ranking, summarization, or posting.
- The caller chooses scope. Keep lightweight asks lightweight instead of trying to auto-escalate them into large-scale research.
- `agent-reach collect --json` is the default thin interface for downstream collection.
- `batch` and `scout` are explicit opt-in helpers. They are not the default route for everyday collection.
- `agent-reach plan candidates` keeps its default `--limit 20`; raise it only when the caller explicitly wants a wider candidate review set.
- Large-scale research is explicit opt-in. When a saved batch plan is involved, run `agent-reach batch --plan PLAN.json --validate-only --json` before the write-producing batch execution.

## Guides

- Install guide: [docs/install.md](docs/install.md)
- Downstream usage: [docs/downstream-usage.md](docs/downstream-usage.md)
- Python SDK: [docs/python-sdk.md](docs/python-sdk.md)
- Codex integration: [docs/codex-integration.md](docs/codex-integration.md)
- Codex compatibility: [docs/codex-compatibility.md](docs/codex-compatibility.md)
- Field research improvements: [docs/field-research-improvements-2026-04-10.md](docs/field-research-improvements-2026-04-10.md)
- 大規模調査進化リサーチ: [docs/agent-reach-scale-evolution-research-2026-04-10.md](docs/agent-reach-scale-evolution-research-2026-04-10.md)
- Agent Reach Nexus concept: [docs/agent-reach-nexus-concept.md](docs/agent-reach-nexus-concept.md)
- Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md)

## What `install` does on Windows

- installs `gh` with `winget`
- installs `yt-dlp` with `winget`
- uses the existing `node`/`npm` install, or installs Node.js LTS with `winget`
- installs `mcporter` with `npm install -g mcporter`
- registers Exa in the user config with `mcporter --config "$HOME\\.mcporter\\mcporter.json" config add exa https://mcp.exa.ai/mcp`
- writes the `yt-dlp` JS runtime config for Node.js
- installs the bundled skill into `CODEX_HOME/skills`, `~/.codex/skills`, or `~/.agents/skills`

## Integration artifacts

This repo ships integration-oriented artifacts directly:

- `.codex-plugin/plugin.json`
- `.mcp.json`
- `agent_reach/skill/`

These artifacts exist to make downstream composition easier. In source checkouts they are available as repo files. In tool installs, `export-integration` falls back to inline payloads and suggested destinations instead of returning dead paths. Scheduling, message formatting, and publishing remain responsibilities of the host project.
