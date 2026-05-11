#!/usr/bin/env bash
# Import Claude Code skills from a GitHub repository.
#
# Usage:
#   ./import-github-skills.sh <github-repo-url> [skills-subdir] [--global]
#
# Examples:
#   ./import-github-skills.sh https://github.com/user/my-skills
#   ./import-github-skills.sh https://github.com/user/my-skills skills
#   ./import-github-skills.sh https://github.com/user/my-skills .claude/skills --global

set -euo pipefail

usage() {
  echo "Usage: $0 <github-repo-url> [skills-subdir] [--global]"
  echo ""
  echo "Arguments:"
  echo "  github-repo-url  GitHub repository URL (https or ssh)"
  echo "  skills-subdir    Subdirectory inside the repo that contains skills (default: .claude/skills)"
  echo "  --global         Install to ~/.claude/skills instead of .claude/skills"
  exit 1
}

if [[ $# -lt 1 ]]; then
  usage
fi

REPO_URL="$1"
SKILLS_SUBDIR="${2:-.claude/skills}"
GLOBAL=false

for arg in "$@"; do
  if [[ "$arg" == "--global" ]]; then
    GLOBAL=true
  fi
done

# Determine destination directory
if [[ "$GLOBAL" == true ]]; then
  DEST_DIR="$HOME/.claude/skills"
else
  DEST_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.claude/skills"
fi

# Extract repo name for temp directory
REPO_NAME=$(basename "$REPO_URL" .git)
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Cloning $REPO_URL..."
git clone --depth 1 "$REPO_URL" "$TMP_DIR/repo" 2>&1

SOURCE_DIR="$TMP_DIR/repo/$SKILLS_SUBDIR"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Error: '$SKILLS_SUBDIR' directory not found in the repository."
  echo "Available directories:"
  ls "$TMP_DIR/repo/"
  exit 1
fi

# Count skills to import
SKILL_COUNT=$(find "$SOURCE_DIR" -maxdepth 1 -mindepth 1 -type d | wc -l)
if [[ "$SKILL_COUNT" -eq 0 ]]; then
  echo "No skills found in $SKILLS_SUBDIR"
  exit 1
fi

echo "Found $SKILL_COUNT skill(s) in $SKILLS_SUBDIR"
echo "Installing to: $DEST_DIR"

mkdir -p "$DEST_DIR"

imported=0
skipped=0

find "$SOURCE_DIR" -maxdepth 1 -mindepth 1 -type d | while read -r skill_dir; do
  skill_name=$(basename "$skill_dir")

  if [[ ! -f "$skill_dir/SKILL.md" ]]; then
    echo "  Skipping '$skill_name' (no SKILL.md found)"
    skipped=$((skipped + 1))
    continue
  fi

  if [[ -d "$DEST_DIR/$skill_name" ]]; then
    echo "  Updating skill: $skill_name"
  else
    echo "  Installing skill: $skill_name"
  fi

  cp -r "$skill_dir" "$DEST_DIR/$skill_name"
  imported=$((imported + 1))
done

echo ""
echo "Done. Skills installed to $DEST_DIR"
echo "Use /<skill-name> in Claude Code to invoke them."
