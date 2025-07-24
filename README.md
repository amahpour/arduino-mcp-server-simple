# Arduino MCP Server (Simple)

A simple Model Context Protocol (MCP) server that enables AI agents to interact with Arduino boards for development and testing.

## What is this?

This project demonstrates how to create an MCP server that allows AI agents to:
- List available Arduino boards
- Compile Arduino sketches
- Upload sketches to boards
- Send/receive serial messages

## Prerequisites

- Arduino CLI installed and configured
- Python 3.7+
- An Arduino board connected via USB

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure Arduino CLI is installed and configured:
```bash
arduino-cli version
```

## Usage

### Start the MCP Server

```bash
python mcp_arduino.py
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