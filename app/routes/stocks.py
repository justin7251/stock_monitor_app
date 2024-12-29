from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database.models import Stock, UserStock
from app.database import db
from app.utils import validate_stock_symbol, validate_name, validate_price
import logging

logger = logging.getLogger(__name__)
stocks_bp = Blueprint('stocks', __name__)

@stocks_bp.route('/')
@login_required
def stock_list():
    try:
        # Get user's stocks through UserStock model
        user_stocks = UserStock.query.filter_by(user_id=current_user.id).all()
        stocks_data = []
        
        for user_stock in user_stocks:
            stock = Stock.query.get(user_stock.stock_id)
            if stock:
                stocks_data.append({
                    'id': stock.id,
                    'symbol': stock.symbol,
                    'company_name': stock.company_name,
                    'quantity': user_stock.quantity,
                    'purchase_price': user_stock.purchase_price,
                    'current_price': stock.current_price or user_stock.purchase_price
                })
        
        return render_template('stocks.html', stocks=stocks_data)
    except Exception as e:
        logger.error(f"Error in stock_list: {str(e)}")
        return render_template('stocks.html', stocks=[], error=str(e))

@stocks_bp.route('/add', methods=['GET', 'POST'])
@login_required
def create_stock():
    if request.method == 'GET':
        return redirect(url_for('stocks.stock_list'))
        
    try:
        data = request.get_json()
        
        # Validate input
        validate_stock_symbol(data['symbol'])
        validate_name(data['name'])
        validate_price(data['price'])
        
        # Check if stock already exists
        existing_stock = Stock.query.filter_by(symbol=data['symbol']).first()
        if existing_stock:
            # Check if user already owns this stock
            existing_user_stock = UserStock.query.filter_by(
                user_id=current_user.id,
                stock_id=existing_stock.id
            ).first()
            
            if existing_user_stock:
                # Update existing position
                existing_user_stock.quantity += data['quantity']
                # Calculate new average purchase price
                total_cost = (existing_user_stock.quantity * existing_user_stock.purchase_price) + \
                           (data['quantity'] * data['price'])
                new_total_quantity = existing_user_stock.quantity + data['quantity']
                existing_user_stock.purchase_price = total_cost / new_total_quantity
            else:
                # Create new UserStock entry
                user_stock = UserStock(
                    user_id=current_user.id,
                    stock_id=existing_stock.id,
                    quantity=data['quantity'],
                    purchase_price=data['price']
                )
                db.session.add(user_stock)
        else:
            # Create new stock and UserStock entry
            new_stock = Stock(
                symbol=data['symbol'],
                company_name=data['name'],
                current_price=data['price']
            )
            db.session.add(new_stock)
            db.session.flush()  # Get the new stock's ID
            
            user_stock = UserStock(
                user_id=current_user.id,
                stock_id=new_stock.id,
                quantity=data['quantity'],
                purchase_price=data['price']
            )
            db.session.add(user_stock)
        
        db.session.commit()
        logger.info(f"Stock {data['symbol']} added for user {current_user.id}")
        return jsonify({"message": "Stock added successfully!"}), 201
        
    except ValueError as e:
        logger.error(f"Validation error in create_stock: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in create_stock: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "An error occurred while adding the stock"}), 500

@stocks_bp.route('/delete/<int:stock_id>', methods=['POST'])
@login_required
def delete_stock(stock_id):
    try:
        user_stock = UserStock.query.filter_by(
            user_id=current_user.id,
            stock_id=stock_id
        ).first()
        
        if not user_stock:
            return jsonify({"error": "Stock not found in your portfolio"}), 404
            
        db.session.delete(user_stock)
        db.session.commit()
        logger.info(f"Stock {stock_id} deleted for user {current_user.id}")
        return jsonify({"message": "Stock deleted successfully!"}), 200
        
    except Exception as e:
        logger.error(f"Error in delete_stock: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

