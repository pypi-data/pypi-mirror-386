#!/usr/bin/env python3
"""
Demo MCP Server - Math and Booking Tools

A Model Context Protocol server that provides:
- Math operations (addition)
- Booking calendar integration
"""

import asyncio
import json
import sys
from typing import Any, Sequence
import logging

from mcp import types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import your existing tools
from main import add, get_booking_time_slots, schedule_meeting

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

# Create server instance
server = Server("mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="add",
            description="Add two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "First number to add"},
                    "b": {"type": "integer", "description": "Second number to add"}
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="get_booking_time_slots",
            description="Get all available time slots for a booking calendar (API key configured via environment)",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "The booking calendar ID"},
                    "base_url": {"type": "string", "description": "Base URL of the booking API", "default": "https://heisenbergapi.staticso2.com"},
                    "timeout": {"type": "integer", "description": "Request timeout in seconds", "default": 30}
                },
                "required": ["calendar_id"]
            }
        ),
        types.Tool(
            name="schedule_meeting",
            description="Schedule a meeting in a specified time slot (API key configured via environment)",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "ID of the booking calendar"},
                    "start_time": {"type": "string", "format": "date-time", "description": "The date and time of the time slot (ISO format or Unix timestamp)"},
                    "guest_time_zone": {"type": "string", "description": "The guest's timezone in IANA format (e.g., 'America/New_York')"},
                    "guest_name": {"type": "string", "description": "Guest's full name"},
                    "guest_email": {"type": "string", "format": "email", "description": "Guest's email address"},
                    "guest_phone": {"type": "string", "description": "Guest's phone number (optional)"},
                    "location_type": {"type": "string", "enum": ["physical", "virtual", "phone"], "description": "Type of location for the meeting"},
                    "location_value": {"type": "string", "description": "For virtual: 'google_meet', etc. For phone: phone number. For physical: address ID"},
                    "string_custom_fields": {"type": "array", "items": {"type": "string"}, "description": "Custom string fields as array"},
                    "array_custom_fields": {"type": "array", "items": {"type": "string"}, "description": "Custom array fields"},
                    "base_url": {"type": "string", "description": "Base URL of the booking API", "default": "https://heisenbergapi.staticso2.com"},
                    "timeout": {"type": "integer", "description": "Request timeout in seconds", "default": 30}
                },
                "required": ["calendar_id", "start_time", "guest_time_zone", "guest_name", "guest_email"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool execution requests."""
    try:
        if name == "add":
            if "a" not in arguments or "b" not in arguments:
                raise ValueError("Missing required arguments 'a' and 'b'")
            
            result = add(arguments["a"], arguments["b"])
            return [types.TextContent(type="text", text=f"The sum of {arguments['a']} and {arguments['b']} is {result}")]
        
        elif name == "get_booking_time_slots":
            if "calendar_id" not in arguments:
                raise ValueError("Missing required argument 'calendar_id'")
            
            result = get_booking_time_slots(
                calendar_id=arguments["calendar_id"],
                base_url=arguments.get("base_url", "https://heisenbergapi.staticso2.com"),
                timeout=arguments.get("timeout", 30)
            )
            
            # Format response (same as before)
            if result.get("success"):
                slots_count = result.get("total_slots", 0)
                response_text = f"✅ Found {slots_count} available time slots for calendar '{arguments['calendar_id']}'."
                # ... rest of formatting
            else:
                response_text = f"❌ Failed to retrieve booking slots: {result.get('user_friendly_error', result.get('error', 'Unknown error'))}"
            
            return [types.TextContent(type="text", text=response_text)]
        
        elif name == "schedule_meeting":
            required_args = ["calendar_id", "start_time", "guest_time_zone", "guest_name", "guest_email"]
            for arg in required_args:
                if arg not in arguments:
                    raise ValueError(f"Missing required argument '{arg}'")
            
            # Convert timestamp if needed
            # converted_start_time = convert_timestamp_if_needed(arguments["start_time"])
            
            result = schedule_meeting(
                calendar_id=arguments["calendar_id"],
                start_time=arguments["start_time"],
                guest_time_zone=arguments["guest_time_zone"],
                guest_name=arguments["guest_name"],
                guest_email=arguments["guest_email"],
                guest_phone=arguments.get("guest_phone"),
                location_type=arguments.get("location_type"),
                location_value=arguments.get("location_value"),
                string_custom_fields=arguments.get("string_custom_fields"),
                array_custom_fields=arguments.get("array_custom_fields"),
                base_url=arguments.get("base_url", "https://heisenbergapi.staticso2.com"),
                timeout=arguments.get("timeout", 30)
            )
            
            # Format response (same as before)
            if result.get("success"):
                response_text = f"✅ Meeting scheduled successfully!"
                response_text += f"\n- Response: {json.dumps(result, indent=2)}"
                # ... rest of formatting
            else:
                response_text = f"❌ Failed to schedule meeting: {result.get('user_friendly_error', result.get('error', 'Unknown error'))}"
            
            return [types.TextContent(type="text", text=response_text)]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return [types.TextContent(type="text", text=f"❌ Error executing {name}: {str(e)}")]

async def main():
    """Main function to run the MCP server."""
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            ),
        )

def run_server():
    """Entry point for the CLI command"""
    try:
        print("🚀 Starting Demo MCP Server...")
        print("📋 Available tools: add, get_booking_time_slots, schedule_meeting")
        print("🔌 Server running in MCP stdio mode")
        print("👋 Press Ctrl+C to stop")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()