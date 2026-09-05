# MCP NixOS Connection and Query Guide

The `mcp-nixos` server connects the agent to Nixpkgs, FlakeHub, and nix.dev data for resolving package attributes and dependencies. It prevents package hallucination and outdated attribute references.

## 1. Connection Configuration

The MCP server must be registered in the project's `.agents/mcp_config.json` or global `~/.gemini/config/mcp_config.json`:

```json
{
  "mcpServers": {
    "nixos": {
      "command": "uvx",
      "args": ["mcp-nixos"]
    }
  }
}
```

## 2. Server Tools Reference

Once connected, `mcp-nixos` provides tools to discover and inspect packages for development environments:

### Tool A: `nix`
General query tool for packages, flakes, and channels.

* **Search Packages**:
  ```json
  {
    "action": "search",
    "query": "mysql",
    "type": "packages",
    "channel": "unstable",
    "limit": 10
  }
  ```
* **Package Details (info)**:
  ```json
  {
    "action": "info",
    "query": "openjdk17",
    "type": "package",
    "channel": "unstable"
  }
  ```

### Tool B: `nix_versions`
Queries package version history on NixHub.io.

* **Find Specific Versions**:
  ```json
  {
    "package": "nodejs",
    "version": "20.10.0"
  }
  ```

## 3. CLI Helper Script

If the agent needs to query `mcp-nixos` via the command line or when verifying in scripts, execute:

```bash
# Search for packages
python3 scripts/query-nixos.py --search "mysql"

# Get package info
python3 scripts/query-nixos.py --info "openjdk17"
```

## 4. Query Intent Rules
* Never guess package attributes. For example, use `mysql84` instead of deprecated `mysql80`.
* For Java, use `openjdk17`, `openjdk21`, or `openjdk11` as identified from project manifests.
* For Python, prefer `python3` (or `python313`) paired with modern build tools (`uv`, `poetry`).
* Verify whether a package requires `allowUnfree = true` (e.g. `mysql-workbench`, `cudaPackages`).
