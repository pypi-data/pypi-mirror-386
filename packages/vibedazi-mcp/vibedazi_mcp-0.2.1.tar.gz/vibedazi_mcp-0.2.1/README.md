# vibeDazi MCP Server

![vibeDazi Banner](https://i.dawnlab.me/568277afa7324f1afe6842a9638079fb.png)


[中文文档 README_CH.md](README_CH.md)

Team-shared MCP logging with git user/branch/diffs and prompt context.

## Install

```bash
./install-vibedazi.sh
```

## Run

```bash
vibedazi-mcp
```

## VSCode MCP

Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "vibedazi": {
      "type": "stdio",
      "command": "vibedazi-mcp"
    }
  }
}
```

## Cursor MCP

Create or update `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "vibedazi": {
      "type": "stdio",
      "command": "/absolute/path/to/your/.venv-vibedazi/bin/vibedazi-mcp"
    }
  }
}
```

Tip: running `./install-vibedazi.sh` will create the venv, install the package, and write this file for you using the correct absolute path.

## Project policy

The installer writes a root-level `rule.md` with the policy. Load it into your project prompt (or leave it for teammates to read).

## AI Squash Merge tool

This MCP exposes a helper to attribute AI work without cluttering history.

- Tool: `ai_squash_merge`
- Flow: creates `ai/<timestamp>-<hint>` branch, commits current changes with AI author, switches back, and `git merge --squash` into your base branch. Optionally deletes the AI branch.

When To Call
- After you’ve finished an AI-assisted change and validated it (tests/build pass).
- Call it right before your final `log_round` (so `log_round` remains last).
- Goal: attribute the work to the AI author without interrupting your development flow.

How To Call
- In Cursor/VSCode MCP Tools: run `vibedazi.ai_squash_merge` with the params below.
- Or from Python while your venv is active.

Parameters (common)
- `branch_hint`: optional suffix in branch name
- `model_name`: label like `GPT-5`, `Claude`, `o3` (no default; pass explicitly to attribute the right model)
- `author_name`, `author_email`: optional overrides for AI identity (if omitted, inferred from model_name)
- `base_branch`: target branch (defaults to current)
- `include_untracked`: stage new files too (default true)
- `paths`: restrict staged paths
- `co_author_trailer`: add `Co-authored-by` trailer on squash commit (default true)
- `delete_ai_branch`: delete the AI branch after squash (default false)
- `set_committer_to_ai`: set committer to AI on the AI branch commit (default false)
- `auto_stash`: try stashing if branch creation would overwrite files (default false)

Recommended Usage
- Keep your development on `main` (or your feature branch). Let the tool branch and return automatically.
- Pass `paths` to commit only source files (avoid `.vibe-dazi/**`, `__pycache__`, `*.egg-info`).
- Set `delete_ai_branch=true` to avoid branch clutter unless you want to inspect the AI-only commit later.

Expected Result
- Seamless flow: the tool creates a temporary `ai/<timestamp>-<hint>` branch, makes a single AI-authored commit, switches back to your base branch, and merges it with `--squash` to keep history clean.
- Clear attribution:
  - The AI branch commit uses the AI as author (e.g. `GPT-5 <noreply@openai.com>`).
  - The squash commit includes `Co-authored-by` and `Squashed-from` trailers to preserve provenance.
- Uninterrupted development: you remain on your original branch the whole time.
- Auto-cleanup: temporary AI branches are deleted by default (`delete_ai_branch=true`).

Notes
- If the repository has no commits yet, the tool creates an AI commit on the AI branch and skips the squash (no base to merge into). Make an initial commit and run again to squash.
- On conflict during squash, it returns `status: conflict` so you can resolve and commit manually.

Examples
- Minimal (auto-detect base branch):
  - `ai_squash_merge(branch_hint="refactor", model_name="Claude")`
- Commit only code paths and delete the AI branch after:
  - `ai_squash_merge(branch_hint="bugfix-xyz", paths=["vibeDazi/src/..."], delete_ai_branch=True)`
- If branch creation complains about overwriting files:
  - `ai_squash_merge(branch_hint="feature-a", auto_stash=True)`

## Configuration

You can control defaults and logging behavior via `.vibe-dazi/config.json` at the repo root (created by the installer). Example:

```json
{
  "log": {
    "ignore_paths": [
      ".vibe-dazi/rounds/**",
      "**/__pycache__/**",
      "**/*.egg-info/**"
    ],
    "max_events": 200,
    "per_file_diff_max_bytes": 120000,
    "snapshot_max_bytes": 240000,
    "snapshot_enabled": true,
    "include_commits_since_last": true
  },
  "ai_squash_merge": {
    "model_name": null,
    "author_name": null,
    "author_email": null,
    "base_branch": null,
    "include_untracked": true,
    "co_author_trailer": true,
    "delete_ai_branch": true,
    "set_committer_to_ai": false,
    "auto_stash": false
  }
}
```

Notes:
- Change `ai_squash_merge.delete_ai_branch` to `false` if you want to keep AI branches around.
- Add patterns to `log.ignore_paths` to exclude more files from diffs/snapshots.
- `per_file_diff_max_bytes` and `snapshot_max_bytes` cap the diff sizes to keep JSON outputs manageable.

