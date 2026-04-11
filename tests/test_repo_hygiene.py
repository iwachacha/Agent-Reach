# -*- coding: utf-8 -*-
"""Tests that lock in repository cleanup decisions."""

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_legacy_files_are_removed():
    repo_root = _repo_root()

    assert not (repo_root / "scripts" / "sync-upstream.sh").exists()
    assert not (repo_root / "test.sh").exists()
    assert not (repo_root / "CLAUDE.md").exists()
    assert not (repo_root / ".claude" / "settings.local.json").exists()
    assert not (repo_root / "docs" / "cookie-export.md").exists()
    assert not (repo_root / "docs" / "dependency-locking.md").exists()
    assert not (repo_root / "docs" / "update.md").exists()
    assert not (repo_root / "docs" / "README_en.md").exists()
    assert not (repo_root / "docs" / "README_ja.md").exists()
    assert not (repo_root / "docs" / "usage_ja.md").exists()
    assert not (repo_root / "docs" / "assets").exists()
    assert not (repo_root / "docs" / "wechat-group-qr.jpg").exists()
    assert not (repo_root / "docs" / "assets" / "logo-1.png").exists()
    assert not (repo_root / "docs" / "assets" / "logo-1.svg").exists()
    assert not (repo_root / "docs" / "assets" / "logo-2.png").exists()
    assert not (repo_root / "docs" / "assets" / "logo-2.svg").exists()
    assert not (repo_root / "docs" / "assets" / "logo-3.png").exists()
    assert not (repo_root / "docs" / "assets" / "logo-3.svg").exists()


def test_readme_does_not_reference_untracked_usage_doc():
    readme = (_repo_root() / "README.md").read_text(encoding="utf-8")

    assert "docs/usage_ja.md" not in readme


def test_docs_folder_only_contains_supported_docs():
    docs_dir = _repo_root() / "docs"
    names = {path.name for path in docs_dir.iterdir()}

    required_docs = {
        "agent-reach-nexus-concept.md",
        "codex-compatibility.md",
        "codex-integration.md",
        "downstream-usage.md",
        "field-research-improvements-2026-04-10.md",
        "install.md",
        "python-sdk.md",
        "troubleshooting.md",
    }
    allowed_docs = {
        *required_docs,
        "agent-reach-external-large-scale-research-prompt-2026-04-11.md",
        "agent-reach-external-mixed-collection-prompt-2026-04-11.md",
        "agent-reach-external-test-prompt-2026-04-11.md",
        "agent-reach-scale-evolution-research-2026-04-10.md",
    }

    assert required_docs <= names
    assert names <= allowed_docs


def test_caller_control_policy_is_documented_consistently():
    repo_root = _repo_root()
    files = {
        "readme": repo_root / "README.md",
        "downstream": repo_root / "docs" / "downstream-usage.md",
        "skill": repo_root / "agent_reach" / "skill" / "SKILL.md",
        "agent_prompt": repo_root / "agent_reach" / "skill" / "agents" / "openai.yaml",
    }

    texts = {name: path.read_text(encoding="utf-8") for name, path in files.items()}

    assert "Agent Reach does not choose" in texts["readme"]
    assert "auto-escalate" in texts["readme"]
    assert "explicit opt-in" in texts["readme"]
    assert "--limit 20" in texts["readme"]

    assert "The caller chooses scope" in texts["downstream"]
    assert "auto-escalate" in texts["downstream"]
    assert "explicit opt-in" in texts["downstream"]
    assert "--limit 20" in texts["downstream"]

    assert "The caller chooses" in texts["skill"]
    assert "auto-escalate" in texts["skill"]
    assert "explicit opt-in" in texts["skill"]
    assert "--limit 20" in texts["skill"]

    assert "does not choose scope" in texts["agent_prompt"]
    assert "explicit opt-in" in texts["agent_prompt"]
