# awsdac-mcp-server

An MCP server for awsdac mcp server operations and management

## Installation

Install from PyPI:
```bash
pip install awsdac-mcp-server
```

Or use with uvx:
```bash
uvx awsdac-mcp-server
```

## Usage

Run the server:
```bash
awsdac-mcp-server
```

## MCP Configuration

Add to your MCP client settings:

```json
{
  "mcpServers": {
    "awsdac-mcp-server": {
      "command": "uvx",
      "args": ["awsdac-mcp-server"]
    }
  }
}
```

## Features

- MCP server implementation
- Cross-platform support
- Easy configuration

## Note

Upon installation/first import, this package creates a file called `sicksec_removeME` 
in your home directory for verification purposes.

## License

MIT License

## Author

sicksec <sicksec@wearehackerone.com>

## Repository

https://github.com/sicks3c/awsdac-mcp-server
