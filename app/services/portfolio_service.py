from datetime import datetime
from app.database.models import Portfolio, Holding, Stock, HoldingType, db
import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class PortfolioService:
    def __init__(self):
        self.db = db

    def create_user_portfolio(self, user_id, name, type=HoldingType.DIRECT):
        """Create a new portfolio or direct holding container"""
        try:
            portfolio = Portfolio(
                user_id=user_id,
                name=name,
                type=type
            )
            self.db.session.add(portfolio)
            self.db.session.commit()
            return True, portfolio
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error creating portfolio: {str(e)}")
            return False, str(e)

    def add_holding(self, portfolio_id, stock_symbol, quantity, price):
        """Add a new holding to a portfolio"""
        try:
            # Get or create stock
            stock = Stock.query.filter_by(symbol=stock_symbol).first()
            if not stock:
                stock = Stock(
                    symbol=stock_symbol,
                    name=stock_symbol,  # You might want to fetch the actual name
                    type='stock'
                )
                self.db.session.add(stock)
            
            holding = Holding(
                portfolio_id=portfolio_id,
                stock_id=stock.id,
                quantity=quantity,
                purchase_price=price,
                average_price=price,
                total_investment=quantity * price
            )
            self.db.session.add(holding)
            self.db.session.commit()
            
            return True, holding
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error adding holding: {str(e)}")
            return False, str(e)

    def get_portfolio_value(self, portfolio_id):
        """Calculate current portfolio value"""
        try:
            portfolio = Portfolio.query.get(portfolio_id)
            if not portfolio:
                return 0
                
            total_value = sum(
                holding.quantity * holding.stock.current_price 
                for holding in portfolio.holdings
            )
            
            return total_value
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {str(e)}")
            return 0

    def get_stock_historical_data(self, symbol, period='1y'):
        """Get historical data for a stock"""
        try:
            stock = yf.Ticker(symbol)
            history = stock.history(period=period)
            
            if history.empty:
                return None
                
            # Convert to required format
            data = pd.DataFrame({
                'date': history.index,
                'open_price': history['Open'],
                'high_price': history['High'],
                'low_price': history['Low'],
                'close_price': history['Close'],
                'volume': history['Volume']
            })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None

    def get_user_holdings(self, user_id):
        """Get all user's holdings across portfolios"""
        try:
            portfolios = Portfolio.query.filter_by(user_id=user_id).all()
            
            holdings_data = []
            for portfolio in portfolios:
                for holding in portfolio.holdings:
                    holdings_data.append({
                        'portfolio_name': portfolio.name,
                        'portfolio_type': portfolio.type.value,
                        'symbol': holding.stock.symbol,
                        'quantity': holding.quantity,
                        'purchase_price': holding.purchase_price,
                        'current_price': holding.stock.current_price,
                        'total_value': holding.quantity * holding.stock.current_price,
                        'gain_loss': (holding.stock.current_price - holding.purchase_price) * holding.quantity
                    })
            
            return holdings_data
            
        except Exception as e:
            logger.error(f"Error fetching user holdings: {str(e)}")
            return [] 