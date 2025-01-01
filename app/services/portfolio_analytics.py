class PortfolioAnalytics:
    def calculate_metrics(self, portfolio):
        return {
            'alpha': self._calculate_alpha(portfolio),
            'beta': self._calculate_beta(portfolio),
            'sharpe_ratio': self._calculate_sharpe_ratio(portfolio),
            'volatility': self._calculate_volatility(portfolio),
            'diversification_score': self._calculate_diversification(portfolio)
        }
