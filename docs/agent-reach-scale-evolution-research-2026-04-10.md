# Agent Reach 大規模調査進化リサーチ - 2026-04-10

この文書は、Agent Reach を使って実施したライブ調査の結果と、1000件超の調査にも耐えるための改善案をまとめた引き継ぎメモです。前回の英語版を日本語化し、さらに「件数だけを増やす」「固定ルートで調査する」「依頼内容と関係の薄い情報を大量に集める」リスクを明示的に補強しています。

## 実行サマリ

実行環境:

- 実行日: 2026-04-10
- Agent Reach CLI: v1.6.0
- readiness: `agent-reach doctor --json --probe` で全9チャネル ready
- 使用チャネル: `exa_search`, `github`, `qiita`, `bluesky`, `twitter`, `rss`, `web`
- ローカル証拠 ledger:
  - `.agent-reach/scale-research-2026-04-10.jsonl`
  - `.agent-reach/scale-research-2026-04-10-deep.jsonl`
  - `.agent-reach/scale-probe-2026-04-10.jsonl`
  - `.agent-reach/scale-1000-smoke-2026-04-10.jsonl`

`.agent-reach/` は gitignore 済みなので、これらの JSONL はリポジトリ成果物ではなくローカルの調査証跡です。

## 1000件スモーク結果

制御されたスモークテストでは、13コマンドで 1089 normalized items を約39秒で収集できました。チャネルエラーはありませんでした。

| ソース | 件数 |
| --- | ---: |
| GitHub | 500 |
| Qiita | 300 |
| Bluesky | 199 |
| Exa search | 50 |
| RSS | 40 |

`agent-reach plan candidates` による URL dedupe では 1089 items から 1024 unique URL candidates が得られました。ledger サイズは約21MBです。

この結果から、現在の CLI でも「1000件規模の収集と保存」は通ることが確認できました。ただし、これは「常に1000件集めるべき」という意味ではありません。Agent Reach と Codex が目指すべきなのは、調査テーマ・不確実性・重要度・時間制約に応じて、必要十分な調査規模を動的に選ぶことです。

## 品質優先の前提

このプロジェクトでは、速度よりも精度と調査品質を優先します。Agent Reach は「速く浅く大量に集める」よりも、ユーザーの依頼意図に沿って、柔軟に調査先を選び、根拠の強い情報を集める方向に進化させるべきです。

ただし、時間をかければよいという意味でもありません。長時間の探索を行う場合でも、一定間隔で relevance audit を挟み、調査テーマに合わないクエリやチャネルを止め、根拠が十分に揃ったら deep read と整理に移るべきです。理想は「時間制限で早く切り上げる」ではなく「証拠の質と不足を見て、必要なら深掘りし、不要なら止める」判断です。

品質優先モードで重視すること:

- ユーザーの依頼文から調査目的、対象範囲、除外すべき情報を推定する。
- 公式情報、一次情報、実装、仕様、release notes、vendor advisory を優先 anchor にする。
- ソーシャルやまとめ記事は trend signal として扱い、それだけで結論を作らない。
- 件数、スター数、いいね数、ブックマーク数を品質スコアと混同しない。
- pilot の段階でノイズが多ければ、同じルートで件数だけ増やさず、クエリや媒体を組み替える。
- deep read は少数でも高信頼な候補を優先し、必要な場合だけ広げる。
- 最終的に、調査できたこと、根拠が弱いこと、未確認のことを分けて出せるようにする。

## 全体チェック結果

前回の改善案は方向性として有効ですが、次の点は補強が必要です。

1. 1000件は既定値ではなく上限耐性として扱うべきです。
   1000件集められることは強みですが、依頼内容が狭い場合や答えが安定している場合に、件数を増やすほど品質が上がるとは限りません。Agent Reach には「大規模化できる余地」を持たせ、Codex には「必要なときだけ広げる判断」を任せる設計がよいです。

2. 固定ルート化は避けるべきです。
   `oss-watch` や `japan-tech` のような source pack は便利ですが、固定の実行ルートとして扱うと、テーマに合わない媒体を毎回回すことになります。source pack は「初期候補を作るテンプレート」に留め、最終的な調査先はトピック分類、readiness、初回探索結果、重複率、関連度によって Codex が組み替えるべきです。

3. 件数だけでは品質を保証できません。
   1000件規模の smoke run では収集能力は確認できましたが、収集結果の全件が依頼テーマに強く合致しているとは限りません。実運用では、早い段階で relevance audit を挟み、関係の薄いクエリやチャネルを止める必要があります。

4. `plan candidates --json` は大規模出力に弱いです。
   1000件規模では候補本文まで JSON に出るため、コンソール出力が巨大になります。`--summary-only` や `--fields` が必要です。

5. 高ボリューム検索では本文保存が重くなります。
   Qiita などは検索結果に本文が含まれるため、数百件でも ledger が大きくなります。`--body-mode none|snippet|full` のような制御が必要です。

6. 並列 writer の安全性は未検証です。
   現在の append-only JSONL は逐次実行では問題ありませんが、大規模な並列実行では sharded ledger か SQLite を検討すべきです。

7. 「速いが浅い」調査に寄りすぎない設計が必要です。
   大規模対応という言葉は速度や件数の最適化に寄りやすいですが、このプロジェクトでは精度を優先します。batch や pagination は調査品質を上げるための手段であり、無差別に件数を増やすための仕組みにしない方がよいです。

## Codex向けの動的調査方針

Agent Reach は収集層に留まり、調査規模と調査先の選択は Codex または下流プロジェクトが判断するのがよいです。ただし、Agent Reach 側はその判断に必要な plan 出力、診断情報、証拠保存、dedupe を提供できます。

推奨フロー:

1. 調査テーマを短く分類する。
   例: OSS探索、仕様確認、最新ニュース、学術調査、日本語コミュニティ、社会的反応、脆弱性/セキュリティ、製品比較。

2. 小さな pilot から始める。
   2から4個程度の広めの探索クエリを小さい `limit` で走らせ、件数、重複率、関連度、ノイズの多さを確認します。

3. 関連度を見て広げるか止める。
   pilot の候補が十分なら deep read に移ります。候補が薄い場合だけ、クエリを変える、チャネルを足す、言語や媒体を変える、期間をずらすなどの追加探索をします。

4. 調査規模は自動予算として扱う。
   `small`, `medium`, `large`, `xlarge` のような目安を持たせつつ、Codex がテーマごとに増減できるようにします。これは速度のための予算ではなく、品質確認のための探索幅です。

5. deep read は選抜して行う。
   検索結果を全件読むのではなく、dedupe 後に公式情報、一次情報、実装、コミュニティシグナルなどの役割を見て選びます。

6. 最後に証拠と不足を明示する。
   どのチャネルを使い、どのチャネルを使わなかったか、使わなかった理由、残る不確実性を出せるようにします。

## 調査規模の目安

これは固定値ではなく、Codex が判断するためのガードレールです。

| 規模 | 目安 | 向いているケース |
| --- | ---: | --- |
| small | 20から50件 | 明確な質問、既知の公式情報確認、短時間の比較 |
| medium | 50から150件 | OSS候補の洗い出し、複数媒体の軽い確認 |
| large | 150から500件 | 広めの市場/技術調査、媒体横断の傾向確認 |
| xlarge | 500から1500件 | 新興領域、ノイズが多い話題、網羅性が重要な調査 |
| xxlarge | 1500件超 | 明示的に大規模調査が必要な場合。SQLite、sharding、再開可能実行を推奨 |

重要なのは「目標件数」や「完了速度」ではなく「必要十分な証拠量」です。関連性が高い一次情報が少数で揃うなら、small で止める方がよいです。一方、テーマが広い、情報が新しい、ソース間で矛盾がある、またはユーザーが明示的に広範調査を求めている場合は、時間をかけて xlarge 以上まで広げてもよいです。

## 動的な調査先選定

固定ルートではなく、テーマに応じて候補チャネルを組み替えます。

| テーマ | 初期候補 | 備考 |
| --- | --- | --- |
| OSS/開発ツール | GitHub, Exa, web, package registries | 公式 repo と README/Docs を優先 |
| MCP/agent protocol | MCP Registry, GitHub, Exa, web, Bluesky/Twitter | registry と仕様/公式 docs を軸にする |
| 日本語技術コミュニティ | Qiita, Zenn, note, Hatena Bookmark, Exa, RSSHub | 現時点では Zenn/note は Exa+web 経由が現実的 |
| ニュース/時系列 | RSS, Exa, web, GDELT/NewsAPI候補 | 公開日とイベント日を分けて扱う |
| 学術/論文 | arXiv, OpenAlex, Semantic Scholar, Crossref, web | 追加チャネル候補として実装価値が高い |
| セキュリティ | GitHub Security Advisories, OSV, NVD, vendor advisories, RSS | 公式 advisory を優先 |
| 社会的反応 | Bluesky, optional Twitter/X, Mastodon候補, Reddit候補 | ノイズが多いため trend signal として扱う |
| 動画/イベント | YouTube, RSS, web | transcript や metadata を証拠として保存 |

この表は探索の出発点であり、固定パイプラインではありません。Codex は pilot の結果を見て、チャネルを足す、外す、クエリを言い換える、言語を変える、期間を絞る、といった判断を行うべきです。

## 関連性ガード

大規模調査では、次のガードを入れるべきです。

- 各クエリに `intent` を持たせる。
  例: `official_docs`, `oss_candidates`, `community_signal`, `recent_news`, `security_advisory`。

- 各チャネルに `source_role` を持たせる。
  例: GitHub は実装確認、MCP Registry は公式 registry、Bluesky/Twitter は社会的反応、RSS は時系列監視。

- pilot 後に relevance audit を行う。
  先頭 N 件だけでも、タイトル/URL/抜粋が調査テーマに合っているかを確認し、ノイズが多ければクエリを修正します。

- 重複率を見る。
  重複が高い場合は deep read へ進み、重複が低くても関連性が低ければ横展開を止めます。

- 公式/一次情報を deep read に含める。
  ソーシャルやまとめ記事だけで結論を作らず、公式 docs、repo、仕様、release notes、vendor advisory などを anchor として読むべきです。

- 使わなかったチャネルも記録する。
  readiness 不足、テーマ不一致、ノイズ過多、認証が必要、API制限などの理由を残すと、後続セッションで判断しやすくなります。

## 外部トレンドの要点

調査ツールの流れは、次のようにレイヤ化しています。

- 発見: 検索エンジン、registry、feed、social stream
- 抽出: page reader、crawler library、browser automation、document parsing
- registry/governance: MCP registry、agent registry、skills、supply-chain metadata
- orchestration: workflow、schedule、resumable batch、downstream ranking

Agent Reach は、この流れの中で薄い collection substrate として位置づけるのが自然です。ランキング、要約、投稿まで抱え込むよりも、収集計画、ソースアダプタ、証拠保存、handoff format を強くする方が、既存の設計方針に合っています。

重要な調査 anchor:

- MCP Registry は public MCP server の公式 metadata repository として位置づけられており、REST API と OpenAPI spec を提供しています: <https://modelcontextprotocol.io/registry/about>
- A2A Protocol は agent-to-agent communication を担い、MCP の agent-to-tool/resource の役割と補完関係にあります: <https://a2a-protocol.org/latest/>
- Firecrawl は AI agent 向け web data API として強いシグナルがあり、公開 case study では 6M+ URL/month の production workload が言及されています: <https://firecrawl.dev/blog/credal-firecrawl-ai-agents>
- Crawl4AI は async crawling、markdown generation、browser control、extraction strategies を備えた active OSS crawler/scraper です: <https://docs.crawl4ai.com/>
- `mcp-omnisearch` のように、Tavily、Brave、Kagi、Exa、Linkup、Firecrawl、GitHub search などを1つの MCP surface にまとめる動きも出ています: <https://github.com/spences10/mcp-omnisearch>

## OSS/調査先候補

deep run で読んだ代表的な repository:

| 領域 | 候補 | メモ |
| --- | --- | --- |
| AI web data API | <https://github.com/firecrawl/firecrawl> | 106k+ stars。AI agent 向け search/scrape/crawl の強い候補。 |
| local crawler/extractor | <https://github.com/unclecode/crawl4ai> | 63k+ stars。Python/Apache-2.0。LLM-friendly crawler/scraper。 |
| unified MCP search | <https://github.com/spences10/mcp-omnisearch> | 複数検索/抽出 provider を MCP に集約。 |
| MCP registry | <https://github.com/modelcontextprotocol/registry> | 公式 public MCP metadata registry 実装。 |
| agent registry concept | <https://github.com/agentoperations/agent-registry> | agents、skills、MCP servers、trust signals の metadata store。 |
| RSS expansion | <https://github.com/DIYgod/RSSHub> | 通常 feed がない媒体を RSS 化する route ecosystem。 |
| feed state | <https://github.com/miniflux/v2> | Atom/RSS/JSON Feed/OPML 周辺の参考実装。 |
| crawling at scale | <https://github.com/apify/crawlee> | Playwright/Puppeteer/Cheerio/JSDOM/raw HTTP、proxy rotation など。 |
| mature Python crawler | <https://github.com/scrapy/scrapy> | 長く使われている Python crawling framework。 |
| text extraction | <https://github.com/adbar/trafilatura> | web text/metadata extraction、crawling、複数出力形式、RAG 関連 topic。 |
| metasearch | <https://github.com/searxng/searxng> | self-hostable metasearch aggregator。 |
| workflow automation | <https://github.com/activepieces/activepieces> | AI workflow automation と MCP 文脈の参考。 |
| workflow automation | <https://github.com/n8n-io/n8n> | 大規模 workflow automation ecosystem。 |
| agent framework signal | <https://github.com/langchain-ai/langgraph> | downstream orchestration 連携の参考。collection adapter ではない。 |
| agent framework signal | <https://github.com/microsoft/autogen> | agent framework の trend signal。collection adapter ではない。 |

## 推奨アーキテクチャ

### P0: 動的調査 plan

固定ルートを避けるため、まずは plan-only の動的計画を作れるようにします。

候補インターフェース:

```powershell
agent-reach scout --topic "AI agent research tooling" --budget auto --plan-only --json
```

plan に含めたい情報:

- topic classification
- suggested research budget: `small`, `medium`, `large`, `xlarge`
- quality profile: default to `precision`
- candidate channels and why they are relevant
- skipped channels and why they are not selected
- pilot queries
- expansion criteria
- stop criteria
- required readiness checks

これはランキングや要約ではなく、収集計画を作るための診断情報です。最終判断は Codex または downstream project が行います。

品質優先の候補インターフェース:

```powershell
agent-reach scout --topic "AI agent research tooling" --quality precision --budget auto --plan-only --json
agent-reach batch --plan research.plan.json --quality precision --checkpoint-every 100 --json
```

`--quality precision` は「低レイテンシ」ではなく「関連性・一次情報・証拠の強さ」を優先するヒントです。実装する場合も、Agent Reach が結論を採点するのではなく、Codex が判断しやすいように checkpoint summary、source role、intent、candidate fields を整える程度に留めるのがよいです。

### P0: batch collection command

Codex や downstream script が `collect` を手でループしなくて済むように、first-class batch runner を追加します。

候補インターフェース:

```powershell
agent-reach batch --plan research.plan.json --save .agent-reach/evidence.jsonl --concurrency 4 --resume --json
```

plan file 例:

```json
{
  "run_id": "2026-04-10-agent-reach-example",
  "queries": [
    {"channel": "github", "operation": "search", "input": "mcp server", "limit": 100, "intent": "oss_candidates"},
    {"channel": "qiita", "operation": "search", "input": "MCP", "limit": 50, "intent": "japanese_community_signal"},
    {"channel": "bluesky", "operation": "search", "input": "MCP", "limit": 50, "intent": "social_signal"}
  ],
  "concurrency": 4,
  "failure_policy": "partial",
  "expansion_policy": "codex_decides",
  "quality_profile": "precision"
}
```

acceptance criteria:

- bounded concurrency で複数 collection を実行する。
- CLI version、channel registry version、start/end time、operation status、counts、error summary を run manifest に残す。
- 完了済み `(channel, operation, input, limit, intent)` を skip して resume できる。
- optional channel の失敗は、`failure_policy=strict` でない限り partial として扱う。
- checkpoint summary で件数、重複率、主要 source role、ノイズ傾向を確認できる。
- ranking、summarization、posting は所有しない。

### P0: relevance audit support

件数偏重を避けるため、候補の関連性を点検しやすい出力を追加します。

候補インターフェース:

```powershell
agent-reach plan candidates --input .agent-reach/evidence.jsonl --fields id,title,url,source,intent --json
agent-reach plan candidates --input .agent-reach/evidence.jsonl --summary-only --json
```

追加したい metadata:

- `intent`
- `query_id`
- `source_role`
- `seen_in`
- `candidate_key`
- `alternate_urls`

Agent Reach 自身が品質スコアを決める必要はありません。ただし、Codex が「この候補は今回の調査テーマに合っているか」を確認できるよう、軽い構造化情報を残すべきです。

### P0: large output controls

1000件規模では JSON 出力が大きくなります。

候補インターフェース:

```powershell
agent-reach plan candidates --input .agent-reach/evidence.jsonl --summary-only --json
agent-reach plan candidates --input .agent-reach/evidence.jsonl --fields id,title,url,source --json
agent-reach collect --channel qiita --operation search --input "MCP" --limit 100 --body-mode none --json
```

acceptance criteria:

- `--summary-only` は件数だけ返す。
- `--fields` は candidate item の出力フィールドを絞る。
- `--body-mode none|snippet|full` は高ボリューム検索チャネルに適用する。
- 既存の full-fidelity JSON は引き続き利用できる。

### P0: pagination contract

現状の adapter は、おおむね1 collection command につき1 request です。1000件超を自然に扱うには、共通の pagination/cursor model が必要です。

候補 adapter contract:

- `limit`: 合計取得件数
- `page_size`: request ごとの件数
- `max_pages`: 明示的な guardrail
- `cursor` or `page`: backend-specific continuation token
- `since` and `until`: 対応チャネルでの期間指定

候補 result metadata:

```json
{
  "pagination": {
    "requested_limit": 1000,
    "page_size": 100,
    "pages_fetched": 10,
    "next_cursor": "...",
    "has_more": true
  }
}
```

最初の対象は GitHub、Qiita、Bluesky、Twitter/X がよいです。RSS は page fan-out よりも feed list fan-out が必要です。

### P1: ledger sharding or SQLite backend

逐次 JSONL は 1089 items では通りましたが、並列・再開可能・100k items まで考えるなら、より安全な保存形式が必要です。

最初の候補:

```powershell
agent-reach batch --save-dir .agent-reach/runs/2026-04-10 --shard-by operation
agent-reach ledger merge --input .agent-reach/runs/2026-04-10 --output .agent-reach/evidence.jsonl
```

次の候補:

```powershell
agent-reach batch --ledger sqlite:.agent-reach/evidence.db
agent-reach plan candidates --input sqlite:.agent-reach/evidence.db --json
```

SQLite は 1000件から100k件規模で有効です。URL と item ID に index を張れるため dedupe が速くなり、console 出力も小さくできます。

### P1: source pack は固定ルートではなく seed として扱う

source pack は便利ですが、固定パイプラインとして実行してはいけません。役割は「初期候補の seed」を作ることです。

候補インターフェース:

```powershell
agent-reach scout --topic "AI agent research tooling" --preset oss-watch --budget auto --plan-only --json
agent-reach scout --topic "MCP security" --preset japan-tech --budget auto --plan-only --json
agent-reach scout --topic "web crawling for agents" --preset broad-web --budget auto --plan-only --json
```

source pack 候補:

- `broad-web`: Exa plus selected `web read`
- `oss-watch`: GitHub search/read, MCP Registry, package registries
- `japan-tech`: Qiita, Hatena Bookmark, Zenn/note discovery through Exa, RSSHub routes
- `social-pulse`: Bluesky plus optional Twitter/X, maybe Mastodon later
- `feed-watch`: RSS/Atom, RSSHub route lists, Miniflux/OPML input
- `research-papers`: arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed
- `security`: GitHub Security Advisories, OSV, NVD, Snyk advisories where available

`preset` は選択肢であって、Codex の判断を置き換えるものではありません。

### P1: new channel candidates

優先度の高い追加チャネル:

- `mcp_registry`: official MCP Registry REST API。operations: `search`, `read`, maybe `list`
- `firecrawl`: optional cloud/self-host adapter。operations: `search`, `read` or `scrape`, `crawl`
- `crawl4ai`: optional local Python/browser adapter。operations: `read`, `crawl`
- `searxng`: self-hostable metasearch。operation: `search`
- `rsshub`: route-based feed discovery/read helper。operations: `read`, `search_routes`
- `hacker_news`: Algolia API or HN RSS wrapper。operations: `search`, `item`
- `arxiv`, `openalex`, `semantic_scholar`, `crossref`: paper/source discovery
- `gitlab`, `huggingface`, `pypi`, `npm`: developer ecosystem coverage
- `mastodon`: ActivityPub/instance search where public APIs allow it
- `zenn`, `note`, `connpass`: Japan-focused technical/community coverage
- `reddit`: official または許容可能な API path がある場合のみ。auth と API terms を慎重に扱う

中優先度の provider adapter:

- Brave Search API
- Tavily
- Kagi
- Linkup
- Perplexity Sonar
- SerpAPI or SearchAPI.io
- NewsAPI/GDELT for news-scale monitoring

これらは optional かつ credential-gated にします。

### P2: better dedupe

現状の URL canonicalization は scheme/host の lowercase と fragment stripping が中心です。改善候補:

- `utm_*`, `fbclid`, `gclid` など tracking params を落とす。
- 意味のない query param order を正規化する。
- `togithub.com/...` のような GitHub mirror URL を `github.com/...` に寄せる。
- social post の external URLs を alternate candidate key として抽出する。
- URL がない item には `content_hash` or `title_hash` を使う。
- `extras.seen_in` で全 sighting を保持する。

### P2: doctor exit modes

`agent-reach doctor --json` は、optional Twitter/X が probe 前に warn/unknown だと non-zero を返しました。これは保守的には妥当ですが、CI や Codex run では制御しやすい mode が必要です。

候補インターフェース:

```powershell
agent-reach doctor --json --core-only
agent-reach doctor --json --allow-optional-warn
agent-reach doctor --json --strict
```

default は保守的なままでよいですが、examples では mode を明示する方が安全です。

### P2: Windows UTF-8 guidance

PowerShell で evidence JSONL を読むときは、UTF-8 を明示します。

```powershell
Get-Content -Encoding UTF8 -LiteralPath ".agent-reach/evidence.jsonl" |
  ForEach-Object { $_ | ConvertFrom-Json }
```

`-Encoding UTF8` なしだと、一部 Windows shell で日本語 Qiita record が文字化けし、`ConvertFrom-Json` まで失敗することがあります。

### P3: integration targets

ranking を Agent Reach に移さず、workflow/orchestration tool から使いやすくします。

- GitHub Actions examples that persist JSONL/SQLite artifacts
- n8n and Activepieces examples using `agent-reach collect --json` or batch output
- MCP server wrapper exposing read-only `channels`, `doctor`, `collect`, and `plan`
- Discord/news bot examples that keep scoring and posting policy downstream

## 実装順序

推奨順:

1. `scout --topic ... --budget auto --plan-only` で動的調査 plan を出す。
2. `--quality precision` と checkpoint summary の設計を追加する。
3. `plan candidates --summary-only` and `--fields` を追加する。
4. `collect --body-mode` を高ボリューム検索チャネル向けに追加する。
5. `batch --plan ... --concurrency ... --resume` を追加する。
6. GitHub、Qiita、Bluesky、Twitter/X に pagination を追加する。
7. sharded ledger merge を追加し、その後 SQLite を検討する。
8. `mcp_registry`, `searxng`, `firecrawl` を optional channel として追加する。
9. source pack を「固定ルート」ではなく plan seed として追加する。
10. RSSHub、papers、package registries、HN、日本語向け source を拡張する。
11. relevance audit 用の metadata と examples を追加する。

この順序なら、Agent Reach の「薄い collection layer」という設計を保ちながら、Codex が調査規模と調査先を柔軟に判断できる土台を強くできます。
