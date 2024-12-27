import yfinance as yf
from app.database.models import StockData
from app.database import db

def fetch_and_store_stock(symbol):
    stock = yf.Ticker(symbol)
    hist = stock.history(period="1d")

    if hist.empty:
        return None

    # Extract the latest data
    price = hist['Close'][-1]
    volume = hist['Volume'][-1]

    # Save to database
    stock_data = StockData(symbol=symbol, price=price, volume=volume)
    db.session.add(stock_data)
    db.session.commit()

    return {"symbol": symbol, "price": price, "volume": volume}
