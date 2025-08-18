#!/usr/bin/env bash
set -euo pipefail
errs=0
files=$(git diff --cached --name-only | grep -E '\.cfg$' || true)
for f in $files; do
  # Count markers
  n=$(grep -E '^#\*#\s*<---------------------- SAVE_CONFIG ---------------------->' -c "$f" || true)
  if [ "${n:-0}" -gt 1 ]; then
    echo "❌ $f: Multiple SAVE_CONFIG markers detected ($n). Keep only one (the last)."
    errs=1
  fi
  # If file has a marker, ensure no gcode_macro lines appear after the marker start
  if grep -qE '^#\*#\s*<---------------------- SAVE_CONFIG ---------------------->' "$f"; then
    after=$(awk '/^#\*#\s*<---------------------- SAVE_CONFIG ---------------------->/{flag=1;next} flag' "$f" | grep -E '^\[gcode_macro\s' || true)
    if [ -n "$after" ]; then
      echo "❌ $f: gcode_macro found in auto-generated SAVE_CONFIG area. Move macros above the marker."
      errs=1
    fi
  fi
done
if [ "$errs" -ne 0 ]; then
  echo "Commit blocked by pre-commit hook."
  exit 1
fi
