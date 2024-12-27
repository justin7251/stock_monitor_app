from flask import Blueprint, render_template, request, redirect, url_for
from app.database.models import Stock
from app.database import db
from app.utils import validate_stock_symbol, validate_name, validate_price

stocks_bp = Blueprint('stocks', __name__, url_prefix='/stocks')


@stocks_bp.route('/')
def stock_list():
    try:
        stocks = Stock.query.all()
        return render_template('stocks.html', stocks=stocks)
    except Exception as e:
        return render_template('stocks.html', stocks=[], error=str(e))
    

@stocks_bp.route('/add', methods=['POST'])
def create_stock():
    data = request.get_json()
    try:
        validate_stock_symbol(data['symbol'])
        validate_name(data['name'])
        validate_price(data['price'])
        new_stock = Stock(
            symbol=data['symbol'],
            price=data['price'],
            volume=data['volume']
        )
        db.session.add(new_stock)
        db.session.commit()
        return jsonify({"message": "Stock created successfully!"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@stocks_bp.route('/delete/<int:stock_id>', methods=['POST'])
def delete_stock(stock_id):
    try:
        stock = Stock.query.get(stock_id)
        if not stock:
            return jsonify({"error": "Stock not found"}), 404
        db.session.delete(stock)
        db.session.commit()
        return jsonify({"message": "Stock deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

