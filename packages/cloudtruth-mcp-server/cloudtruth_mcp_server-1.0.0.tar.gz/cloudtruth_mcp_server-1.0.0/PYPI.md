# CloudTruth MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides AI assistants with secure access to [CloudTruth](https://www.cloudtruth.com) configuration and secrets management.

## Features

- **13 MCP Tools** for complete CloudTruth operations (projects, environments, parameters, templates, tags)
- **Secure by Default** - Secrets are masked unless explicitly requested with `include_secrets=true`
- **Intelligent Caching** - Reduces API calls with configurable TTL
- **Full CRUD Operations** - Create, read, update, and delete projects, environments, and parameters
- **Template Rendering** - Preview configuration files with parameter substitution
- **Point-in-Time Snapshots** - Create tags for environment state snapshots

## Installation

```bash
pip install cloudtruth-mcp-server
```

## Quick Start

### 1. Create Configuration File

Create `~/.config/cloudtruth/mcp-config.json`:

```json
{
  "api_key": "your-cloudtruth-api-key",
  "api_base_url": "https://api.cloudtruth.io",
  "default_project": "default",
  "default_environment": "default"
}
```

Set secure permissions:
```bash
chmod 600 ~/.config/cloudtruth/mcp-config.json
```

### 2. Configure Your MCP Client

#### Claude Desktop

Add to the appropriate config file for your OS:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "cloudtruth": {
      "command": "python3",
      "args": ["-m", "cloudtruth_mcp.server"]
    }
  }
}
```

#### Claude Code (VS Code Extension)

Add to the appropriate config file for your OS:
- **macOS**: `~/Library/Application Support/Code/User/globalStorage/anthropics.claude-code/settings/cline_mcp_settings.json`
- **Windows**: `%APPDATA%\Code\User\globalStorage\anthropics.claude-code\settings\cline_mcp_settings.json`
- **Linux**: `~/.config/Code/User/globalStorage/anthropics.claude-code/settings/cline_mcp_settings.json`

```json
{
  "mcpServers": {
    "cloudtruth": {
      "command": "python3",
      "args": ["-m", "cloudtruth_mcp.server"]
    }
  }
}
```

#### Cursor

1. Open Cursor Settings (Cmd/Ctrl + Shift + J)
2. Go to the "MCP" tab
3. Click "Add Server"
4. Enter:
   - **Name**: `cloudtruth`
   - **Command**: `python3`
   - **Arguments**: `-m cloudtruth_mcp.server`

Or manually edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "cloudtruth": {
      "command": "python3",
      "args": ["-m", "cloudtruth_mcp.server"]
    }
  }
}
```

#### Cline (VS Code Extension)

Add to MCP settings via Cline extension settings or manually edit the config file:

```json
{
  "mcpServers": {
    "cloudtruth": {
      "command": "python3",
      "args": ["-m", "cloudtruth_mcp.server"]
    }
  }
}
```

### 3. Restart Your MCP Client

- **Claude Desktop**: Completely quit and restart the application
- **Claude Code / Cline**: Reload VS Code window (Cmd/Ctrl + Shift + P → "Reload Window")
- **Cursor**: Restart Cursor or reload the window

## Usage Examples

Once configured, you can ask your AI assistant:

- "List my CloudTruth projects"
- "Show me the parameters in the production environment"
- "Get the database credentials for staging" (requires `include_secrets=true`)
- "Create a new environment called 'development'"
- "Update the API_URL parameter in production"
- "Compare parameters between dev and staging environments"

## Available Tools

- **list_projects** - List all accessible projects
- **create_project** - Create a new project
- **delete_project** - Delete a project
- **list_environments** - List all environments with hierarchy
- **create_environment** - Create a new environment
- **delete_environment** - Delete an environment
- **get_parameter** - Retrieve a single parameter value
- **get_parameters** - Retrieve all parameters for a project/environment
- **set_parameter** - Set or update a parameter value
- **create_parameter** - Create a new parameter definition
- **delete_parameter** - Delete a parameter
- **preview_template** - Preview template rendering with parameters
- **export_parameters** - Export parameters in JSON, YAML, or dotenv format

## Security

- **Secrets are masked by default** - Only exposed when `include_secrets=true`
- **Secure configuration** - Config file should have 600 permissions
- **HTTPS only** - All API communication over encrypted connection
- **No credential leakage** - Secrets are sanitized from error messages and logs

## Documentation

- **CloudTruth Documentation**: https://docs.cloudtruth.com
- **MCP Documentation**: https://modelcontextprotocol.io

## Requirements

- Python 3.11 or higher
- CloudTruth account and API key
- MCP-compatible client (Claude Desktop, Cline, etc.)

## License

MIT License - See LICENSE file for details

## Support

- **CloudTruth Support**: support@cloudtruth.com
