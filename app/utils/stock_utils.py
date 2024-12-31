import yfinance as yf
from datetime import datetime, timedelta
from app.database.models import Stock, StockHistory, db

def get_or_update_stock(symbol, force_update=False):
    """
    Get stock from database or fetch from yfinance if not exists or needs update
    Returns tuple (stock, success, error_message)
    """
    try:
        # Validate and format symbol
        formatted_symbol, is_valid = is_valid_symbol(symbol)
        if not is_valid:
            return None, False, f"Invalid symbol format: {symbol}"
        
        symbol = formatted_symbol
        stock = Stock.query.filter_by(symbol=symbol).first()
        now = datetime.utcnow()

        # Check if we need to update the stock data
        needs_update = (
            force_update or
            not stock or
            not stock.last_updated or
            (now - stock.last_updated) > timedelta(minutes=15)
        )

        if needs_update:
            # Fetch from yfinance
            ticker = yf.Ticker(symbol)
            
            # Get ticker info
            info = ticker.info
            if not info:
                return None, False, "Unable to fetch stock data"

            # Get current price and other market data
            current_price = info.get('regularMarketPrice') or info.get('currentPrice')
            if not current_price:
                return None, False, "Unable to get current price"

            if not stock:
                # Create new stock
                stock = Stock(
                    symbol=symbol,
                    name=info.get('longName') or info.get('shortName', symbol),
                    type='stock',
                    current_price=current_price,
                    market_cap=info.get('marketCap', 0),
                    volume=info.get('volume', 0),
                    avg_volume=info.get('averageVolume', 0)
                )
                db.session.add(stock)
                db.session.flush()  # Get the stock.id before adding history

            else:
                # Update existing stock
                stock.current_price = current_price
                stock.name = info.get('longName') or info.get('shortName', stock.name)
                stock.market_cap = info.get('marketCap', 0)
                stock.volume = info.get('volume', 0)
                stock.avg_volume = info.get('averageVolume', 0)

            # Get historical data
            try:
                # Get 1 month of daily data
                hist = ticker.history(period='1mo', interval='1d')
                
                if not hist.empty:
                    # Delete existing history for this period to avoid duplicates
                    start_date = hist.index.min()
                    StockHistory.query.filter(
                        StockHistory.stock_id == stock.id,
                        StockHistory.date >= start_date
                    ).delete()

                    # Add new history records
                    for date, row in hist.iterrows():
                        history = StockHistory(
                            stock_id=stock.id,
                            date=date,
                            open_price=float(row['Open']),
                            high_price=float(row['High']),
                            low_price=float(row['Low']),
                            close_price=float(row['Close']),
                            volume=int(row['Volume']),
                            adjusted_close=float(row['Close'])
                        )
                        db.session.add(history)

            except Exception as hist_error:
                print(f"Error fetching historical data: {hist_error}")
                # Add at least today's data point
                history = StockHistory(
                    stock_id=stock.id,
                    date=now,
                    close_price=current_price,
                    volume=info.get('volume', 0),
                    adjusted_close=current_price
                )
                db.session.add(history)

            stock.last_updated = now
            db.session.commit()

        return stock, True, None

    except Exception as e:
        db.session.rollback()
        print(f"Error updating stock {symbol}: {str(e)}")
        return None, False, str(e)

def backfill_stock_history(symbol, period='1y'):
    """
    Backfill historical data for a stock
    Returns tuple (success, error_message)
    """
    try:
        stock = Stock.query.filter_by(symbol=symbol).first()
        if not stock:
            return False, "Stock not found"

        # Fetch historical data
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return False, "No historical data available"

        # Delete existing history to avoid duplicates
        StockHistory.query.filter_by(stock_id=stock.id).delete()

        # Add new history records
        for date, row in hist.iterrows():
            history = StockHistory(
                stock_id=stock.id,
                date=date,
                open_price=float(row['Open']),
                high_price=float(row['High']),
                low_price=float(row['Low']),
                close_price=float(row['Close']),
                volume=int(row['Volume']),
                adjusted_close=float(row['Close'])
            )
            db.session.add(history)

        db.session.commit()
        return True, None

    except Exception as e:
        db.session.rollback()
        print(f"Error backfilling history for {symbol}: {str(e)}")
        return False, str(e)

def get_stock_history(symbol, period='1mo', interval='1d'):
    """
    Get historical data for a stock
    Returns tuple (history_data, success, error_message)
    """
    try:
        stock = Stock.query.filter_by(symbol=symbol).first()
        if not stock:
            return None, False, "Stock not found"

        # Try to get from database first
        if interval == '1d':
            history = StockHistory.query.filter_by(stock_id=stock.id).order_by(StockHistory.date).all()
            if history:
                history_data = {
                    'dates': [h.date.strftime('%Y-%m-%d %H:%M:%S') for h in history],
                    'open': [h.open_price for h in history if h.open_price],
                    'high': [h.high_price for h in history if h.high_price],
                    'low': [h.low_price for h in history if h.low_price],
                    'close': [h.close_price for h in history],
                    'volume': [h.volume for h in history],
                    'adjusted_close': [h.adjusted_close for h in history if h.adjusted_close]
                }
                return history_data, True, None

        # If not in database or different interval needed, fetch from yfinance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return None, False, "No historical data available"

        history_data = {
            'dates': hist.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            'open': hist['Open'].round(2).tolist(),
            'high': hist['High'].round(2).tolist(),
            'low': hist['Low'].round(2).tolist(),
            'close': hist['Close'].round(2).tolist(),
            'volume': hist['Volume'].tolist(),
            'adjusted_close': hist['Close'].round(2).tolist()
        }

        return history_data, True, None

    except Exception as e:
        print(f"Error fetching history for {symbol}: {str(e)}")
        return None, False, str(e) 