# MCP Configuration Guide

This document explains how to configure Model Context Protocol (MCP) services.

## Overview

MCP (Model Context Protocol) is a standardized protocol that allows agents to safely interact with external systems, such as:
- File system operations
- GitHub repository access
- Web search
- Database queries

---

## Prerequisites

### Required Dependencies

```bash
pip install -r requirements.txt
```

### Node.js

MCP servers are typically Node.js packages. Ensure Node.js 18+ is installed (Node.js 20+ recommended).

```bash
node --version  # Should be v18+ (v20+ recommended)
```

---

## Environment Variables

Configure the following in your `.env` file:

| Variable | Required | Description |
|----------|----------|-------------|
| `WORKING_DIRECTORY` | ✅ | Data directory for filesystem MCP server |
| `TAVILY_API_KEY` | ❌ | API key for web-search MCP server |
| `GITHUB_TOKEN` | ❌ | Personal access token for github MCP server |

Example `.env`:

```sh
# Your data storage path (also used by filesystem MCP server)
WORKING_DIRECTORY = ./data/

# MCP (Model Context Protocol) Settings (optional)
# Tavily API key for web-search MCP server
TAVILY_API_KEY = your_tavily_api_key_here
# GitHub token for github MCP server
GITHUB_TOKEN = your_github_token_here
```

---

## Global Configuration

### File Location

MCP services are centrally defined in `config/mcp.yaml`:

```yaml
servers:
  filesystem:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "${WORKING_DIRECTORY}"]
    description: Local filesystem access for data files
    
  web-search:
    command: npx
    args: ["-y", "@anthropic/mcp-server-web-search"]
    env:
      TAVILY_API_KEY: ${TAVILY_API_KEY}
    description: Web search capabilities
    
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: ${GITHUB_TOKEN}
    description: GitHub repository access

defaults:
  - filesystem   # Enabled for all agents by default
```

### Configuration Structure

| Field | Description |
|-------|-------------|
| `servers` | All available MCP service definitions |
| `servers.{name}.command` | Command to start the service |
| `servers.{name}.args` | Command arguments |
| `servers.{name}.env` | Environment variables |
| `servers.{name}.description` | Human-readable description |
| `defaults` | Services enabled for all agents by default |

---

## Agent-Specific Configuration

### Enable in config.yaml

In addition to global `defaults`, each agent can enable additional services:

```yaml
# config/agents/search_agent/config.yaml
mcp_servers:
  - filesystem
  - web-search
```

### Final Result

Agent's enabled services = `defaults` ∪ Agent-specific `mcp_servers`

---

## Available Tools

### Filesystem Server

The `filesystem` MCP server provides 14 tools:

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents as text |
| `read_text_file` | Read file with encoding support |
| `read_media_file` | Read image/audio as base64 |
| `read_multiple_files` | Read multiple files simultaneously |
| `write_file` | Create or overwrite file |
| `edit_file` | Make line-based edits to text file |
| `create_directory` | Create directory |
| `list_directory` | List directory contents |
| `list_directory_with_sizes` | List with file sizes |
| `directory_tree` | Recursive tree view as JSON |
| `move_file` | Move or rename file |
| `search_files` | Search for files by pattern |
| `get_file_info` | Get file metadata |
| `file_exists` | Check if file exists |

> [!NOTE]
> Filesystem access is restricted to `${WORKING_DIRECTORY}`.

### Web Search Server

Requires `TAVILY_API_KEY`. Provides web search capabilities.

### GitHub Server

Requires `GITHUB_TOKEN`. Provides access to repositories, issues, and pull requests.

---

## Programmatic Usage

```python
import asyncio
from src.core.mcp_manager import get_mcp_manager

async def use_mcp():
    manager = get_mcp_manager()
    
    # Discover tools from a server
    tools = await manager.discover_tools("filesystem")
    
    # Call a tool
    result = await manager.call_tool(
        "filesystem",
        "read_file",
        {"path": "data/sample.csv"}
    )
    
    # Cleanup
    await manager.close_all()

asyncio.run(use_mcp())
```

---

## Security Considerations

> [!WARNING]
> MCP services have powerful system access capabilities. Ensure:
> - Only enable necessary services
> - Securely store API tokens
> - Limit file system access scope via `WORKING_DIRECTORY`

---

## Related Documentation
- [Quick Start](QUICKSTART.md)
- [Agent Configuration Reference](AGENT_CONFIG.md)
- [Tool Configuration](TOOL_CONFIG.md)

