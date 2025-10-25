# awslabs.qbusiness-anonymous-mcp-server

An MCP server for awslaus.quusiness anonymous mcp server operations and management

## Installation

Install from PyPI:
```bash
pip install awslabs.qbusiness-anonymous-mcp-server
```

Or use with uvx:
```bash
uvx awslabs.qbusiness-anonymous-mcp-server
```

## Usage

Run the server:
```bash
awslabs.qbusiness-anonymous-mcp-server
```

## MCP Configuration

Add to your MCP client settings:

```json
{
  "mcpServers": {
    "awslabs.qbusiness-anonymous-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.qbusiness-anonymous-mcp-server"]
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

https://github.com/sicks3c/awslabs.qbusiness-anonymous-mcp-server
