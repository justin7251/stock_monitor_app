from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
from app.database.models import Stock
from app.database import db
import logging

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def dashboard():
    try:
        # Get user's stocks
        user_stocks = Stock.query.filter_by(user_id=current_user.id).all()
        
        # Calculate statistics
        total_stocks = len(user_stocks)
        portfolio_value = 0.00
        daily_change = 0.00
        total_gain = 0.00
        
        # Process stocks data for display
        stocks = []
        for stock in user_stocks:
            try:
                current_price = stock.purchase_price  # Placeholder
                total_value = current_price * stock.quantity
                change = ((current_price - stock.purchase_price) / stock.purchase_price) * 100 if stock.purchase_price else 0
                
                portfolio_value += total_value
                
                stocks.append({
                    'symbol': stock.symbol,
                    'company_name': stock.company_name,
                    'quantity': stock.quantity,
                    'current_price': current_price,
                    'total_value': total_value,
                    'change': change
                })
            except Exception as e:
                logger.error(f"Error processing stock {stock.symbol}: {str(e)}")
                continue
        
        stats = {
            'total_stocks': total_stocks,
            'portfolio_value': portfolio_value,
            'daily_change': daily_change,
            'total_gain': total_gain
        }
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             stocks=stocks)
    
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash('An error occurred while loading the dashboard.', 'danger')
        return render_template('dashboard.html', 
                             stats={'total_stocks': 0, 'portfolio_value': 0.00, 'daily_change': 0.00, 'total_gain': 0.00}, 
                             stocks=[])
