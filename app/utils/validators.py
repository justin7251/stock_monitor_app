import re
from decimal import Decimal

def validate_stock_symbol(symbol):
    """
    Validates stock symbol format.
    Must be 1-5 uppercase letters.
    """
    # Common symbol patterns
    patterns = [
        (r'^[A-Za-z]{1,5}$', lambda x: x.upper()),  # Regular stocks: AAPL, MSFT
        (r'^[A-Za-z]{1,5}=F$', lambda x: x.upper()),  # Futures: NG=F, CL=F
        (r'^[A-Za-z]{1,5}\.[A-Z]{1,2}$', lambda x: x.upper()),  # International: 600519.SS
        (r'^\^[A-Za-z]{1,10}$', lambda x: x.upper()),  # Indices: ^GSPC, ^DJI
        (r'^[A-Za-z]{1,5}-[A-Za-z]{1,5}$', lambda x: x.upper()),  # Currency pairs: EUR-USD
    ]
    
    for pattern, formatter in patterns:
        if re.match(pattern, symbol):
            return formatter(symbol), True
    
    return None, False

def validate_name(name):
    """
    Validates name.
    Must be 1-100 characters long and contain only letters, numbers, spaces, and basic punctuation.
    """
    if not name:
        raise ValueError("Name is required")
    
    if not re.match(r'^[A-Za-z0-9\s\.,&\'-]{1,100}$', name):
        raise ValueError("Invalid Name format")
    
    if len(name) > 100:
        raise ValueError("Name must be less than 100 characters")    
    return True

def validate_price(price):
    """
    Validates stock price.
    Must be a positive number with up to 2 decimal places.
    """
    try:
        price_decimal = Decimal(str(price))
        
        if price_decimal <= 0:
            raise ValueError("Price must be greater than 0")
        
        if abs(price_decimal.as_tuple().exponent) > 2:
            raise ValueError("Price can only have up to 2 decimal places")
        
        return True
    except (TypeError, ValueError, decimal.InvalidOperation):
        raise ValueError("Invalid price format") 