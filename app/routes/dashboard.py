from app.database.models import Commodity, Stock
from flask import Blueprint, render_template

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    #only for login users
    # Fetch stocks
    # Fetch commodities
    # Process stocks and commodities
    # Calculate summary metrics
    return render_template('dashboard.html')
