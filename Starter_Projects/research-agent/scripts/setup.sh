#!/usr/bin/env bash
# One-time setup for the competitor-research workshop.
# Idempotent: safe to re-run any time. Does two things:
#   1. Creates .env from .env.example if missing (so students can add their Brave key).
#   2. Installs Playwright Chromium browser if not already present.

set -e

# Resolve repo root regardless of where the script is invoked from
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Detect Playwright cache directory across platforms
case "$OSTYPE" in
  darwin*)  CACHE_DIR="$HOME/Library/Caches/ms-playwright" ;;
  linux*)   CACHE_DIR="$HOME/.cache/ms-playwright" ;;
  msys*|cygwin*|win32) CACHE_DIR="$LOCALAPPDATA/ms-playwright" ;;
  *)        CACHE_DIR="$HOME/.cache/ms-playwright" ;;
esac

# ─── Step 1: .env file ────────────────────────────────────────────
if [ -f "$ROOT_DIR/.env" ]; then
  echo "✓ .env already exists (left untouched)."
elif [ -f "$ROOT_DIR/.env.example" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo "✓ Created .env from .env.example."
  echo "  → Edit .env now to add your BRAVE_API_KEY (optional)."
fi

# ─── Step 2: Playwright Chromium ──────────────────────────────────
if compgen -G "$CACHE_DIR/chromium-*" > /dev/null 2>&1; then
  echo "✓ Playwright Chromium already installed."
  exit 0
fi

echo "──────────────────────────────────────────────────────────────"
echo "  First-time setup: installing Playwright Chromium (~165 MB)"
echo "  This runs once per machine. Subsequent runs skip this."
echo "──────────────────────────────────────────────────────────────"

if ! command -v npx > /dev/null 2>&1; then
  echo "Error: npx not found. Install Node.js from https://nodejs.org first." >&2
  exit 1
fi

npx playwright install chromium

echo "✓ Playwright setup complete."
