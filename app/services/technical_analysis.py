class TechnicalAnalysis:
    def get_indicators(self, stock_data):
        return {
            'moving_averages': self.calculate_ma(stock_data),
            'rsi': self.calculate_rsi(stock_data),
            'macd': self.calculate_macd(stock_data),
            'bollinger_bands': self.calculate_bollinger(stock_data)
        }
