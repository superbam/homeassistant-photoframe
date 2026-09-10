#!/usr/bin/env bash
# Commit and push any pending changes in this repo. Run manually whenever
# you want to publish local edits without going through a PR.
#
# Usage: scripts/push.sh ["commit message"]

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ -z "$(git status --porcelain)" ]]; then
  echo "Nothing to commit — working tree clean."
  exit 0
fi

message="${1:-Update $(date '+%Y-%m-%d %H:%M:%S')}"

git add -A
git status --short
git commit -m "$message"

branch="$(git rev-parse --abbrev-ref HEAD)"
git push origin "$branch"

echo "Pushed to origin/$branch."
