"""
Phone number validation and formatting utilities for US phone numbers.
"""

import re


def format_us_phone(phone: str) -> str | None:
    """
    Validates and formats US phone numbers.
    
    - Strips non-numeric characters: (, ), +, -, spaces, dots
    - Handles 11-digit numbers starting with 1 (removes leading 1)
    - Returns 10-digit number or None if invalid
    
    Args:
        phone: The phone number string to validate and format
        
    Returns:
        A 10-digit phone number string, or None if invalid
        
    Examples:
        >>> format_us_phone("(555) 123-4567")
        '5551234567'
        >>> format_us_phone("+1-555-123-4567")
        '5551234567'
        >>> format_us_phone("15551234567")
        '5551234567'
        >>> format_us_phone("555.123.4567")
        '5551234567'
        >>> format_us_phone("123")  # Too short
        None
    """
    if not phone:
        return None
    
    # Strip all non-numeric characters
    digits = re.sub(r'\D', '', phone)
    
    # Handle 11-digit numbers starting with 1 (US country code)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    
    # Valid US phone number should be exactly 10 digits
    if len(digits) != 10:
        return None
    
    return digits


def is_valid_us_phone(phone: str) -> bool:
    """
    Checks if a phone number is a valid US phone number.
    
    Args:
        phone: The phone number string to validate
        
    Returns:
        True if valid, False otherwise
    """
    return format_us_phone(phone) is not None
