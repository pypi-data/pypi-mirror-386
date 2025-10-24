import os
from mcp.server.fastmcp import FastMCP
import httpx
import json
from typing import Optional, Dict, Any
from models import BookingForm, Location

# Create an MCP server
mcp = FastMCP("Demo")

def get_api_key() -> str:
    """Get API key from environment variable"""
    api_key = os.getenv("ONCEHUB_API_KEY")
    if not api_key:
        raise ValueError("ONCEHUB_API_KEY environment variable is required. Please set it during integration.")
    return api_key

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def get_booking_time_slots(
    calendar_id: str,
    base_url: str = "https://heisenbergapi.staticso2.com",
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Get ALL available time slots for a booking calendar.
    
    Args:
        calendar_id: The booking calendar ID
        base_url: Base URL of the booking API
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Dictionary containing booking slots information
    """
    try:
        # Get API key from environment
        api_key = get_api_key()
        
        # Construct the endpoint URL
        url = f"{base_url.rstrip('/')}/v2/booking-calendars/{calendar_id}/time-slots"
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "API-key": api_key
        }
        
        # Make the HTTP request
        with httpx.Client() as client:
            response = client.get(
                url=url,
                headers=headers,
                timeout=timeout
            )
        
        # Parse response (same as before)
        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "url": url,
            "calendar_id": calendar_id
        }
        
        if response.status_code == 200:
            try:
                time_slots = response.json()
                result["time_slots"] = time_slots
                result["total_slots"] = len(time_slots) if isinstance(time_slots, list) else 0
                
                # Add metadata
                if isinstance(time_slots, list) and time_slots:
                    location_type_counts = {}
                    earliest_slot = None
                    latest_slot = None
                    
                    for slot in time_slots:
                        start_time = slot.get("start_time")
                        if start_time:
                            if earliest_slot is None or start_time < earliest_slot:
                                earliest_slot = start_time
                            if latest_slot is None or start_time > latest_slot:
                                latest_slot = start_time
                        
                        locations = slot.get("locations", [])
                        for location in locations:
                            loc_type = location.get("type", "unknown")
                            location_type_counts[loc_type] = location_type_counts.get(loc_type, 0) + 1
                    
                    result["metadata"] = {
                        "earliest_slot": earliest_slot,
                        "latest_slot": latest_slot,
                        "location_type_counts": location_type_counts
                    }
                    
            except json.JSONDecodeError:
                result["time_slots"] = response.text
                result["error"] = "Response is not valid JSON"
                result["total_slots"] = 0
                
        else:
            try:
                error_data = response.json()
                result["error"] = error_data.get("message", f"HTTP {response.status_code}")
                result["error_details"] = error_data
            except json.JSONDecodeError:
                result["error"] = f"HTTP {response.status_code}: {response.text}"
        
        return result
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "user_friendly_error": "API key not configured. Please set ONCEHUB_API_KEY environment variable.",
            "status_code": None,
            "calendar_id": calendar_id
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": f"Request timed out after {timeout} seconds",
            "status_code": None,
            "calendar_id": calendar_id
        }
    except httpx.RequestError as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "status_code": None,
            "calendar_id": calendar_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "status_code": None,
            "calendar_id": calendar_id
        }

@mcp.tool()
def schedule_meeting(
    calendar_id: str,
    start_time: str,
    guest_time_zone: str,
    guest_name: str,
    guest_email: str,
    guest_phone: Optional[str] = None,
    location_type: Optional[str] = None,
    location_value: Optional[str] = None,
    string_custom_fields: Optional[list] = None,
    array_custom_fields: Optional[list] = None,
    base_url: str = "https://heisenbergapi.staticso2.com",
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Schedule a meeting in a specified time slot.
    
    Args:
        calendar_id: ID of the booking calendar
        start_time: The date and time of the time slot (ISO format)
        guest_time_zone: The guest's timezone in IANA format
        guest_name: Guest's full name
        guest_email: Guest's email address
        guest_phone: Guest's phone number (optional)
        location_type: Type of location ("physical", "virtual", or "phone")
        location_value: Location details
        string_custom_fields: Custom string fields as list
        array_custom_fields: Custom array fields as list
        base_url: Base URL of the booking API
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with booking results
    """
    try:
        # Get API key from environment
        api_key = get_api_key()
        
        # Construct the endpoint URL
        url = f"{base_url.rstrip('/')}/v2/booking-calendars/{calendar_id}/schedule"
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "API-key": api_key
        }
        
        # Create BookingForm
        booking_form = BookingForm(
            name=guest_name,
            email=guest_email,
            phone=guest_phone,
            string_custom_fields=string_custom_fields or [],
            array_custom_fields=array_custom_fields or []
        )
        
        # Prepare the booking payload
        booking_data = {
            "start_time": start_time,
            "guest_time_zone": guest_time_zone,
            "booking_form": booking_form.to_dict()
        }
        
        # Add location details if provided
        if location_type and location_value:
            booking_data["location_type"] = location_type
            booking_data["location_value"] = location_value
        
        # Make the HTTP request
        with httpx.Client() as client:
            response = client.post(
                url=url,
                json=booking_data,
                headers=headers,
                timeout=timeout
            )
        
        # Parse response
        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "url": url,
            "calendar_id": calendar_id,
            "booking_request": booking_data
        }
        
        if response.status_code == 200:
            try:
                booking_response = response.json()
                result["booking_id"] = booking_response.get("id")
                result["meeting_details"] = booking_response
                
                # Add confirmation details
                result["confirmation"] = {
                    "guest_name": guest_name,
                    "guest_email": guest_email,
                    "guest_phone": guest_phone,
                    "scheduled_time": start_time,
                    "timezone": guest_time_zone,
                    "location_type": location_type,
                    "location_value": location_value,
                    "booking_id": booking_response.get("id")
                }
                    
            except json.JSONDecodeError:
                result["meeting_details"] = response.text
                result["error"] = "Response is not valid JSON"
                
        else:
            try:
                error_data = response.json()
                result["error"] = error_data.get("message", f"HTTP {response.status_code}")
                result["error_details"] = error_data
                
                if response.status_code == 400:
                    result["user_friendly_error"] = "Invalid booking details. Please check the time slot and guest information."
                elif response.status_code == 401:
                    result["user_friendly_error"] = "Authentication failed. Please check if the API key is valid."
                elif response.status_code == 404:
                    result["user_friendly_error"] = f"Calendar '{calendar_id}' not found."
                elif response.status_code >= 500:
                    result["user_friendly_error"] = "Server error occurred. Please try again later."
                    
            except json.JSONDecodeError:
                result["error"] = f"HTTP {response.status_code}: {response.text}"
        
        return result
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "user_friendly_error": "API key not configured. Please set ONCEHUB_API_KEY environment variable.",
            "status_code": None,
            "calendar_id": calendar_id
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": f"Request timed out after {timeout} seconds",
            "user_friendly_error": "The booking request timed out. Please try again.",
            "status_code": None,
            "calendar_id": calendar_id
        }
    except httpx.RequestError as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "user_friendly_error": "Failed to connect to the booking service.",
            "status_code": None,
            "calendar_id": calendar_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "user_friendly_error": f"An unexpected error occurred: {str(e)}",
            "status_code": None,
            "calendar_id": calendar_id
        }

if __name__ == "__main__":
    mcp.run()