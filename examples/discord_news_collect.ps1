# Collect raw news candidates for a downstream Discord bot without posting.

param(
  [string]$Query = "OpenAI",
  [string]$OutputDir = ".agent-reach/discord-news",
  [int]$Limit = 5,
  [string]$RunId = ("discord-news-" + [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ"))
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$EvidencePath = Join-Path $OutputDir "evidence.jsonl"
$BlueskyJson = Join-Path $OutputDir "bluesky.json"
$QiitaJson = Join-Path $OutputDir "qiita.json"
$CandidatesJson = Join-Path $OutputDir "candidates.json"

agent-reach collect --json --save $EvidencePath --run-id $RunId --channel bluesky --operation search --input $Query --limit $Limit |
  Set-Content -Encoding utf8 -Path $BlueskyJson

agent-reach collect --json --save $EvidencePath --run-id $RunId --channel qiita --operation search --input $Query --limit $Limit |
  Set-Content -Encoding utf8 -Path $QiitaJson

agent-reach plan candidates --input $EvidencePath --by url --limit 20 --json |
  Set-Content -Encoding utf8 -Path $CandidatesJson

Write-Host "Wrote raw collection artifacts to $OutputDir for downstream review or bot logic."
