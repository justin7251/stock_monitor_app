import sys
import os
# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import yfinance as yf
from datetime import datetime, timedelta
from app import create_app
from app.database import db
from app.database.models import Stock, StockHistory
import logging
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/stock_updater.log')
    ]
)
logger = logging.getLogger(__name__)

def update_stock_data():
    """Update both current and historical stock data"""
    logger.info("=" * 80)
    logger.info(f"Stock Updater Starting at {datetime.now()}")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get all stocks
            stocks = Stock.query.all()
            
            if not stocks:
                logger.info("No stocks found in database")
                return
            
            logger.info(f"Found {len(stocks)} stocks in database")
            for stock in stocks:
                try:
                    logger.info(f"Processing {stock.symbol} - Last updated: {stock.last_updated}")
                    
                    # Get stock info from yfinance
                    ticker = yf.Ticker(stock.symbol)
                    
                    # Try different price fields
                    info = ticker.info
                    logger.info(f"Raw ticker info for {stock.symbol}: {info}")
                    
                    current_price = None
                    price_fields = [
                        'regularMarketPrice',
                        'currentPrice',
                        'lastPrice',
                        'previousClose',
                        'ask',
                        'bid'
                    ]
                    
                    for field in price_fields:
                        current_price = info.get(field)
                        if current_price:
                            logger.info(f"Found price for {stock.symbol} using field '{field}': ${current_price}")
                            break
                    
                    if current_price:
                        stock.current_price = current_price
                        stock.last_updated = datetime.utcnow()
                        logger.info(f"Updated current price for {stock.symbol}: ${current_price}")
                    else:
                        # Try getting price from recent history
                        hist = ticker.history(period='1d')
                        if not hist.empty:
                            current_price = float(hist['Close'].iloc[-1])
                            stock.current_price = current_price
                            stock.last_updated = datetime.utcnow()
                            logger.info(f"Updated price from history for {stock.symbol}: ${current_price}")
                        else:
                            logger.error(f"Could not get price for {stock.symbol} from any source")
                            continue
                    
                    # Get historical data (1 day by default, adjust period as needed)
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=1)  # Get last 24 hours
                    
                    hist = ticker.history(
                        start=start_date,
                        end=end_date,
                        interval='1h'  # 1-hour intervals
                    )
                    
                    # Store historical data
                    for index, row in hist.iterrows():
                        # Check if we already have this data point
                        existing_history = StockHistory.query.filter_by(
                            stock_id=stock.id,
                            date=index
                        ).first()
                        
                        if not existing_history:
                            history = StockHistory(
                                stock_id=stock.id,
                                date=index,
                                open_price=row['Open'],
                                high_price=row['High'],
                                low_price=row['Low'],
                                close_price=row['Close'],
                                volume=row['Volume']
                            )
                            db.session.add(history)
                            logger.info(f"Added historical data for {stock.symbol} at {index}")
                    
                except Exception as e:
                    logger.error(f"Error updating {stock.symbol}: {str(e)}")
                    logger.error("Traceback:", exc_info=True)
                    continue
            
            # Commit all updates
            db.session.commit()
            logger.info("Stock data update completed successfully")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error in update_stock_data: {str(e)}")
            logger.error("Traceback:", exc_info=True)
            db.session.rollback()

def update_all():
    """Update both stock data"""
    try:
        logger.info("Starting update_all process")
        update_stock_data()
        logger.info("All updates completed successfully")
    except Exception as e:
        logger.error(f"Error in update_all: {str(e)}")
        logger.error("Traceback:", exc_info=True)

if __name__ == "__main__":
    logger.info(f"Stock Updater Script Starting - Python Path: {sys.path}")
    update_all()
