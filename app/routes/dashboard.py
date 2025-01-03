from flask import render_template, Blueprint
from flask_login import login_required, current_user
from app.database.models import UserStock, Stock, db
from sqlalchemy import func
from datetime import datetime, timedelta
from app.utils.stock_utils import get_or_update_stock

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def dashboard():
    try:
        # Get user's holdings with proper data structure and update prices
        holdings = []
        total_value = 0
        total_cost = 0

        user_stocks = (
            db.session.query(UserStock, Stock)
            .join(Stock, UserStock.stock_id == Stock.id)
            .filter(UserStock.user_id == current_user.id)
            .all()
        )

        print(f"Debug - User stocks: {user_stocks}")  # Debug print

        for user_stock, stock in user_stocks:
            # Update stock data
            updated_stock, success, _ = get_or_update_stock(stock.symbol)
            if success and updated_stock:
                current_price = updated_stock.current_price
            else:
                current_price = stock.current_price

            # Calculate values
            position_value = user_stock.quantity * current_price
            position_cost = user_stock.quantity * user_stock.purchase_price
            return_pct = ((current_price - user_stock.purchase_price) / user_stock.purchase_price * 100) if user_stock.purchase_price > 0 else 0

            holdings.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'type': stock.type,
                'quantity': user_stock.quantity,
                'avg_price': user_stock.purchase_price,
                'current_price': current_price,
                'total_value': position_value,
                'return_pct': return_pct
            })

            total_value += position_value
            total_cost += position_cost

        # Calculate portfolio summary
        portfolio_summary = {
            'total_value': round(total_value, 2),
            'total_cost': round(total_cost, 2),
            'total_return': round(((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0, 2),
            'daily_change': 0  # Will be updated via API
        }

        # Sort holdings by value
        holdings = sorted(holdings, key=lambda x: x['total_value'], reverse=True)

        # Fetch user's watchlist
        watchlist_items = Watchlist.query.filter_by(user_id=current_user.id).all()
        watchlist = []

        for item in watchlist_items:
            # Assuming you have a function to get stock details
            stock_details = get_stock_details(item.stock_symbol)  # Fetch stock details from an API or database
            watchlist.append({
                'symbol': item.stock_symbol,
                'name': stock_details['name'],
                'price': stock_details['current_price'],
                'change': stock_details['change_percentage']
            })

        return render_template(
            'dashboard.html',
            holdings=holdings,
            portfolio_summary=portfolio_summary,
            watchlist=watchlist
        )

    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return render_template(
            'dashboard.html',
            holdings=[],
            portfolio_summary={
                'total_value': 0,
                'total_cost': 0,
                'total_return': 0,
                'daily_change': 0
            }
        )
