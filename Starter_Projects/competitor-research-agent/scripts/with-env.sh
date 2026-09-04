#!/usr/bin/env bash
# Loads .env from the repo root, then execs the rest of the args.
# Used by .mcp.json so MCP servers automatically see env vars defined in .env.
#
# Example usage (from .mcp.json):
#   "command": "bash",
#   "args": ["scripts/with-env.sh", "npx", "-y", "some-mcp-server"]

set -a
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$ROOT_DIR/.env" ] && source "$ROOT_DIR/.env"
set +a

exec "$@"
