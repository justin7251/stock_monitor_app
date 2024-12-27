from flask import Blueprint, render_template, request, redirect, url_for
from app.database.models import Commodity
from app.database import db
from app.utils import validate_name, validate_price 

commodities_bp = Blueprint('commodities', __name__)


@commodities_bp.route('/')
def commodity_list():
    try:
        commodities = Commodity.query.all()
        return render_template('commodities.html', commodities=commodities)
    except Exception as e:
        return render_template('commodities.html', commodities=[], error=str(e))

@commodities_bp.route('/add', methods=['POST'])
def create_commodity():
    data = request.get_json()
    try:
        validate_name(data['name'])
        validate_price(data['price'])
        new_commodity = Commodity(
            name=data['name'],
            price=data['price'],
            volume=data['volume']
        )
        db.session.add(new_commodity)
        db.session.commit()
        return jsonify({"message": "Commodity created successfully!"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

def fetch_commodity_types():
    return ["", "Energy", "Metals", "Agriculture", "Livestock"]

@commodities_bp.route('/delete/<int:commodity_id>', methods=['POST'])
def delete_commodity(commodity_id):
    try:
        commodity = Commodity.query.get(commodity_id)
        if not commodity:
            return jsonify({"error": "Commodity not found"}), 404
        db.session.delete(commodity)
        db.session.commit()
        return jsonify({"message": "Commodity deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

