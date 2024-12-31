from .home import home_bp
from .dashboard import dashboard_bp
from .stocks import stocks_bp
from .api import api_bp

__all__ = ['home_bp', 'dashboard_bp', 'stocks_bp', 'api_bp']

def register_blueprints(app):
    for blueprint in route_blueprints:
        app.register_blueprint(blueprint)
