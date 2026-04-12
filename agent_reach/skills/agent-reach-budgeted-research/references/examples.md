# Examples

## Example 1: Broad Research With Evidence

User ask:

```text
Agent Reach を使って、主要な AI agent framework を広く調べたい。後で証拠も見返したい。
```

Good plan:

```markdown
調査実行プラン
- 目的: 主要な AI agent framework の比較候補を広めに集めつつ、後で証拠を見返せる形で残す。
- 対象: AI agent framework に関する公式情報、関連 OSS、主要なコミュニティ反応。
- 鮮度要件: 実行時点の最新情報を優先する。最終回答では具体日付を明記する。
- 実行モード: broad_with_ledger
- 発見フェーズ: discovery は 3 クエリまで。`exa_search`、`github`、`hacker_news` から始め、各クエリは `--limit 5` から `--limit 8` に抑える。
- 成果物サイズ予算: discovery の JSON は `--raw-mode none`、`--item-text-mode snippet`、`--item-text-max-chars 240` を既定にする。大きい raw は監査上必要になった場合だけ再取得する。
- 証拠の残し方: 各 discovery は `--save-dir .agent-reach/shards` に保存し、まとまったら `ledger merge` を実行する。必要なら `ledger summarize` と `ledger query` で状態確認する。
- 候補選別ゲート: `plan candidates --by normalized_url --limit 20 --json` で候補を整理し、短い候補一覧を作ってから深掘り対象を決める。
- 深掘り予算: 深掘りは候補選別後の 5 件まで。公式 docs、公式 repo、一次発表を優先する。
- 最終まとめ境界: 最終要約は深掘りした候補と、その根拠リンクだけを対象にする。discovery で集めた全件を逐一要約しない。
- 停止条件: discovery 1 ラウンドで候補が十分なら停止する。足りない場合も追加 discovery は 1 ラウンドまでに留める。
- 前提と仮定: 全件監査や raw 保全の明示要件がないため、まず compact artifact を優先する。広めの収集だが、トークンと JSON サイズを抑えるため discovery と深掘りを分離する。
```

## Example 2: Small Multi-Source Comparison

User ask:

```text
Agent Reach で OpenAI と Anthropic の最近の agent docs を比較したいけど、重くはしたくない。
```

Good plan:

```markdown
調査実行プラン
- 目的: OpenAI と Anthropic の最近の agent docs の差分を、軽量な収集で比較する。
- 対象: OpenAI と Anthropic の公式 docs、公式発表、必要最小限の関連 repo。
- 鮮度要件: 実行時点の最新 docs と発表を優先する。最終回答では具体日付を明記する。
- 実行モード: bounded_multi_source
- 発見フェーズ: `web` と必要なら `github` を使い、発見コマンドは 2-3 本までに留める。各コマンドは `--limit 5` を既定にする。
- 成果物サイズ予算: `--raw-mode none` と `--item-text-mode snippet` を使い、docs discovery の保持テキストは小さくする。
- 証拠の残し方: 保存は必須ではない。証拠が必要になった場合だけ `--save .agent-reach/evidence.jsonl` を使う。
- 候補選別ゲート: docs URL と release notes の候補だけを短く残し、必要なページだけを読む。
- 深掘り予算: 深掘りは 3 ページまで。docs トップ、関連リリースノート、必要なら 1 つの repo に限定する。
- 最終まとめ境界: 最終要約は比較に必要な差分だけをまとめ、途中 discovery の全件列挙はしない。
- 停止条件: 比較に必要な公式ページが揃った時点で停止する。
- 前提と仮定: 「重くしたくない」という要望を優先し、ledger や broad discovery は使わない前提にした。
```
