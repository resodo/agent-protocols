#!/usr/bin/env bash
# Create/refresh the per-protocol skill symlinks a consumer repo needs, and
# remove dangling ones. Run from a consumer repo after moving the submodule
# pointer. Mirrors the check in the consumer's scripts/agent_protocols_guard.sh:
# every <protocol>/SKILL.md must be mounted at .claude/skills/<protocol> and
# .agents/skills/<protocol> as a symlink to ../../<submodule path>/<protocol>.
#
# Usage: sync_skill_mounts.sh [submodule-path]   (default: external/agent-protocols)
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
protocol_path="${1:-external/agent-protocols}"
prefix="../../$protocol_path/"

for dir in .claude/skills .agents/skills; do
  mkdir -p "$dir"

  # Drop mounts into the submodule whose protocol no longer ships a SKILL.md.
  for link in "$dir"/*; do
    [[ -L "$link" ]] || continue
    target="$(readlink "$link")"
    [[ "$target" == "$prefix"* ]] || continue
    [[ -f "$link/SKILL.md" ]] || { rm "$link"; echo "removed dangling mount: $link"; }
  done

  for skill in "$protocol_path"/*/SKILL.md; do
    protocol="$(basename "$(dirname "$skill")")"
    mount="$dir/$protocol"
    if [[ -L "$mount" && "$(readlink "$mount")" == "$prefix$protocol" ]]; then
      continue
    fi
    rm -rf "$mount"
    ln -s "$prefix$protocol" "$mount"
    echo "mounted: $mount"
  done
done
