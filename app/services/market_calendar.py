class MarketCalendar:
    def get_trading_days(self, start_date, end_date):
        return self.calendar.trading_days(start_date, end_date)

    def is_market_open(self):
        return self.calendar.is_market_open()
