class DividendTracker:
    def track_dividends(self, portfolio):
        return {
            'upcoming_dividends': self.get_upcoming_dividends(portfolio),
            'dividend_history': self.get_dividend_history(portfolio),
            'annual_yield': self.calculate_dividend_yield(portfolio)
        }
