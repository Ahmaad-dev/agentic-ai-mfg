#!/usr/bin/env bash
# Download all thesis reference PDFs listed in paper.txt into this directory.
#
#   Usage:  ./download.sh [list-file]      (default list: paper.txt)
#
# Idempotent: skips files that already exist and are valid PDFs; retries only
# the missing/corrupt ones. Lines starting with '#' and blank lines are ignored.
set -u
cd "$(dirname "$0")"
LIST="${1:-paper.txt}"

if [ ! -f "$LIST" ]; then
  echo "list file not found: $LIST" >&2
  exit 1
fi

ok=0; skip=0; fail=0; failed_names=""
trim() { local s="$1"; s="${s#"${s%%[![:space:]]*}"}"; s="${s%"${s##*[![:space:]]}"}"; printf '%s' "$s"; }
while IFS='|' read -r name url; do
  name="$(trim "${name:-}")"
  case "$name" in ''|\#*) continue ;; esac
  url="$(trim "${url:-}")"
  [ -z "$url" ] && continue

  out="${name}.pdf"
  if [ -s "$out" ] && head -c 5 "$out" | grep -q "%PDF"; then
    printf 'SKIP %s\n' "$out"; skip=$((skip + 1)); continue
  fi

  code=$(curl -sS -L -A "Mozilla/5.0" --max-time 90 -w "%{http_code}" -o "$out" "$url" 2>/dev/null)
  if [ "$code" = "200" ] && [ -s "$out" ] && head -c 5 "$out" | grep -q "%PDF"; then
    printf 'OK   %-6s %s\n' "$(du -h "$out" | cut -f1)" "$out"; ok=$((ok + 1))
  else
    printf 'FAIL (%s) %s\n' "$code" "$out"; rm -f "$out"
    fail=$((fail + 1)); failed_names="${failed_names} ${name}"
  fi
done < "$LIST"

echo "----------------------------------------"
echo "downloaded=$ok  skipped=$skip  failed=$fail"
[ -n "$failed_names" ] && echo "failed:${failed_names}"
echo "total PDFs in $(pwd): $(ls -1 *.pdf 2>/dev/null | wc -l | tr -d ' ')"
