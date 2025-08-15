# Arduino MCP Server (Simple)

A simple Model Context Protocol (MCP) server that enables AI agents to interact with Arduino boards for development and testing.

> **Note:** This project was developed and tested on macOS with Cursor IDE. While it should work on other platforms, some paths and configurations may need adjustment for Windows or Linux systems.

## What is this?

This project demonstrates how to create an MCP server that allows AI agents to:
- List available Arduino boards
- Compile Arduino sketches
- Upload sketches to boards
- Send/receive serial messages

## Prerequisites

- Arduino CLI installed and configured
- Python 3.10+
- An Arduino board connected via USB

## Installation

1. Install the package directly from GitHub:
```bash
# Install from main branch
pip install git+https://github.com/amahpour/arduino-mcp-server-simple.git

# Or install from the specific MCP-enabled branch
pip install git+https://github.com/amahpour/arduino-mcp-server-simple.git@codex/update-pyproject.toml-for-mcp-tool

# For development (editable install)
git clone https://github.com/amahpour/arduino-mcp-server-simple.git
cd arduino-mcp-server-simple
pip install -e .
```

2. Make sure Arduino CLI is installed and configured:
```bash
arduino-cli version
```

## Usage

### Start the MCP Server

After installation, you can start the server in multiple ways:

```bash
# Using the console script (recommended)
arduino-mcp-tool

# Or using module execution
python -m arduino_mcp_tool
```

For development or local testing:
```bash
# From the repository directory
python -m arduino_mcp_tool
```

### Package Structure

The project is organized as a proper Python package:

```
arduino_mcp_tool/
├── __init__.py      # Main MCP server implementation
└── __main__.py      # Entry point for python -m execution
```

### Cursor Integration

This project includes a `.cursor/mcp.json` configuration file that allows Cursor users to integrate the Arduino MCP server directly into their development environment.

The configuration automatically registers the Arduino MCP server, giving you access to Arduino development tools directly within Cursor's AI features. You can:

- Ask Cursor to compile and upload Arduino sketches
- Test serial communication through the AI interface
- Get help with Arduino development workflows

The MCP server will be available as soon as you open this project in Cursor.

### Available Tools

- `list_ports()` - List all available USB/serial ports
- `ping()` - Simple health check
- `compile(sketch, fqbn=None, port=None)` - Compile an Arduino sketch
- `upload(sketch, port, fqbn=None)` - Upload a sketch to a board
- `serial_send(port, baud, message, timeout=2)` - Send a message over serial and read response

### Example Workflow

1. List available ports to find your Arduino
2. Compile your sketch (auto-detects board type)
3. Upload to the board
4. Send test messages over serial

## Example Sketch

The included `sketches/echo_serial/echo_serial.ino` is a simple echo server that:
- Receives serial input
- Echoes it back with a prefix
- Perfect for testing the MCP server functionality

## Integration

This MCP server can be integrated with any MCP-compatible AI agent or development environment to enable automated Arduino development workflows.

### MCP Configuration

When using this server with MCP clients, you can configure it as:

```json
{
  "mcpServers": {
    "arduino": {
      "command": "arduino-mcp-tool",
      "args": []
    }
  }
}
```

Or if installed in development mode:

```json
{
  "mcpServers": {
    "arduino": {
      "command": "python",
      "args": ["-m", "arduino_mcp_tool"]
    }
  }
}
```
