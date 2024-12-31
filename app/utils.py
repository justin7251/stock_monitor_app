def validate_stock_symbol(symbol):
    """Validate stock symbol."""
    if not isinstance(symbol, str):
        raise ValueError("Stock symbol must be a string.")
    if len(symbol) < 1 or len(symbol) > 10:
        raise ValueError("Stock symbol must be between 1 and 10 characters.")
    if not symbol.isalnum():
        raise ValueError("Stock symbol must be alphanumeric.")
    return True

def validate_name(name):
    if not isinstance(name, str):
        raise ValueError("Name must be a string.")
    if len(name) < 1 or len(name) > 100:
        raise ValueError("Name must be between 1 and 100 characters.")
    return True

def validate_price(price):
    if not isinstance(price, (int, float)):
        raise ValueError("Price must be a number.")
    if price < 0:
        raise ValueError("Price must be a non-negative number.")
    return True
