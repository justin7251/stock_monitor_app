import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
import logging

logger = logging.getLogger(__name__)

class AdvancedIndicatorsService:
    def __init__(self):
        self.lookback_period = 20
        self.volatility_window = 14
        self.regression_period = 30

    def calculate_volume_delta(self, df, window=20):
        """
        Calculate Volume Delta (Buying vs Selling Pressure)
        Args:
            df: DataFrame with OHLCV data
            window: Rolling window for volume analysis
        """
        try:
            # Calculate price changes
            df['price_change'] = df['close_price'] - df['open_price']
            
            # Calculate volume delta
            df['volume_delta'] = np.where(df['price_change'] > 0, 
                                        df['volume'], 
                                        np.where(df['price_change'] < 0, 
                                                -df['volume'], 0))
            
            # Calculate cumulative volume delta
            df['cum_volume_delta'] = df['volume_delta'].cumsum()
            
            # Calculate volume delta momentum
            df['volume_delta_ma'] = df['volume_delta'].rolling(window=window).mean()
            df['volume_delta_momentum'] = df['volume_delta'] - df['volume_delta_ma']
            
            # Calculate volume delta divergence
            df['price_ma'] = df['close_price'].rolling(window=window).mean()
            df['volume_delta_divergence'] = (
                (df['close_price'] - df['price_ma']) * 
                (df['volume_delta'] - df['volume_delta_ma'])
            )
            
            return {
                'volume_delta': df['volume_delta'],
                'cum_volume_delta': df['cum_volume_delta'],
                'volume_delta_momentum': df['volume_delta_momentum'],
                'volume_delta_divergence': df['volume_delta_divergence']
            }
            
        except Exception as e:
            logger.error(f"Error calculating Volume Delta: {str(e)}")
            return None

    def calculate_avso(self, df, alpha=0.1):
        """
        Calculate Adaptive Volatility Scaled Oscillator
        Args:
            df: DataFrame with OHLCV data
            alpha: Smoothing factor for adaptive calculation
        """
        try:
            # Calculate price returns
            df['returns'] = df['close_price'].pct_change()
            
            # Calculate adaptive volatility
            df['volatility'] = df['returns'].rolling(window=self.volatility_window).std()
            
            # Calculate adaptive bands
            df['upper_band'] = df['close_price'] + (df['volatility'] * df['close_price'])
            df['lower_band'] = df['close_price'] - (df['volatility'] * df['close_price'])
            
            # Calculate AVSO
            df['avso'] = (df['close_price'] - df['lower_band']) / (df['upper_band'] - df['lower_band'])
            
            # Calculate adaptive thresholds
            df['avso_ma'] = df['avso'].ewm(alpha=alpha).mean()
            df['avso_std'] = df['avso'].rolling(window=self.volatility_window).std()
            
            df['avso_upper'] = df['avso_ma'] + (2 * df['avso_std'])
            df['avso_lower'] = df['avso_ma'] - (2 * df['avso_std'])
            
            # Generate signals
            df['avso_signal'] = np.where(df['avso'] > df['avso_upper'], -1,  # Overbought
                                       np.where(df['avso'] < df['avso_lower'], 1, 0))  # Oversold
            
            return {
                'avso': df['avso'],
                'avso_ma': df['avso_ma'],
                'avso_upper': df['avso_upper'],
                'avso_lower': df['avso_lower'],
                'avso_signal': df['avso_signal']
            }
            
        except Exception as e:
            logger.error(f"Error calculating AVSO: {str(e)}")
            return None

    def calculate_lro(self, df, period=None):
        """
        Calculate Linear Regression Oscillator
        Args:
            df: DataFrame with OHLCV data
            period: Regression period (optional)
        """
        try:
            if period is None:
                period = self.regression_period
                
            # Initialize arrays for results
            lro_values = []
            r2_values = []
            slope_values = []
            
            # Calculate for each window
            for i in range(len(df) - period + 1):
                window = df['close_price'].iloc[i:i+period]
                
                # Prepare data for regression
                X = np.arange(len(window)).reshape(-1, 1)
                y = window.values.reshape(-1, 1)
                
                # Fit linear regression
                model = LinearRegression()
                model.fit(X, y)
                
                # Calculate regression values
                y_pred = model.predict(X)
                
                # Calculate R-squared
                r2 = model.score(X, y)
                
                # Calculate oscillator value
                last_price = window.iloc[-1]
                regression_value = y_pred[-1][0]
                oscillator_value = (last_price - regression_value) / regression_value
                
                # Store values
                lro_values.append(oscillator_value)
                r2_values.append(r2)
                slope_values.append(model.coef_[0][0])
            
            # Add padding for initial periods
            padding = [np.nan] * (period - 1)
            
            # Create Series for results
            df['LRO'] = padding + lro_values
            df['LRO_R2'] = padding + r2_values
            df['LRO_SLOPE'] = padding + slope_values
            
            # Calculate signals
            df['LRO_MA'] = df['LRO'].rolling(window=period//2).mean()
            df['LRO_STD'] = df['LRO'].rolling(window=period//2).std()
            
            df['LRO_UPPER'] = df['LRO_MA'] + (2 * df['LRO_STD'])
            df['LRO_LOWER'] = df['LRO_MA'] - (2 * df['LRO_STD'])
            
            # Generate trading signals
            df['LRO_SIGNAL'] = np.where(df['LRO'] > df['LRO_UPPER'], -1,  # Overbought
                                      np.where(df['LRO'] < df['LRO_LOWER'], 1, 0))  # Oversold
            
            return {
                'lro': df['LRO'],
                'r2': df['LRO_R2'],
                'slope': df['LRO_SLOPE'],
                'signal': df['LRO_SIGNAL'],
                'upper': df['LRO_UPPER'],
                'lower': df['LRO_LOWER']
            }
            
        except Exception as e:
            logger.error(f"Error calculating LRO: {str(e)}")
            return None

    def get_combined_signals(self, df):
        """Get combined signals from all indicators"""
        try:
            # Calculate all indicators
            volume_delta = self.calculate_volume_delta(df)
            avso = self.calculate_avso(df)
            lro = self.calculate_lro(df)
            
            if all([volume_delta, avso, lro]):
                # Combine signals
                signals = {
                    'volume_pressure': np.sign(volume_delta['volume_delta_momentum'].iloc[-1]),
                    'volume_trend': np.sign(volume_delta['cum_volume_delta'].diff().iloc[-1]),
                    'avso_signal': avso['avso_signal'].iloc[-1],
                    'lro_signal': lro['signal'].iloc[-1],
                    'trend_strength': abs(lro['r2'].iloc[-1]),
                    'trend_direction': np.sign(lro['slope'].iloc[-1])
                }
                
                # Calculate composite signal
                composite_signal = (
                    signals['volume_pressure'] * 0.3 +
                    signals['avso_signal'] * 0.3 +
                    signals['lro_signal'] * 0.4
                )
                
                signals['composite_signal'] = np.sign(composite_signal)
                signals['signal_strength'] = abs(composite_signal)
                
                return signals
                
            return None
            
        except Exception as e:
            logger.error(f"Error calculating combined signals: {str(e)}")
            return None 