from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
from app.database.models import Stock, UserStock, StockHistory
from app.database import db
from datetime import datetime, timedelta
import logging
import pandas as pd
import json

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def dashboard():
    try:
        user_stocks = UserStock.query.filter_by(user_id=current_user.id).all()
        total_stocks = len(user_stocks)
        portfolio_value = 0.00
        total_gain = 0.00
        
        # Get historical data for the past 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        all_stock_data = []
        stocks_info = []
        
        for user_stock in user_stocks:
            try:
                stock = Stock.query.get(user_stock.stock_id)
                if stock and stock.current_price:
                    total_value = stock.current_price * user_stock.quantity
                    purchase_value = user_stock.purchase_price * user_stock.quantity
                    change = ((stock.current_price - user_stock.purchase_price) / user_stock.purchase_price) * 100
                    
                    portfolio_value += total_value
                    total_gain += (total_value - purchase_value)
                    
                    # Get historical data for this stock
                    history = StockHistory.query.filter(
                        StockHistory.stock_id == stock.id,
                        StockHistory.date >= start_date,
                        StockHistory.date <= end_date
                    ).order_by(StockHistory.date).all()
                    
                    # Convert to DataFrame
                    df = pd.DataFrame([{
                        'date': h.date,
                        'close': h.close_price,
                        'volume': h.volume,
                        'symbol': stock.symbol,
                        'value': h.close_price * user_stock.quantity
                    } for h in history])
                    
                    if not df.empty:
                        all_stock_data.append(df)
                    
                    stocks_info.append({
                        'symbol': stock.symbol,
                        'company_name': stock.company_name,
                        'quantity': user_stock.quantity,
                        'current_price': stock.current_price,
                        'total_value': total_value,
                        'change': change
                    })
                
            except Exception as e:
                logger.error(f"Error processing stock: {str(e)}")
                continue
        
        # Combine all stock data
        if all_stock_data:
            combined_df = pd.concat(all_stock_data)
            
            # Portfolio value over time
            portfolio_df = combined_df.groupby('date')['value'].sum().reset_index()
            dates = portfolio_df['date'].dt.strftime('%Y-%m-%d').tolist()
            portfolio_values = portfolio_df['value'].round(2).tolist()
            
            # Individual stock performance
            stock_performance = combined_df.pivot(index='date', columns='symbol', values='close')
            stock_returns = stock_performance.pct_change()
            cumulative_returns = (1 + stock_returns).cumprod()
            
            # Convert to JSON for charts
            stock_data = {
                symbol: {
                    'dates': cumulative_returns.index.strftime('%Y-%m-%d').tolist(),
                    'values': cumulative_returns[symbol].round(4).tolist()
                }
                for symbol in stock_performance.columns
            }
            
            # Calculate daily change
            if len(portfolio_values) >= 2:
                daily_change = ((portfolio_values[-1] - portfolio_values[-2]) / portfolio_values[-2] * 100)
            else:
                daily_change = 0
        else:
            dates = []
            portfolio_values = []
            stock_data = {}
            daily_change = 0
        
        stats = {
            'total_stocks': total_stocks,
            'portfolio_value': portfolio_value,
            'daily_change': daily_change,
            'total_gain': total_gain
        }
        
        return render_template('dashboard.html',
                             stats=stats,
                             stocks=stocks_info,
                             dates=json.dumps(dates),
                             portfolio_values=json.dumps(portfolio_values),
                             stock_data=json.dumps(stock_data))
    
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash('An error occurred while loading the dashboard.', 'danger')
        return render_template('dashboard.html',
                             stats={'total_stocks': 0,
                                   'portfolio_value': 0.00,
                                   'daily_change': 0.00,
                                   'total_gain': 0.00},
                             stocks=[],
                             dates=json.dumps([]),
                             portfolio_values=json.dumps([]),
                             stock_data=json.dumps({}))
