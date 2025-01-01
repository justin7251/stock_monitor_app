import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import ta
import logging

logger = logging.getLogger(__name__)

class MLIndicatorsService:
    def __init__(self):
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.prediction_threshold = 0.6

    def calculate_ml_rsi(self, df, period=14, lookback=5):
        """Calculate ML-enhanced RSI with predictive capabilities"""
        try:
            # Calculate traditional RSI using 'ta' library
            df['RSI'] = ta.momentum.RSIIndicator(df['close_price'], window=period).rsi()
            
            # Create additional features
            self._add_technical_features(df)
            
            # Prepare ML features
            X, y = self._prepare_ml_features(df, lookback)
            
            # Train ML model
            self._train_ml_model(X, y)
            
            # Generate ML-enhanced RSI signals
            signals = self._generate_ml_rsi_signals(df, lookback)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error calculating ML RSI: {str(e)}")
            return None

    def _add_technical_features(self, df):
        """Add technical indicators as features using 'ta' library"""
        # Price-based indicators
        df['SMA_20'] = ta.trend.sma_indicator(df['close_price'], window=20)
        df['SMA_50'] = ta.trend.sma_indicator(df['close_price'], window=50)
        df['EMA_20'] = ta.trend.ema_indicator(df['close_price'], window=20)
        
        # Momentum indicators
        df['MOM'] = ta.momentum.momentum_indicator(df['close_price'], window=10)
        df['ROC'] = ta.momentum.roc(df['close_price'], window=10)
        
        # Volatility indicators
        df['BB_high'] = ta.volatility.bollinger_hband(df['close_price'])
        df['BB_low'] = ta.volatility.bollinger_lband(df['close_price'])
        
        # Volume indicators
        df['MFI'] = ta.volume.money_flow_index(
            df['high_price'], 
            df['low_price'], 
            df['close_price'], 
            df['volume']
        )
        
        # Trend indicators
        df['ADX'] = ta.trend.adx(
            df['high_price'], 
            df['low_price'], 
            df['close_price']
        )

    def _prepare_ml_features(self, df, lookback):
        """Prepare features and labels for ML model"""
        feature_columns = [
            'RSI', 'SMA_20', 'SMA_50', 'EMA_20', 
            'MOM', 'ROC', 'BB_high', 'BB_low', 
            'MFI', 'ADX'
        ]
        
        # Create rolling features
        for col in feature_columns:
            for i in range(1, lookback + 1):
                df[f'{col}_lag_{i}'] = df[col].shift(i)
        
        # Create target variable
        df['target'] = (df['close_price'].shift(-1) > df['close_price']).astype(int)
        
        # Remove rows with NaN values
        df = df.dropna()
        
        # Prepare features and target
        X = df[[col for col in df.columns if col.endswith(f'lag_{i}') 
               for i in range(1, lookback + 1)]]
        y = df['target']
        
        return X, y

    def _train_ml_model(self, X, y):
        """Train the Random Forest model"""
        try:
            # Split data
            X_train = self.scaler.fit_transform(X)
            
            # Train model
            self.rf_model.fit(X_train, y)
            
            # Log model performance
            train_score = self.rf_model.score(X_train, y)
            logger.info(f"ML RSI Model - Train Score: {train_score:.4f}")
            
        except Exception as e:
            logger.error(f"Error training ML RSI model: {str(e)}")

    def _generate_ml_rsi_signals(self, df, lookback):
        """Generate trading signals using ML-enhanced RSI"""
        try:
            # Prepare features for prediction
            X_pred = df[[col for col in df.columns if col.endswith(f'lag_{i}') 
                        for i in range(1, lookback + 1)]].tail(1)
            X_pred_scaled = self.scaler.transform(X_pred)
            
            # Get prediction probabilities
            pred_proba = self.rf_model.predict_proba(X_pred_scaled)[0]
            
            # Get traditional RSI value
            current_rsi = df['RSI'].iloc[-1]
            
            return {
                'ml_rsi_signal': 'BUY' if pred_proba[1] > self.prediction_threshold else 'SELL',
                'traditional_rsi': current_rsi,
                'ml_confidence': pred_proba[1],
                'prediction_proba': pred_proba.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error generating ML RSI signals: {str(e)}")
            return None 