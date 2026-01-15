"""
Date utility functions
Provides date formatting and conversion utilities
"""
from datetime import datetime
from typing import Optional


def format_thai_date(date_string: str) -> str:
    """
    Convert date string to Thai Buddhist calendar format
    
    Args:
        date_string: Date string in format "YYYY-MM-DD HH:MM:SS"
        
    Returns:
        Formatted Thai date string (e.g., "15 ธันวาคม 2567")
    """
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        thai_months = [
            'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
            'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
        ]
        day = date_obj.day
        month = thai_months[date_obj.month - 1]
        year = date_obj.year + 543  # Convert to Buddhist year
        return f"{day} {month} {year}"
    except Exception:
        return date_string


def format_iso_date(date_string: str) -> Optional[str]:
    """
    Convert date string to ISO format
    
    Args:
        date_string: Date string in various formats
        
    Returns:
        ISO formatted date string or None if parsing fails
    """
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        return date_obj.isoformat()
    except Exception:
        return None
