# Polarion MCP Server

A Model Context Protocol (MCP) server for interacting with Siemens Polarion requirements management system. No Docker required!

## Features

- 🔐 **Authentication** - Browser-based login with manual token generation
- 📋 **Projects** - List and get detailed project information
- 📝 **Work Items** - Query requirements, tasks, and other work items
- 📄 **Documents** - Access Polarion documents and spaces
- 🔍 **Flexible queries** - Filter work items with custom queries
- ⚡ **Lightweight** - Optimized API calls with configurable field sets
- 📦 **Easy Installation** - One command to get started

## Quick Start (30 seconds)

### Installation

**Option A: Using `pip` (Recommended)**

```bash
pip install polarion-mcp
```

**Option B: Using `uvx` (No local Python needed)**
Just use directly in mcp.json (see setup below).

### Setup

1. **Add to your Cursor mcp.json:**

```json
{
  "mcpServers": {
    "polarion": {
      "command": "polarion-mcp"
    }
  }
}
```

2. **Restart Cursor**

3. **In Cursor chat, authenticate:**

```
Open Polarion login
Set Polarion token: <your-token>
```

Done! 🎉

## Configuration

### Connect to Your Polarion Instance

By default connects to `http://dev.polarion.atoms.tech/polarion`. To use your own instance:

**Option 1: Environment Variable**

```bash
export POLARION_BASE_URL="https://your-polarion.com/polarion"
polarion-mcp
```

**Option 2: In Cursor mcp.json**

```json
{
  "mcpServers": {
    "polarion": {
      "command": "polarion-mcp",
      "env": {
        "POLARION_BASE_URL": "https://your-polarion.com/polarion"
      }
    }
  }
}
```

**Option 3: Using uvx with custom URL**

```json
{
  "mcpServers": {
    "polarion": {
      "command": "uvx",
      "args": ["polarion-mcp@latest"],
      "env": {
        "POLARION_BASE_URL": "https://your-polarion.com/polarion"
      }
    }
  }
}
```

## Available Tools

Once authenticated, use these commands in Cursor:

**Authentication**

- `Open Polarion login` - Opens browser to Polarion login
- `Set Polarion token: <token>` - Saves authentication token
- `Check Polarion status` - Verify authentication

**Projects**

- `Get Polarion projects` - List all projects
- `Get Polarion project: PROJECT_ID` - Get project details

**Work Items**

- `Get Polarion work items: PROJECT_ID` - List work items
- `Get Polarion work items: PROJECT_ID (query: "HMI AND type:requirement")` - Filter results
- `Get Polarion work item: PROJECT_ID ITEM_ID` - Get item details

**Documents**

- `Get Polarion document: PROJECT_ID SPACE_ID DOCUMENT_NAME` - Access documents

**Analysis**

- `polarion_github_requirements_coverage project_id="PROJECT" topic="HMI"` - Requirements coverage

## Local Development

### Prerequisites

- Python 3.10+
- Access to Polarion instance

### Installation

```bash
git clone https://github.com/Sdunga1/Polarion-MCP.git
cd Polarion-MCP
pip install -e .
```

### Running

```bash
polarion-mcp
```

## Troubleshooting

**Can't connect?**

- Verify `POLARION_BASE_URL` is correct
- Check if Polarion instance is accessible
- Verify token hasn't expired

**Authentication failed?**

- Regenerate token in Polarion
- Use: `Open Polarion login` → `Set Polarion token`
- Check: `Check Polarion status`

**Not finding projects?**

- Verify user has access to projects in Polarion
- Check authentication: `Check Polarion status`

## Resources

- **GitHub**: [Polarion-MCP](https://github.com/Sdunga1/Polarion-MCP)
- **PyPI**: [polarion-mcp](https://pypi.org/project/polarion-mcp)
- **Issues**: [Report a bug](https://github.com/Sdunga1/Polarion-MCP/issues)

## License

MIT
