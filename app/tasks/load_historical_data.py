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

logger = logging.getLogger(__name__)

def load_historical_data(days=365*10):  # 10 years by default
    app = create_app()
    
    with app.app_context():
        try:
            stocks = Stock.query.all()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            for stock in stocks:
                try:
                    logger.info(f"Loading historical data for {stock.symbol}")
                    ticker = yf.Ticker(stock.symbol)
                    hist = ticker.history(start=start_date, end=end_date)
                    
                    for index, row in hist.iterrows():
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
                    
                    # Commit per stock to avoid huge transactions
                    db.session.commit()
                    logger.info(f"Loaded historical data for {stock.symbol}")
                    
                except Exception as e:
                    logger.error(f"Error loading history for {stock.symbol}: {str(e)}")
                    db.session.rollback()
                    continue
                
        except Exception as e:
            logger.error(f"Error in load_historical_data: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    load_historical_data() 