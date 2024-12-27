from flask import Blueprint

# Import all route blueprints
from .home import home_bp
from .stocks import stocks_bp
from .commodities import commodities_bp

# List of all blueprints for easy registration
route_blueprints = [
    home_bp,
    stocks_bp,
    commodities_bp
]

def register_blueprints(app):
    for blueprint in route_blueprints:
        app.register_blueprint(blueprint)


