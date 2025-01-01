# app/services/alert_service.py
class AlertService:
    def __init__(self):
        self.alert_types = {
            'price_above': lambda price, threshold: price > threshold,
            'price_below': lambda price, threshold: price < threshold,
            'percent_change': lambda change, threshold: abs(change) > threshold
        }

    def check_alerts(self, stock, price, change):
        alerts = UserAlert.query.filter_by(stock_id=stock.id).all()
        for alert in alerts:
            if self.alert_types[alert.type](price, alert.threshold):
                self.send_alert(alert)