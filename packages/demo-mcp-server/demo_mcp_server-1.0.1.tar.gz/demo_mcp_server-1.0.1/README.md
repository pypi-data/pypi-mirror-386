# Demo MCP Server

A Model Context Protocol (MCP) server providing math operations and OnceHub booking calendar integration.

[![PyPI version](https://badge.fury.io/py/test-mcp-server.svg)](https://badge.fury.io/py/test-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

### 🧮 Math Tools
- **add**: Add two numbers together with input validation

### 📅 Booking Tools
- **get_booking_time_slots**: Retrieve all available time slots from OnceHub booking calendars
- **schedule_meeting**: Book meetings with participant details and location preferences

## Installation

```bash
pip install test-mcp-server
```

Or with uv:
```bash
uv add test-mcp-server
```

## Configuration

### API Key Setup

The OnceHub API key is configured once during integration:

#### For Claude Desktop:

```json
{
  "mcpServers": {
    "test-mcp-server": {
      "command": "test-mcp-server",
      "env": {
        "ONCEHUB_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### For Command Line:

```bash
# Set environment variable
export ONCEHUB_API_KEY="your_api_key_here"

# Run server
test-mcp-server
```

#### For Windows:

```cmd
set ONCEHUB_API_KEY=your_api_key_here
test-mcp-server
```

## Usage

Once configured, you can use the tools without specifying the API key:

```
# Get available slots
"Get booking slots for calendar 'cal_123'"

# Schedule meeting  
"Schedule a meeting for calendar 'cal_123' on 2024-01-15 at 2:30 PM EST for John Doe (john@example.com)"
```

## Development

```bash
git clone https://github.com/yourusername/test-mcp-server.git
cd test-mcp-server
uv sync
```

## License

MIT License - see [LICENSE](LICENSE) file for details.