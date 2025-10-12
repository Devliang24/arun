#!/usr/bin/env bash
set -euo pipefail

# Auto-fix YAML hooks style before commit

paths=(testcases testsuites)
changed=0

for p in "${paths[@]}"; do
  if [ -d "$p" ]; then
    python -m apirunner.cli fix "$p" || true
    changed=1
  fi
done

if [ "$changed" -eq 1 ]; then
  # Re-add possibly modified files
  git add testcases/**/*.yml testcases/**/*.yaml 2>/dev/null || true
  git add testsuites/**/*.yml testsuites/**/*.yaml 2>/dev/null || true
fi

exit 0

