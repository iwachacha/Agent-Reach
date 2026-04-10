# Agent Reach Nexus Concept

This concept note describes a possible evolution of Agent Reach based on the 2026-04-10 field research. It is intentionally forward-looking. It should guide design discussion before implementation.

## One-Line Idea

Agent Reach Nexus is a no-copy capability graph and evidence pipeline for Codex and downstream automation.

It keeps Agent Reach's current discipline: collect, diagnose, normalize, and explain capabilities. It does not own ranking, summarization, scheduling, Discord publishing, or long-term application state unless a future host project explicitly asks for that layer.

## Why This Is Timely

Current agent tooling is moving toward a layered model:

- Knowledge layer: docs, RAG, live documentation, feeds, and search.
- Tool layer: MCP servers, CLIs, APIs, browser-visible resources, and connectors.
- Instruction layer: skills, prompts, AGENTS.md, policy files, and best-practice packs.
- Runtime layer: hooks, approvals, CI jobs, background agents, and agent-to-agent handoffs.
- Governance layer: registries, lockfiles, provenance, security scans, and audit trails.

Agent Reach already implements several parts of this shape for research collection:

- `channels --json`: capability registry
- `doctor --json`: readiness diagnostics
- `collect --json`: normalized collection envelope
- `export-integration --client codex --format json`: Codex-readable integration policy
- global skill install: no-copy operational guidance for Codex

Nexus extends that pattern from "available research channels" to "available agent capabilities and evidence."

## Product Pillars

### 1. Atlas

Atlas answers: "What can this environment safely use right now?"

Possible command:

```powershell
agent-reach atlas --json
```

Possible output sections:

- `channels`: current Agent Reach channels and operations
- `readiness`: merged doctor status and operation readiness
- `mcp_servers`: discovered MCP servers from known config locations or exported integrations
- `skills`: discovered Agent Reach and external skills
- `actions`: available GitHub Actions integration hints
- `policies`: no-copy rule, failure policy, large-scale research limits
- `security`: optional warnings for unknown tools, unpinned Actions, missing auth, or high-volatility channels

Design rule:

- Atlas reports capabilities. It should not install tools, edit downstream repos, or make network-heavy calls unless explicitly requested.

Minimum viable version:

- Reuse `export-integration` and `doctor` internally.
- Emit the current Agent Reach runtime policy plus installed skill locations.
- Add enough schema to make future MCP/skill registry discovery easy.

### 2. Scout

Scout answers: "How should I research this topic without wasting tokens or losing provenance?"

Possible commands:

```powershell
agent-reach scout --topic "AI agent tooling" --plan-only --json
agent-reach scout --topic "AI agent tooling" --limit 10 --save .agent-reach/evidence.jsonl --json
```

Possible behavior:

- Generate a bounded plan with 2-4 discovery queries.
- Run selected `exa_search`, `github`, `qiita`, `bluesky`, `rss`, and optional `twitter` searches.
- Dedupe URLs and item IDs.
- Propose selected `web read` follow-ups.
- Save every raw `CollectionResult` envelope to an evidence ledger.
- Return partial results with channel failures instead of blocking on optional tools.

Design rule:

- Scout is a research runner, not a summarizer. Downstream projects decide ranking and narrative.

Minimum viable version:

- Start with `--plan-only`.
- Then add `--execute-searches`.
- Add deep reads only after ledger and dedupe are stable.

### 3. Evidence Ledger

Evidence Ledger answers: "What did the agent actually see?"

Possible file:

```text
.agent-reach/evidence.jsonl
```

Possible record:

```json
{
  "run_id": "2026-04-10-agent-tooling",
  "record_type": "collection_result",
  "created_at": "2026-04-10T09:13:38Z",
  "channel": "exa_search",
  "operation": "search",
  "input": "AI agent tooling",
  "ok": true,
  "count": 8,
  "item_ids": ["..."],
  "urls": ["..."],
  "result": {}
}
```

Design rule:

- Preserve raw normalized envelopes. Any ranking, summarization, or Discord formatting should be a downstream transform.

Minimum viable version:

- Add `--save` to `collect`.
- Save JSON Lines.
- Include tests for append and error cases.

### 4. Candidate Planner

Candidate Planner answers: "Which collected URLs should be read next?"

Possible command:

```powershell
agent-reach plan candidates --input .agent-reach/evidence.jsonl --limit 20 --json
```

Possible behavior:

- Dedupe by canonical URL and normalized item ID.
- Group sightings across channels.
- Prefer official docs and repository reads when the source is recognizable.
- Emit candidate URLs and reasons.

Design rule:

- Planner can provide reasons and hints, but it should avoid pretending to be an authority scorer until stronger source-quality signals exist.

### 5. Governance Gateway

Governance Gateway answers: "Should the agent do this tool action now?"

Inspired by hook-based control surfaces, this layer would expose a policy decision helper rather than hard-coding one agent runtime.

Possible command:

```powershell
agent-reach guard --event pre-collect --channel twitter --operation search --json
```

Possible decisions:

- `allow`: operation is ready and within bounded limits
- `warn`: optional channel or unprobed live operation
- `deny`: destructive or unsupported action
- `ask`: user confirmation recommended

Design rule:

- Keep this runtime-neutral. Codex, Claude Code, CI scripts, and local wrappers can all call the same policy helper.

## Target Downstream Workflows

### Discord News Bot

The bot keeps:

- schedule
- topics
- source configuration
- dedupe database
- ranking and summarization
- Discord message formatting
- delivery state

Agent Reach provides:

- readiness checks
- collection across channels
- raw evidence artifacts
- source hints
- partial failure reporting

### Codex Vibe Coding

Codex starts by reading:

```powershell
agent-reach atlas --json
agent-reach scout --topic "<task topic>" --plan-only --json
```

Then Codex uses only the relevant channels, preserves evidence, and avoids copying Agent Reach files into the working repo.

### CI Research Jobs

GitHub Actions installs Agent Reach through the composite action, runs bounded Scout jobs, uploads `.agent-reach/evidence.jsonl`, and passes normalized items to the downstream summarizer.

## Implementation Roadmap

### Phase 1: Ledger

- Add `--save` to `collect`.
- Create `agent_reach/ledger.py`.
- Add tests for JSONL append, invalid paths, and error result persistence.
- Update `docs/downstream-usage.md`.

### Phase 2: Atlas

- Create `agent-reach atlas --json`.
- Reuse `doctor`, `channels`, and `export-integration`.
- Include installed skill status and no-copy policy.
- Add tests for tool-install and checkout execution contexts.

### Phase 3: Scout Plan

- Create `agent-reach scout --topic ... --plan-only --json`.
- Emit query plan, channel plan, readiness requirements, and recommended limits.
- Add docs and examples.

### Phase 4: Candidate Planner

- Add `agent-reach plan candidates`.
- Dedupe ledger records.
- Emit selected deep-read candidates.

### Phase 5: Guard

- Add `agent-reach guard`.
- Start with Twitter readiness and large fan-out limits.
- Later add pluggable project policies if a downstream project needs them.

## Non-Goals

- Do not make Agent Reach a summarizer by default.
- Do not make Agent Reach a Discord bot.
- Do not require downstream repositories to vendor Agent Reach files.
- Do not make Twitter/X a required dependency.
- Do not require a vector database for the first version.
- Do not auto-install unknown tools during research runs.

## Design Risks

- Too much orchestration could blur Agent Reach's narrow role. Keep collection and evidence first.
- A planner can become misleading if it looks like a ranking model. Keep source hints transparent.
- Registry discovery can become platform-specific. Start with current Codex integration exports and local known paths.
- Twitter/X reliability can change quickly. Always gate live search with operation-level probe results.
- Evidence ledgers can grow large. Use JSONL and downstream artifact retention policies instead of in-memory accumulation.

## Success Criteria

Agent Reach Nexus is successful if a fresh Codex session can:

1. Run one command to discover usable capabilities.
2. Run one command to create a safe research plan.
3. Run bounded collection without copying Agent Reach files into the downstream repo.
4. Save raw evidence for later inspection.
5. Hand normalized items to a bot, CI job, or summarizer without bespoke scraping.

The key product feeling should be: "Codex knows what it can safely reach, why it chose those sources, and what evidence it collected."
