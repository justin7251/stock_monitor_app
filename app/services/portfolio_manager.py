class PortfolioManager:
    def suggest_rebalancing(self, portfolio, target_allocation):
        current_allocation = self.get_current_allocation(portfolio)
        return self.calculate_trades_needed(current_allocation, target_allocation)
