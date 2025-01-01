import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
import tensorflow as tf
from datetime import datetime, timedelta
import logging
from app.services.ml_indicators_service import MLIndicatorsService
from app.services.advanced_indicators_service import AdvancedIndicatorsService

logger = logging.getLogger(__name__)

class AIAnalysisService:
    def __init__(self):
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.prediction_days = 60  # Number of days to use for prediction
        self.ml_indicators = MLIndicatorsService()
        self.advanced_indicators = AdvancedIndicatorsService()
        
    def prepare_data(self, stock_history):
        """Prepare data for AI analysis"""
        try:
            # Convert to DataFrame if not already
            df = pd.DataFrame(stock_history)
            
            # Add ML-enhanced RSI
            ml_rsi_signals = self.ml_indicators.calculate_ml_rsi(df)
            if ml_rsi_signals:
                df['ML_RSI_SIGNAL'] = ml_rsi_signals['ml_rsi_signal']
                df['ML_RSI_CONFIDENCE'] = ml_rsi_signals['ml_confidence']
            
            # Calculate technical indicators
            df['SMA_20'] = df['close_price'].rolling(window=20).mean()
            df['SMA_50'] = df['close_price'].rolling(window=50).mean()
            df['RSI'] = self.calculate_rsi(df['close_price'])
            
            # Enhanced MACD
            df['MACD'], df['MACD_signal'], df['MACD_hist'] = self.calculate_macd(df['close_price'])
            
            # OBV
            df['OBV'] = self.calculate_obv(df['close_price'], df['volume'])
            df['OBV_EMA'] = df['OBV'].ewm(span=20).mean()
            
            df['BB_upper'], df['BB_lower'] = self.calculate_bollinger_bands(df['close_price'])
            
            # Add advanced indicators
            advanced_signals = self.advanced_indicators.get_combined_signals(df)
            if advanced_signals:
                df['VOLUME_PRESSURE'] = advanced_signals['volume_pressure']
                df['AVSO_SIGNAL'] = advanced_signals['avso_signal']
                df['LRO_SIGNAL'] = advanced_signals['lro_signal']
                df['TREND_STRENGTH'] = advanced_signals['trend_strength']
            
            # Create feature set
            features = np.column_stack((
                df['close_price'],
                df['volume'],
                df['SMA_20'],
                df['SMA_50'],
                df['RSI'],
                df['MACD'],
                df['MACD_signal'],
                df['MACD_hist'],
                df['OBV'],
                df['OBV_EMA'],
                df['BB_upper'],
                df['BB_lower']
            ))
            
            # Scale features
            scaled_features = self.scaler.fit_transform(features)
            
            return scaled_features, df
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            return None, None

    def train_model(self, stock_history):
        """Train the LSTM model"""
        try:
            scaled_data, df = self.prepare_data(stock_history)
            if scaled_data is None:
                return False
            
            X, y = [], []
            for i in range(self.prediction_days, len(scaled_data)):
                X.append(scaled_data[i-self.prediction_days:i])
                y.append(scaled_data[i, 0])  # Predict next day's closing price
                
            X, y = np.array(X), np.array(y)
            
            # Create LSTM model
            self.model = Sequential([
                LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
                Dropout(0.2),
                LSTM(units=50, return_sequences=True),
                Dropout(0.2),
                LSTM(units=50),
                Dropout(0.2),
                Dense(units=1)
            ])
            
            self.model.compile(optimizer='adam', loss='mean_squared_error')
            self.model.fit(X, y, epochs=25, batch_size=32, verbose=0)
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False

    def get_prediction(self, stock_history):
        """Get prediction for next day"""
        try:
            scaled_data, df = self.prepare_data(stock_history[-self.prediction_days:])
            if scaled_data is None:
                return None
            
            # Prepare input data
            X = np.array([scaled_data])
            
            # Make prediction
            prediction = self.model.predict(X)
            actual_prediction = self.scaler.inverse_transform(prediction)[0, 0]
            
            return actual_prediction
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            return None

    def get_trading_signals(self, stock_history):
        """Generate trading signals based on technical analysis"""
        try:
            _, df = self.prepare_data(stock_history)
            if df is None:
                return None
            
            signals = {
                'price_trend': self._analyze_price_trend(df),
                'volume_analysis': self._analyze_volume(df),
                'technical_indicators': self._analyze_technical_indicators(df),
                'prediction': self.get_prediction(stock_history)
            }
            
            # Generate final recommendation
            recommendation = self._generate_recommendation(signals)
            
            return {
                'recommendation': recommendation,
                'signals': signals,
                'confidence': self._calculate_confidence(signals)
            }
            
        except Exception as e:
            logger.error(f"Error generating trading signals: {str(e)}")
            return None

    def _analyze_price_trend(self, df):
        """Analyze price trends"""
        current_price = df['close_price'].iloc[-1]
        sma_20 = df['SMA_20'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        
        return {
            'above_sma_20': current_price > sma_20,
            'above_sma_50': current_price > sma_50,
            'trend': 'upward' if current_price > sma_20 > sma_50 else 'downward'
        }

    def _analyze_volume(self, df):
        """Analyze volume patterns"""
        avg_volume = df['volume'].mean()
        current_volume = df['volume'].iloc[-1]
        
        return {
            'volume_trend': 'high' if current_volume > avg_volume else 'low',
            'volume_ratio': current_volume / avg_volume
        }

    def _analyze_technical_indicators(self, df):
        """Enhanced technical indicator analysis"""
        # Get latest values
        current_macd = df['MACD'].iloc[-1]
        current_signal = df['MACD_signal'].iloc[-1]
        current_hist = df['MACD_hist'].iloc[-1]
        current_obv = df['OBV'].iloc[-1]
        obv_ema = df['OBV_EMA'].iloc[-1]
        
        # MACD Analysis
        macd_crossover = current_macd > current_signal
        macd_trend = 'bullish' if current_hist > 0 else 'bearish'
        
        # OBV Analysis
        obv_trend = 'bullish' if current_obv > obv_ema else 'bearish'
        
        return {
            'rsi': df['RSI'].iloc[-1],
            'macd': {
                'value': current_macd,
                'signal': current_signal,
                'histogram': current_hist,
                'crossover': macd_crossover,
                'trend': macd_trend
            },
            'obv': {
                'value': current_obv,
                'ema': obv_ema,
                'trend': obv_trend
            },
            'bollinger_position': self._get_bollinger_position(df)
        }

    def _generate_recommendation(self, signals):
        """Enhanced recommendation generation"""
        score = 0
        
        # Price trend analysis
        if signals['price_trend']['trend'] == 'upward':
            score += 2
        
        # Volume analysis
        if signals['volume_analysis']['volume_trend'] == 'high':
            score += 1
        
        # Technical indicators
        tech = signals['technical_indicators']
        
        # RSI
        if tech['rsi'] < 30:  # Oversold
            score += 2
        elif tech['rsi'] > 70:  # Overbought
            score -= 2
        
        # MACD
        if tech['macd']['trend'] == 'bullish':
            score += 2
        else:
            score -= 1
            
        if tech['macd']['crossover']:  # Bullish crossover
            score += 1
        
        # OBV
        if tech['obv']['trend'] == 'bullish':
            score += 2
        else:
            score -= 1
        
        # AI prediction
        current_price = signals['price_trend']['current_price']
        if signals['prediction'] > current_price * 1.02:
            score += 2
        
        # Add ML RSI signals to scoring
        if signals.get('ML_RSI_SIGNAL') == 'BUY' and signals.get('ML_RSI_CONFIDENCE', 0) > 0.7:
            score += 3
        elif signals.get('ML_RSI_SIGNAL') == 'SELL' and signals.get('ML_RSI_CONFIDENCE', 0) > 0.7:
            score -= 3
        
        # Add advanced indicators to scoring
        if signals.get('VOLUME_PRESSURE', 0) > 0:
            score += 1
        if signals.get('AVSO_SIGNAL', 0) > 0:
            score += 2
        if signals.get('LRO_SIGNAL', 0) > 0:
            score += 2
        
        # Weight by trend strength
        trend_strength = signals.get('TREND_STRENGTH', 0.5)
        score *= (0.5 + trend_strength)
        
        # Generate recommendation with confidence levels
        if score >= 5:
            return 'STRONG_BUY'
        elif score >= 2:
            return 'BUY'
        elif score >= -1:
            return 'HOLD'
        elif score >= -4:
            return 'SELL'
        else:
            return 'STRONG_SELL'

    def _calculate_confidence(self, signals):
        """Enhanced confidence calculation"""
        confidence_factors = []
        
        # Technical indicator agreement
        tech = signals['technical_indicators']
        indicators_bullish = sum([
            tech['macd']['trend'] == 'bullish',
            tech['obv']['trend'] == 'bullish',
            tech['rsi'] < 50,
            signals['price_trend']['trend'] == 'upward'
        ])
        
        # Calculate agreement percentage
        indicator_confidence = indicators_bullish / 4
        confidence_factors.append(indicator_confidence)
        
        # Volume confidence
        volume_ratio = signals['volume_analysis']['volume_ratio']
        volume_confidence = min(volume_ratio / 2, 1.0)
        confidence_factors.append(volume_confidence)
        
        # RSI extremes confidence
        rsi = tech['rsi']
        if rsi < 30 or rsi > 70:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)
        
        # Return average confidence
        return sum(confidence_factors) / len(confidence_factors)

    # Technical indicator calculations
    def calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, prices):
        """
        Calculate MACD (Moving Average Convergence Divergence)
        Returns: MACD line, Signal line, and Histogram
        """
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_histogram = macd_line - signal_line
        return macd_line, signal_line, macd_histogram

    def calculate_obv(self, prices, volumes):
        """
        Calculate On-Balance Volume (OBV)
        OBV = Previous OBV +/- Current Volume
        """
        df = pd.DataFrame({'close': prices, 'volume': volumes})
        df['price_change'] = df['close'].diff()
        
        obv = []
        prev_obv = 0
        
        for i in range(len(df)):
            if i == 0:
                obv.append(prev_obv)
                continue
                
            if df['price_change'].iloc[i] > 0:
                current_obv = prev_obv + df['volume'].iloc[i]
            elif df['price_change'].iloc[i] < 0:
                current_obv = prev_obv - df['volume'].iloc[i]
            else:
                current_obv = prev_obv
                
            obv.append(current_obv)
            prev_obv = current_obv
            
        return pd.Series(obv, index=df.index)

    def calculate_bollinger_bands(self, prices, period=20):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        return upper_band, lower_band 