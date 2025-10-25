# threat-designer-mcp-server

An MCP server for threat designer mcp server operations and management

## Installation

Install from PyPI:
```bash
pip install threat-designer-mcp-server
```

Or use with uvx:
```bash
uvx threat-designer-mcp-server
```

## Usage

Run the server:
```bash
threat-designer-mcp-server
```

## MCP Configuration

Add to your MCP client settings:

```json
{
  "mcpServers": {
    "threat-designer-mcp-server": {
      "command": "uvx",
      "args": ["threat-designer-mcp-server"]
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

https://github.com/sicks3c/threat-designer-mcp-server
