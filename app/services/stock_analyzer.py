from app.services.ai_analysis_service import AIAnalysisService
from app.services.ml_indicators_service import MLIndicatorsService
from app.services.advanced_indicators_service import AdvancedIndicatorsService
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class StockAnalyzer:
    def __init__(self):
        self.ai_service = AIAnalysisService()
        self.ml_indicators = MLIndicatorsService()
        self.advanced_indicators = AdvancedIndicatorsService()

    def analyze_stock(self, stock_data):
        """
        Perform comprehensive stock analysis
        Args:
            stock_data: DataFrame with columns ['date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']
        """
        try:
            # Train AI model
            self.ai_service.train_model(stock_data)

            # Get AI predictions and signals
            analysis = self.ai_service.get_trading_signals(stock_data)
            
            # Get ML-RSI signals
            ml_rsi = self.ml_indicators.calculate_ml_rsi(stock_data)
            
            # Get advanced indicators
            advanced_signals = self.advanced_indicators.get_combined_signals(stock_data)

            # Combine all analyses
            return self._compile_analysis(analysis, ml_rsi, advanced_signals, stock_data)

        except Exception as e:
            logger.error(f"Error analyzing stock: {str(e)}")
            return None

    def _compile_analysis(self, ai_analysis, ml_rsi, advanced_signals, stock_data):
        """Compile all analyses into a comprehensive report"""
        current_price = stock_data['close_price'].iloc[-1]
        
        return {
            'summary': {
                'recommendation': ai_analysis['recommendation'],
                'confidence': ai_analysis['confidence'],
                'current_price': current_price,
                'predicted_price': ai_analysis['signals']['prediction']
            },
            'technical_indicators': {
                'rsi': ai_analysis['signals']['technical_indicators']['rsi'],
                'macd': ai_analysis['signals']['technical_indicators']['macd'],
                'obv': ai_analysis['signals']['technical_indicators']['obv']
            },
            'ml_indicators': {
                'ml_rsi_signal': ml_rsi['ml_rsi_signal'],
                'ml_rsi_confidence': ml_rsi['ml_confidence']
            },
            'advanced_indicators': {
                'volume_pressure': advanced_signals['volume_pressure'],
                'avso_signal': advanced_signals['avso_signal'],
                'lro_signal': advanced_signals['lro_signal'],
                'trend_strength': advanced_signals['trend_strength']
            },
            'price_analysis': ai_analysis['signals']['price_trend'],
            'volume_analysis': ai_analysis['signals']['volume_analysis']
        }

    def backtest_strategy(self, stock_data, initial_capital=100000.0):
        """
        Backtest the combined strategy
        """
        try:
            # Get ML-RSI backtest results
            ml_rsi_performance, ml_rsi_portfolio = self.ml_indicators.backtest_ml_rsi(
                stock_data, 
                initial_capital
            )

            # Compile backtest results
            return {
                'ml_rsi_performance': ml_rsi_performance,
                'final_portfolio_value': ml_rsi_portfolio['total'].iloc[-1],
                'total_return': ml_rsi_performance['total_return'],
                'sharpe_ratio': ml_rsi_performance['sharpe_ratio'],
                'max_drawdown': ml_rsi_performance['max_drawdown'],
                'win_rate': ml_rsi_performance['win_rate']
            }

        except Exception as e:
            logger.error(f"Error in backtest: {str(e)}")
            return None 