# Field Research Improvements - 2026-04-10

This note captures the follow-up work suggested by the 2026-04-10 live Agent Reach research run. Use it as the handoff document for a future Codex session.

## Research Scope

The research run used the globally installed Agent Reach CLI from an Agent Reach checkout and followed the bounded fan-out rule.

- Approximate Agent Reach commands: 37
- Channels used: `exa_search`, `github`, `web`, `bluesky`, `qiita`, `rss`, `twitter`
- Readiness commands: `agent-reach channels --json`, `agent-reach doctor --json`, `agent-reach doctor --json --probe`, `agent-reach export-integration --client codex --format json`
- Approximate normalized items collected: 149
- Approximate deep reads or repo reads: 13
- Primary-source anchors: OpenAI Codex Skills and Codex cookbook, Google Gemini API Docs MCP and Agent Skills, Model Context Protocol registry, A2A protocol docs, Claude Code hooks docs, GitHub repositories
- Social and community signal anchors: Bluesky, Twitter/X after `doctor --json --probe`, Qiita

Treat the counts as a practical scale marker, not a formal benchmark. The run was broad enough for ideation, but not a replacement for product-specific validation.

## What The Research Showed

The strongest external trend is that agent tooling is converging around composable capability surfaces:

- `MCP` standardizes tool and data access.
- `Skills` package operating instructions, examples, and progressive disclosure.
- `Registries` help discover and govern agents, tools, skills, and MCP servers.
- `Hooks` provide lifecycle control before and after tool use.
- `A2A` targets agent-to-agent communication and handoff.

Agent Reach already sits in the right shape for this trend: it has a stable CLI, machine-readable channel registry, doctor diagnostics, normalized result envelopes, no-copy downstream usage, and Codex runtime policy metadata.

## Observed Pain Points

- Twitter/X must remain optional. `doctor --json` without probe can only report a warning or unknown operation status; `doctor --json --probe` is required before depending on search.
- Social search has noise and occasional odd timestamps. Use it as trend detection, not as authoritative evidence.
- Web reads can include navigation-heavy text. Prefer official docs and repo reads as anchors when a claim matters.
- GitHub and Exa search queries can return sparse or noisy results. Use 2-4 query variants and dedupe downstream.
- Stars, likes, reposts, and bookmarks are useful ranking signals but not quality signals by themselves.
- Current Agent Reach produces collection envelopes, but it does not yet persist a first-class evidence ledger across multiple commands.

## Improvements To Prioritize

### P0: Evidence Ledger

Add a small evidence ledger format and optional writer for research runs.

Recommended surface:

```powershell
agent-reach collect --channel exa_search --operation search --input "AI agent tooling" --limit 10 --json --save .agent-reach/evidence.jsonl
```

Alternative if avoiding changes to `collect`:

```powershell
agent-reach ledger append --from result.json --run-id 2026-04-10-agent-tooling
```

Acceptance criteria:

- Stores raw `CollectionResult` JSON as JSON Lines.
- Captures `run_id`, timestamp, channel, operation, input, ok/error, count, item IDs, and URLs.
- Does not summarize or rank by itself.
- Works in arbitrary downstream projects without copying Agent Reach files.
- Has tests for success, error envelopes, and append behavior.

### P1: Dedupe And Candidate Planning

Add a lightweight helper that reads multiple `CollectionResult` envelopes and returns a deduped candidate list.

Recommended surface:

```powershell
agent-reach plan candidates --input .agent-reach/evidence.jsonl --by url --json
```

Acceptance criteria:

- Dedupe by URL first, then by normalized `id`.
- Preserve all contributing sources in `extras.seen_in`.
- Return a bounded list suitable for selected `web read` follow-up.
- Do not require embeddings, vector databases, or a model call for the first version.

### P1: Research Run Manifest

Add a manifest that tells Codex how to run large research safely.

Recommended surface:

```powershell
agent-reach scout --topic "AI agent tooling" --plan-only --json
```

Acceptance criteria:

- Emits a plan with 2-4 broad search queries, optional specialist channel queries, recommended limits, and strict no-copy reminders.
- Includes `required_readiness` and says when `doctor --json --probe` is required.
- Does not execute network collection in `--plan-only`.

### P2: Source Quality Flags

Add source-level metadata that downstream projects can use for ranking without Agent Reach owning ranking.

Candidate flags:

- `source_kind`: `official_docs`, `repository`, `social_post`, `blog`, `news`, `feed_item`, `unknown`
- `authority_hint`: `official`, `project_owner`, `community`, `social`, `unknown`
- `freshness_hint`: generated from `published_at` when available
- `volatility_hint`: `high` for social and rapidly changing APIs, `medium` for blogs and repos, `low` for stable docs

Acceptance criteria:

- Hints live in `meta` or `extras`; they do not change the stable top-level schema.
- Existing consumers still work.
- Tests cover at least `github`, `web`, `rss`, and one social channel.

### P2: Better Web Read Hygiene

Improve handling of navigation-heavy pages.

Options:

- Add `meta.text_length`, `meta.link_count`, and `meta.extraction_warning`.
- Add a `--max-text-chars` display option for CLI text mode.
- Keep JSON full-fidelity by default.

Acceptance criteria:

- No destructive truncation of JSON `raw`.
- The warning is diagnostic only.
- Tests cover a synthetic navigation-heavy payload if practical.

### P3: Downstream CI Examples

Add runnable examples for bots and scheduled digests.

Recommended examples:

- `.github/workflows/agent-reach-smoke.yml`
- `examples/discord_news_collect.ps1`
- `examples/research-ledger.ps1`

Acceptance criteria:

- Examples install Agent Reach via the composite action or global CLI.
- Examples never copy `.codex-plugin`, `.mcp.json`, or Agent Reach source files into the downstream project.
- Examples persist raw JSON as artifacts.

## Next Session Checklist

Start here:

```powershell
git status --short --branch
agent-reach version
agent-reach doctor --json
agent-reach export-integration --client codex --format json
```

Then pick one implementation target:

- If the user wants the smallest useful change, implement `Evidence Ledger`.
- If the user wants the most strategic change, implement `scout --plan-only`.
- If the user wants downstream bot usability, implement `examples/discord_news_collect.ps1` and CI docs.

Before editing code, inspect:

- `agent_reach/results.py`
- `agent_reach/client.py`
- `agent_reach/cli.py`
- `agent_reach/integrations/codex.py`
- `tests/test_cli.py`
- `tests/test_integration_artifacts.py`

Verification commands:

```powershell
$env:PYTHONPATH='C:\research'; uv run --with pytest python -m pytest
uv lock --check
git diff --check
$env:PYTHONPATH='C:\research'; python -m compileall agent_reach tests
```

## Evidence Links

- OpenAI Codex Skills: https://developers.openai.com/codex/skills/create-skill
- OpenAI Codex + Agents SDK cookbook: https://developers.openai.com/cookbook/examples/codex/codex_mcp_agents_sdk/building_consistent_workflows_codex_cli_agents_sdk
- Google Gemini API Docs MCP and Agent Skills: https://blog.google/innovation-and-ai/technology/developers-tools/gemini-api-docsmcp-agent-skills/
- Model Context Protocol registry: https://modelcontextprotocol.io/registry/about
- A2A protocol: https://a2a-protocol.org/dev
- Claude Code hooks: https://code.claude.com/docs/en/hooks
- MCP registry repo: https://github.com/modelcontextprotocol/registry
- Activepieces repo: https://github.com/activepieces/activepieces
- Secpipe repo: https://github.com/FuzzingLabs/secpipe
- AGENTS.lock repo: https://github.com/luml-ai/AGENTS.lock
