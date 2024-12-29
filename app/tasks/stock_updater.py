import sys
import os
# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import yfinance as yf
from datetime import datetime, timedelta
from app import create_app
from app.database import db
from app.database.models import Stock, StockHistory, Commodity
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def update_stock_data():
    """Update both current and historical stock data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get all stocks
            stocks = Stock.query.all()
            
            if not stocks:
                logger.info("No stocks found in database")
                return
            
            for stock in stocks:
                try:
                    # Get stock info from yfinance
                    ticker = yf.Ticker(stock.symbol)
                    
                    # Update current price
                    current_price = ticker.info.get('regularMarketPrice')
                    if current_price:
                        stock.current_price = current_price
                        stock.last_updated = datetime.utcnow()
                        logger.info(f"Updated current price for {stock.symbol}: ${current_price}")
                    
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
                    continue
            
            # Commit all updates
            db.session.commit()
            logger.info("Stock data update completed")
            
        except Exception as e:
            logger.error(f"Error in update_stock_data: {str(e)}")
            db.session.rollback()

def update_commodity_prices():
    """Update commodity prices"""
    app = create_app()
    
    with app.app_context():
        try:
            commodities = Commodity.query.all()
            
            if not commodities:
                logger.info("No commodities found in database")
                return
            
            for commodity in commodities:
                try:
                    ticker = yf.Ticker(commodity.symbol)
                    current_price = ticker.info.get('regularMarketPrice')
                    
                    if current_price:
                        commodity.current_price = current_price
                        commodity.last_updated = datetime.utcnow()
                        logger.info(f"Updated price for {commodity.name}: ${current_price}")
                    
                except Exception as e:
                    logger.error(f"Error updating {commodity.name}: {str(e)}")
                    continue
            
            db.session.commit()
            logger.info("Commodity price update completed")
            
        except Exception as e:
            logger.error(f"Error in update_commodity_prices: {str(e)}")
            db.session.rollback()

def update_all():
    """Update both stock and commodity data"""
    try:
        update_stock_data()
        update_commodity_prices()
        logger.info("All updates completed successfully")
    except Exception as e:
        logger.error(f"Error in update_all: {str(e)}")

if __name__ == "__main__":
    update_all()
