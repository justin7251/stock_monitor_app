from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.database.models import Stock, UserStock, StockHistory, Watchlist
from app.database import db
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from app.utils.stock_plotter import StockPlotter
from app.utils.stock_utils import get_stock_history
import json
import requests

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/portfolio/value', methods=['GET'])
@login_required
def get_portfolio_value():
    try:
        # Get date range from query parameters
        days = request.args.get('days', default=30, type=int)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get user's stocks with their quantities
        user_stocks = (
            db.session.query(UserStock, Stock)
            .join(Stock, UserStock.stock_id == Stock.id)
            .filter(UserStock.user_id == current_user.id)
            .all()
        )
        
        if not user_stocks:
            return jsonify({'dates': [], 'values': []})

        # Initialize data structure for portfolio values
        portfolio_values = {}
        
        for user_stock, stock in user_stocks:
            # Get historical data for each stock
            history_data, success, _ = get_stock_history(stock.symbol, period=f'{days}d')
            
            if success and history_data:
                for date, close_price in zip(history_data['dates'], history_data['close']):
                    date = date.split()[0]  # Get just the date part
                    value = close_price * user_stock.quantity
                    
                    if date in portfolio_values:
                        portfolio_values[date] += value
                    else:
                        portfolio_values[date] = value

        # Convert to sorted lists
        sorted_dates = sorted(portfolio_values.keys())
        values = [portfolio_values[date] for date in sorted_dates]

        return jsonify({
            'dates': sorted_dates,
            'values': [round(v, 2) for v in values]
        })
    
    except Exception as e:
        print(f"Portfolio value error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stocks/performance', methods=['GET'])
@login_required
def get_stocks_performance():
    try:
        days = request.args.get('days', default=30, type=int)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        user_stocks = UserStock.query.filter_by(user_id=current_user.id).all()
        performance_data = {}
        
        for user_stock in user_stocks:
            stock = Stock.query.get(user_stock.stock_id)
            if stock:
                history = StockHistory.query.filter(
                    StockHistory.stock_id == stock.id,
                    StockHistory.date >= start_date,
                    StockHistory.date <= end_date
                ).order_by(StockHistory.date).all()
                
                if history:
                    dates = [h.date.strftime('%Y-%m-%d') for h in history]
                    prices = [h.close_price for h in history]
                    
                    # Calculate percentage change
                    base_price = prices[0]
                    changes = [(price / base_price - 1) * 100 for price in prices]
                    
                    performance_data[stock.symbol] = {
                        'dates': dates,
                        'changes': changes
                    }
        
        return jsonify(performance_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stocks/update', methods=['POST'])
@login_required
def update_stock_prices():
    try:
        user_stocks = UserStock.query.filter_by(user_id=current_user.id).all()
        updated_stocks = []
        
        for user_stock in user_stocks:
            stock = Stock.query.get(user_stock.stock_id)
            if stock:
                # Get latest data from yfinance
                ticker = yf.Ticker(stock.symbol)
                current_price = ticker.history(period='1d')['Close'].iloc[-1]
                
                # Update stock price
                stock.current_price = current_price
                
                # Add to history
                history = StockHistory(
                    stock_id=stock.id,
                    date=datetime.now(),
                    close_price=current_price,
                    volume=ticker.history(period='1d')['Volume'].iloc[-1]
                )
                db.session.add(history)
                
                updated_stocks.append({
                    'symbol': stock.symbol,
                    'price': current_price
                })
        
        db.session.commit()
        return jsonify({'updated': updated_stocks})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/portfolio/stats', methods=['GET'])
@login_required
def get_portfolio_stats():
    try:
        user_stocks = UserStock.query.filter_by(user_id=current_user.id).all()
        total_value = 0
        total_gain = 0
        daily_change = 0
        
        for user_stock in user_stocks:
            stock = Stock.query.get(user_stock.stock_id)
            if stock and stock.current_price:
                current_value = stock.current_price * user_stock.quantity
                purchase_value = user_stock.purchase_price * user_stock.quantity
                
                total_value += current_value
                total_gain += (current_value - purchase_value)
                
                # Calculate daily change
                yesterday = datetime.now() - timedelta(days=1)
                yesterday_history = StockHistory.query.filter(
                    StockHistory.stock_id == stock.id,
                    StockHistory.date >= yesterday
                ).first()
                
                if yesterday_history:
                    daily_change += ((stock.current_price - yesterday_history.close_price) / 
                                   yesterday_history.close_price * 100)
        
        return jsonify({
            'total_value': round(total_value, 2),
            'total_gain': round(total_gain, 2),
            'daily_change': round(daily_change, 2)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stock/<symbol>/data', methods=['GET'])
@login_required
def get_stock_data(symbol):
    try:
        # Get date range from query parameters
        interval = request.args.get('interval', default='1d')
        period = request.args.get('period', default='1mo')
        
        # Get stock data from yfinance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        # Format data for plotting
        data = {
            'dates': hist.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            'open': hist['Open'].round(2).tolist(),
            'high': hist['High'].round(2).tolist(),
            'low': hist['Low'].round(2).tolist(),
            'close': hist['Close'].round(2).tolist(),
            'volume': hist['Volume'].tolist()
        }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

@api_bp.route('/stock/<symbol>/chart')
@login_required
def get_stock_chart(symbol):
    try:
        period = request.args.get('period', '1mo')
        indicators = request.args.get('indicators', '[]')
        indicators = json.loads(indicators)
        
        plotter = StockPlotter(symbol, period)
        
        # Add all requested indicators
        for indicator in indicators:
            plotter.add_indicator(indicator['category'], indicator['name'])
        
        return plotter.create_plot()
    except Exception as e:
        return str(e), 500 

@api_bp.route('/stock/<symbol>/price', methods=['GET'])
@login_required
def get_stock_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return jsonify({'price': ticker.history(period='1d')['Close'].iloc[-1]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/search/stocks', methods=['GET'])
@login_required
def search_stocks():
    query = request.args.get('query', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        # First check our database
        db_results = Stock.query.filter(
            db.or_(
                Stock.symbol.ilike(f'%{query}%'),
                Stock.name.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        db_results = [{'symbol': s.symbol, 'name': s.name, 'type': s.type} for s in db_results]
        
        # If we have less than 10 results, fetch from Yahoo Finance
        if len(db_results) < 10:
            url = f"https://query2.finance.yahoo.com/v1/finance/search"
            params = {
                'q': query,
                'quotesCount': 10,
                'newsCount': 0,
                'enableFuzzyQuery': True,
                'quotesQueryId': 'tss_match_phrase_query'
            }
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                yf_results = response.json().get('quotes', [])
                
                # Filter and format Yahoo Finance results
                for result in yf_results:
                    symbol = result.get('symbol')
                    if symbol and not any(r['symbol'] == symbol for r in db_results):
                        db_results.append({
                            'symbol': symbol,
                            'name': result.get('shortname', result.get('longname', '')),
                            'type': 'stock' if result.get('quoteType') == 'EQUITY' else result.get('quoteType', '').lower(),
                            'exchange': result.get('exchange', '')
                        })
        
        # Sort results: exact matches first, then by symbol length
        def sort_key(item):
            symbol_match = item['symbol'].lower() == query.lower()
            name_match = item['name'].lower() == query.lower()
            symbol_starts = item['symbol'].lower().startswith(query.lower())
            name_starts = item['name'].lower().startswith(query.lower())
            return (
                not symbol_match,  # Exact symbol matches first
                not name_match,    # Exact name matches second
                not symbol_starts, # Symbol starts with query third
                not name_starts,   # Name starts with query fourth
                len(item['symbol']),  # Shorter symbols preferred
                item['symbol'].lower()  # Alphabetical order
            )

        sorted_results = sorted(db_results, key=sort_key)
        return jsonify(sorted_results[:10])
        
    except Exception as e:
        print(f"Stock search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

@api_bp.route('/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    data = request.get_json()
    symbol = data.get('symbol')

    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400

    # Check if the stock exists in the stocks table
    stock = Stock.query.filter_by(symbol=symbol).first()
    
    if not stock:
        # If the stock does not exist, add it to the stocks table
        try:
            ticker = yf.Ticker(symbol)
            stock_info = ticker.info
            
            stock = Stock(
                symbol=symbol,
                name=stock_info.get('longName', 'Unknown'),
                current_price=stock_info.get('currentPrice', 0.0),
                type=stock_info.get('quoteType', 'Unknown'),
                last_updated=datetime.utcnow()
            )
            db.session.add(stock)
            db.session.commit()
        except Exception as e:
            return jsonify({'error': f'Failed to fetch stock data: {str(e)}'}), 500

    # Check if the stock is already in the watchlist
    existing_watchlist_item = Watchlist.query.filter_by(user_id=current_user.id, stock_id=stock.id).first()
    if existing_watchlist_item:
        return jsonify({'error': 'Stock is already in your watchlist'}), 400

    # Add the stock to the watchlist
    watchlist_item = Watchlist(user_id=current_user.id, stock_id=stock.id)
    db.session.add(watchlist_item)
    db.session.commit()

    return jsonify({'message': f'Stock {symbol} added to watchlist'}), 200