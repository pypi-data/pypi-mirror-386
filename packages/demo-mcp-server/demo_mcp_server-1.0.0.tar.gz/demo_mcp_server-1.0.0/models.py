from typing import Optional, List
from dataclasses import dataclass, field

@dataclass
class Location:
    """Location details for a meeting"""
    type: str  # "physical", "virtual", or "phone"
    value: str  # For virtual: "google_meet", etc. For phone: phone number. For physical: address ID
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API requests"""
        return {
            "type": self.type,
            "value": self.value
        }

@dataclass
class BookingForm:
    """Guest information for booking"""
    name: str
    email: str
    phone: Optional[str] = None  # Changed from ""
    string_custom_fields: Optional[List[str]] = field(default_factory=list)  # Fixed type
    array_custom_fields: Optional[List[str]] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API requests"""
        result = {
            "name": self.name,
            "email": self.email
        }
        
        if self.phone:
            result["phone"] = self.phone
        if self.string_custom_fields:
            result["string_custom_fields"] = self.string_custom_fields
        if self.array_custom_fields:
            result["array_custom_fields"] = self.array_custom_fields
            
        return result