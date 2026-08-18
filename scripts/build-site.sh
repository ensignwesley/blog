#!/usr/bin/env bash
# Build the Hugo site without exposing an empty/half-built public/ directory.
#
# Why this exists: `hugo --cleanDestinationDir` deletes stale output before the
# build completes. If Hugo or the surrounding session dies after the clean step,
# nginx can be left serving a missing/stale generated site. This script builds
# into a fresh temp directory first, then swaps it into place only after Hugo
# succeeds.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/public"
TMP_PARENT="$ROOT/.build"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TMP_DIR="$TMP_PARENT/hugo-$STAMP.$$"
NEW_PUBLIC="$TMP_DIR/public"
BACKUP="$TMP_PARENT/public.previous.$STAMP.$$"
LOG_DIR="$ROOT/logs"
LOG_FILE="$LOG_DIR/build-$STAMP.log"

mkdir -p "$TMP_PARENT" "$LOG_DIR"

cleanup() {
  rm -rf "$TMP_DIR"
  if [[ -d "$BACKUP" && ! -e "$DEST" ]]; then
    mv "$BACKUP" "$DEST"
  fi
}
trap cleanup EXIT

{
  echo "[$(date -u --iso-8601=seconds)] build start"
  echo "root=$ROOT"
  echo "destination=$DEST"
  echo "tmp=$NEW_PUBLIC"
  echo
  free -h || true
  echo
  "$ROOT/scripts/generate-status-fallback.py"
  echo
  "$ROOT/scripts/generate-flight-recorder.py"
  echo
  HUGO_BIN="${HUGO_BIN:-hugo}"
  /usr/bin/time -v "$HUGO_BIN" --source "$ROOT" --destination "$NEW_PUBLIC"
  echo
  echo "[$(date -u --iso-8601=seconds)] hugo build succeeded"
} 2>&1 | tee "$LOG_FILE"

if [[ ! -f "$NEW_PUBLIC/index.html" ]]; then
  echo "ERROR: build output missing index.html" | tee -a "$LOG_FILE" >&2
  exit 1
fi

# Swap only after the build has succeeded. If anything fails mid-swap, cleanup()
# restores the previous public/ directory.
rm -rf "$BACKUP"
if [[ -e "$DEST" ]]; then
  mv "$DEST" "$BACKUP"
fi
mv "$NEW_PUBLIC" "$DEST"
rm -rf "$BACKUP"
trap - EXIT
rm -rf "$TMP_DIR"

echo "[$(date -u --iso-8601=seconds)] deployed $DEST" | tee -a "$LOG_FILE"
echo "log=$LOG_FILE"
