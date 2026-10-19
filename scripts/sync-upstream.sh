#!/usr/bin/env bash
# Merge fetched upstream changes into a dedicated branch. Never resets the fork's main branch.
# Usage: scripts/sync-upstream.sh [upstream ref] [fork base ref] [sync branch]
set -euo pipefail
SOURCE_REF="${1:-upstream/main}"
BASE_REF="${2:-origin/main}"
SYNC_BRANCH="${3:-automation/sync-upstream}"
[ -z "$(git status --porcelain)" ] || { echo "Commit or stash local changes before syncing." >&2; exit 1; }
[ ! -f "$(git rev-parse --git-path MERGE_HEAD)" ] || { echo "Finish the existing merge first." >&2; exit 1; }
git rev-parse --verify "$SOURCE_REF^{commit}" >/dev/null
git rev-parse --verify "$BASE_REF^{commit}" >/dev/null
if git show-ref --verify --quiet "refs/heads/$SYNC_BRANCH"; then
  git switch "$SYNC_BRANCH"
elif git show-ref --verify --quiet "refs/remotes/origin/$SYNC_BRANCH"; then
  git switch --create "$SYNC_BRANCH" --track "origin/$SYNC_BRANCH"
else
  git switch --create "$SYNC_BRANCH" "$BASE_REF"
fi
merge_ref() {
  if ! git merge --no-ff --no-edit "$1"; then
    git merge --abort
    echo "Sync stopped on a merge conflict. No remote changes were pushed; resolve this update manually." >&2
    return 1
  fi
}
merge_ref "$BASE_REF"
merge_ref "$SOURCE_REF"
if git diff --quiet "$BASE_REF" HEAD; then
  echo "The fork already contains the upstream file changes."
  [ -z "${GITHUB_OUTPUT:-}" ] || echo "changed=false" >> "$GITHUB_OUTPUT"
else
  echo "Merged upstream while retaining the fork's changes."
  [ -z "${GITHUB_OUTPUT:-}" ] || echo "changed=true" >> "$GITHUB_OUTPUT"
fi
