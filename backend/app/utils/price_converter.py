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
    
    # If the price is already in THB (contains '฿', '฿', or 'บาท')
    # Return it as is, but maybe clean it up a bit
    if any(th_symbol in price_str for th_symbol in ["฿", "baht", "บาท"]):
        # If it's something like "฿1,799.00", keep it as is or format slightly
        return price_str.replace("Baht", "บาท").strip()

    # Extract numbers from the string (e.g., "$59.99" -> 59.99)
    # Remove commas first to simplify regex
    clean_price = price_str.replace(',', '')
    match = re.search(r"(\d+\.?\d*)", clean_price)
    if match:
        try:
            val = float(match.group(1))
            
            # If the value is quite large and no currency symbol was found, 
            # it might already be THB (e.g., "1799" without symbol)
            # But let's stick to the USD to THB conversion if no THB markers are present
            
            thb_value = val * exchange_rate
            
            if thb_value == 0:
                return "เล่นฟรี"
            
            return f"{thb_value:,.2f} บาท"
        except ValueError:
            return price_str
            
    return price_str
