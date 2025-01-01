class ExportService:
    def export_portfolio(self, user_id, format='csv'):
        portfolio_data = self.get_portfolio_data(user_id)
        if format == 'csv':
            return self.to_csv(portfolio_data)
        elif format == 'pdf':
            return self.to_pdf(portfolio_data)
