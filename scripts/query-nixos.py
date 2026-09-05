#!/usr/bin/env python3
"""
CLI wrapper for querying the mcp-nixos MCP server over stdio.
Ensures deterministic Nixpkgs package lookups for development environments.
"""

import sys
import json
import shutil
import argparse
from subprocess import Popen, PIPE

def call_mcp_nixos(action: str, query: str = "", query_type: str = "packages", channel: str = "unstable", limit: int = 15):
    if not shutil.which("uvx"):
        print("ERROR: 'uvx' command not found. Ensure Astral uv is installed.", file=sys.stderr)
        sys.exit(1)

    try:
        proc = Popen(["uvx", "mcp-nixos"], stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
    except Exception as e:
        print(f"ERROR: Failed to launch mcp-nixos via uvx: {e}", file=sys.stderr)
        sys.exit(1)

    def send_rpc(method: str, params=None, req_id=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if req_id is not None:
            msg["id"] = req_id
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()
        if req_id is not None:
            line = proc.stdout.readline()
            if not line:
                raise RuntimeError("Empty response from mcp-nixos server")
            return json.loads(line)
        return None

    try:
        # Initialize
        send_rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "query-nixos-cli", "version": "1.0"}
        }, req_id=1)
        send_rpc("notifications/initialized")

        args = {
            "action": action,
            "channel": channel,
            "limit": limit
        }
        if query:
            args["query"] = query
        if query_type:
            args["type"] = query_type

        resp = send_rpc("tools/call", {"name": "nix", "arguments": args}, req_id=2)
        proc.kill()

        if "error" in resp:
            print(f"MCP ERROR: {resp['error']}", file=sys.stderr)
            sys.exit(1)

        result_content = resp.get("result", {}).get("content", [])
        text_output = "\n".join(c.get("text", "") for c in result_content if c.get("type") == "text")
        return text_output
    except Exception as e:
        proc.kill()
        print(f"ERROR communicating with mcp-nixos: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Deterministic Nixpkgs package query CLI via mcp-nixos")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--search", help="Search Nix packages by keyword")
    group.add_argument("--info", help="Get exact package details")

    parser.add_argument("--type", default="packages", choices=["packages", "programs", "flakes"], help="Query sub-type")
    parser.add_argument("--channel", default="unstable", help="Channel (unstable, 24.11, etc.)")
    parser.add_argument("--limit", type=int, default=15, help="Maximum number of results")

    args = parser.parse_args()

    if args.search:
        out = call_mcp_nixos("search", query=args.search, query_type="packages", channel=args.channel, limit=args.limit)
    elif args.info:
        out = call_mcp_nixos("info", query=args.info, query_type="package", channel=args.channel)

    print(out)

if __name__ == "__main__":
    main()
