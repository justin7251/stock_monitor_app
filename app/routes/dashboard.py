from flask import render_template, Blueprint
from flask_login import login_required, current_user
from app.database.models import UserStock, Stock, Watchlist, db
from sqlalchemy import func
from datetime import datetime, timedelta
from app.utils.stock_utils import get_or_update_stock

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def dashboard():
    # Fetch user's holdings
    user_stocks = UserStock.query.filter_by(user_id=current_user.id).all()
    holdings = []
    total_value = 0

    for user_stock in user_stocks:
        stock = Stock.query.get(user_stock.stock_id)
        if stock:
            current_value = user_stock.quantity * stock.current_price
            purchase_price = user_stock.purchase_price  # Assuming you have this field in UserStock
            return_pct = ((stock.current_price - purchase_price) / purchase_price) * 100 if purchase_price else 0
            
            holdings.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'quantity': user_stock.quantity,
                'current_price': stock.current_price,
                'total_value': current_value,
                'return_pct': return_pct
            })
            total_value += current_value

    # Fetch user's watchlist
    watchlist_items = Watchlist.query.filter_by(user_id=current_user.id).all()
    watchlist = []
    
    for item in watchlist_items:
        stock = Stock.query.get(item.stock_id)
        if stock:
            # Calculate change or any other relevant metric
            change = stock.current_price
            watchlist.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'price': stock.current_price,
                'change': change,
            })
        else:
            print(f"Stock with ID {item.stock_id} not found.")  # Debugging line

    # Check if portfolio_summary is being created correctly
    portfolio_summary = {
        'total_value': total_value,
        'total_cost': sum(user_stock.purchase_price * user_stock.quantity for user_stock in user_stocks),
        'total_return': total_value - sum(user_stock.purchase_price * user_stock.quantity for user_stock in user_stocks),
        'daily_change': 0  # Placeholder for daily change calculation
    }

    return render_template('dashboard.html', holdings=holdings, portfolio_summary=portfolio_summary, watchlist=watchlist)