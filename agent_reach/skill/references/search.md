# Search

Use Exa for broad web discovery.

```powershell
agent-reach collect --channel exa_search --operation search --input "latest o3 vs gpt-5.4" --limit 5 --json
```

For Qiita:

```powershell
agent-reach collect --channel qiita --operation search --input "python user:Qiita" --limit 5 --json
```

For note, Zenn, docs, and blogs:

1. Search with Exa.
2. Open the chosen result with Jina Reader.

```powershell
agent-reach collect --channel web --operation read --input "https://example.com/article" --json
```

If you need to debug Exa directly, fall back to:

```powershell
mcporter --config "$HOME\.mcporter\mcporter.json" call exa.web_search_exa --args "{\"query\":\"latest o3 vs gpt-5.4\",\"numResults\":5}" --output json
```

For Hatena Bookmark URL reactions:

```powershell
agent-reach collect --channel hatena_bookmark --operation read --input "https://example.com" --limit 5 --json
```
