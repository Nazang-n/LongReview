import re

def convert_usd_to_thb(price_str: str, exchange_rate: float = 35.0) -> str:
    """
    Converts a price string (e.g., "$59.99", "Free to Play") to THB.
    
    Args:
        price_str: The price string from Steam (usually in USD or 'Free').
        exchange_rate: The USD to THB exchange rate.
        
    Returns:
        A formatted THB price string or the original if it's "Free".
    """
    if not price_str:
        return ""
    
    # Handle free games
    lower_price = price_str.lower()
    if any(free_word in lower_price for free_word in ["free", "ฟรี"]):
        return "เล่นฟรี"
    
    # Extract numbers from the string (e.g., "$1,200.00" -> 1200.00)
    # Remove commas first to simplify regex
    clean_price = price_str.replace(',', '')
    match = re.search(r"(\d+\.?\d*)", clean_price)
    if match:
        try:
            usd_value = float(match.group(1))
            thb_value = usd_value * exchange_rate
            
            # Round and format as currency
            # Using Thai Baht symbol or "บาท"
            if thb_value == 0:
                return "เล่นฟรี"
            
            return f"{thb_value:,.2f} บาท"
        except ValueError:
            return price_str
            
    return price_str
