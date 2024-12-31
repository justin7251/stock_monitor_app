from dataclasses import dataclass
from typing import Callable, Dict, Any
import pandas as pd
import numpy as np

@dataclass
class Indicator:
    name: str
    function: Callable
    params: Dict[str, Any]
    color: str
    visible: bool = True
    
class TechnicalIndicators:
    @staticmethod
    def calculate_sma(data: pd.DataFrame, period: int) -> pd.Series:
        return data['Close'].rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(data: pd.DataFrame, period: int) -> pd.Series:
        return data['Close'].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20, std: int = 2):
        middle_band = data['Close'].rolling(window=period).mean()
        std_dev = data['Close'].rolling(window=period).std()
        upper_band = middle_band + (std_dev * std)
        lower_band = middle_band - (std_dev * std)
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
        exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal_line

AVAILABLE_INDICATORS = {
    'SMA': {
        '20 SMA': Indicator(
            name='20 SMA',
            function=TechnicalIndicators.calculate_sma,
            params={'period': 20},
            color='#2196F3',
            visible=True
        ),
        '50 SMA': Indicator(
            name='50 SMA',
            function=TechnicalIndicators.calculate_sma,
            params={'period': 50},
            color='#FFA726',
            visible=True
        ),
        '100 SMA': Indicator(
            name='100 SMA',
            function=TechnicalIndicators.calculate_sma,
            params={'period': 100},
            color='#EF5350',
            visible=True
        )
    },
    'Bollinger Bands': {
        'Bollinger': Indicator(
            name='Bollinger Bands',
            function=TechnicalIndicators.calculate_bollinger_bands,
            params={'period': 20, 'std': 2},
            color='#4CAF50',
            visible=True
        )
    },
    'RSI': {
        'RSI': Indicator(
            name='RSI',
            function=TechnicalIndicators.calculate_rsi,
            params={'period': 14},
            color='#9C27B0',
            visible=True
        )
    },
    'MACD': {
        'MACD': Indicator(
            name='MACD',
            function=TechnicalIndicators.calculate_macd,
            params={'fast': 12, 'slow': 26, 'signal': 9},
            color='#FF5722',
            visible=True
        )
    }
} 