#!/usr/bin/env bash
# Commit and push any pending changes in this repo. Run manually whenever
# you want to publish local edits without going through a PR. Auto-bumps
# manifest.json's patch version on every push, since HACS tracks this repo
# by commit (no GitHub releases) and needs the version to change for an
# update to show up as meaningfully new.
#
# Usage: scripts/push.sh ["commit message"]

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ -z "$(git status --porcelain)" ]]; then
  echo "Nothing to commit — working tree clean."
  exit 0
fi

manifest="custom_components/photoframe/manifest.json"
current_version="$(grep -o '"version": "[0-9]*\.[0-9]*\.[0-9]*"' "$manifest" | grep -o '[0-9]*\.[0-9]*\.[0-9]*')"
IFS='.' read -r major minor patch <<< "$current_version"
new_version="$major.$minor.$((patch + 1))"
sed -i '' "s/\"version\": \"$current_version\"/\"version\": \"$new_version\"/" "$manifest"
echo "Bumped $manifest: $current_version -> $new_version"

message="${1:-Update $(date '+%Y-%m-%d %H:%M:%S')}"

git add -A
git status --short
git commit -m "$message"

branch="$(git rev-parse --abbrev-ref HEAD)"
git push origin "$branch"

echo "Pushed to origin/$branch."
