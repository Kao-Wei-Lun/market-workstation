#!/usr/bin/env bash
set -euo pipefail

msg="${1:-chore: checkpoint backup}"

git add -A
if ! git diff --cached --quiet; then
  git commit -m "$msg"
else
  echo "No staged changes to commit."
fi
