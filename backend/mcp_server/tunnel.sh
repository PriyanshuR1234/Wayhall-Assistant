#!/bin/bash
# Wayhall Civic AI — Remote MCP Server & Tunnel Launcher
# Runs the MCP Streamable-HTTP Server on port 8005 and creates a live HTTPS tunnel for Claude.ai Web.

set -e

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BACKEND_DIR"

echo "🏛️ Starting Wayhall Municipal MCP Server (Streamable-HTTP) on port 8005..."
PYTHONPATH="$BACKEND_DIR" .venv/bin/python -m mcp_server.server --transport streamable-http --host 127.0.0.1 --port 8005 &
SERVER_PID=$!

trap "kill $SERVER_PID 2>/dev/null || true" EXIT

sleep 2

echo "🌐 Opening public HTTPS Cloudflare tunnel..."
echo "--------------------------------------------------------"
if command -v cloudflared &> /dev/null; then
    cloudflared tunnel --url http://127.0.0.1:8005
elif [ -f /opt/homebrew/bin/cloudflared ]; then
    /opt/homebrew/bin/cloudflared tunnel --url http://127.0.0.1:8005
else
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -R 80:localhost:8005 nokey@localhost.run
fi
