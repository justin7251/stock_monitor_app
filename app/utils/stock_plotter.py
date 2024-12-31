from app.utils.indicators import AVAILABLE_INDICATORS, TechnicalIndicators
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import yfinance as yf

class StockPlotter:
    def __init__(self, symbol, period='1mo'):
        self.symbol = symbol
        self.period = period
        self.data = None
        self.active_indicators = {}
        self.load_data()
        
    def load_data(self):
        try:
            ticker = yf.Ticker(self.symbol)
            
            period_mapping = {
                '1mo': ('6mo', 30),
                '3mo': ('1y', 90),
                '6mo': ('2y', 180),
                '1y': ('2y', 365),
                'max': ('max', None)
            }
            
            fetch_period, days_to_show = period_mapping.get(self.period, ('1y', 90))
            
            # Fetch data
            self.data = ticker.history(
                period=fetch_period,
                interval='1d',
                actions=False,
                auto_adjust=True
            )
            
            if self.data.empty:
                raise ValueError(f"No data available for {self.symbol}")
            
            # Ensure index is datetime and timezone-naive
            if self.data.index.tz is not None:
                self.data.index = self.data.index.tz_localize(None)
            
            # Trim to the requested period if needed
            if days_to_show:
                self.data = self.data.tail(days_to_show)
                
            print(f"Data loaded successfully.")
            print(f"Index type: {type(self.data.index)}")
            print(f"First date: {self.data.index[0]}")
            print(f"Last date: {self.data.index[-1]}")
            print(f"Number of rows: {len(self.data)}")
            
        except Exception as e:
            print(f"Error in load_data: {str(e)}")
            raise Exception(f"Error loading data for {self.symbol}: {str(e)}")
            
    def add_indicator(self, indicator_type: str, indicator_name: str):
        key = f"{indicator_type}:{indicator_name}"
        if indicator_type in AVAILABLE_INDICATORS and indicator_name in AVAILABLE_INDICATORS[indicator_type]:
            self.active_indicators[key] = AVAILABLE_INDICATORS[indicator_type][indicator_name]
            
    def create_plot(self):
        try:
            fig = make_subplots(
                rows=1, 
                cols=1, 
                shared_xaxes=True,
                subplot_titles=[f'{self.symbol} Stock Price']
            )

            # Add candlestick
            candlestick = go.Candlestick(
                x=self.data.index,
                open=self.data['Open'],
                high=self.data['High'],
                low=self.data['Low'],
                close=self.data['Close'],
                name=self.symbol,
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            )
            fig.add_trace(candlestick)

            # Add all active indicators
            for key, indicator in self.active_indicators.items():
                indicator_type, name = key.split(':')
                
                if indicator_type == 'SMA':
                    period = indicator.params['period']
                    sma = self.data['Close'].rolling(window=period, min_periods=1).mean()
                    
                    sma_trace = go.Scatter(
                        x=self.data.index,
                        y=sma,
                        name=f'{name}',
                        line=dict(color=indicator.color, width=1.5)
                    )
                    fig.add_trace(sma_trace)
                
                elif 'Bollinger' in name:
                    upper, middle, lower = indicator.function(self.data, **indicator.params)
                    
                    # Add traces in specific order: lower, upper, middle
                    # This ensures proper fill
                    lower_trace = go.Scatter(
                        x=self.data.index,
                        y=lower,
                        name='Lower Band',
                        line=dict(color=indicator.color, width=1, dash='dash'),
                        opacity=0.7,
                        showlegend=True
                    )
                    
                    upper_trace = go.Scatter(
                        x=self.data.index,
                        y=upper,
                        name='Upper Band',
                        line=dict(color=indicator.color, width=1, dash='dash'),
                        fill='tonexty',  # Fill to the lower band
                        fillcolor='rgba(76, 175, 80, 0.1)',  # Light green with transparency
                        opacity=0.7,
                        showlegend=True
                    )
                    
                    middle_trace = go.Scatter(
                        x=self.data.index,
                        y=middle,
                        name='Middle Band',
                        line=dict(color=indicator.color, width=1.5),
                        showlegend=True
                    )
                    
                    # Add traces in specific order
                    fig.add_trace(lower_trace)
                    fig.add_trace(upper_trace)
                    fig.add_trace(middle_trace)

            # Configure tick settings based on period
            if self.period == '1mo':
                dtick = 'W1'
                tickformat = '%Y-%m-%d'
            elif self.period == '3mo' or self.period == '6mo':
                dtick = 'M1'
                tickformat = '%Y-%m-%d'
            elif self.period == '1y':
                dtick = 'M1'
                tickformat = '%Y-%m'
            else:  # max
                dtick = 'M4'
                tickformat = '%Y-%m'

            # Update layout with dynamic tick settings
            fig.update_layout(
                xaxis=dict(
                    title=dict(
                        text='Date',
                        font=dict(size=16, color='white'),
                        standoff=20
                    ),
                    showgrid=True,
                    gridcolor='rgba(128,128,128,0.2)',
                    gridwidth=1,
                    tickfont=dict(size=12, color='white'),
                    rangeslider=dict(visible=False),
                    type='date',
                    dtick=dtick,
                    tickformat=tickformat,
                    showticklabels=True,
                    side='bottom',
                    showline=True,
                    linecolor='rgba(128,128,128,0.4)',
                    linewidth=2,
                    fixedrange=False,
                    automargin=True,
                    tickangle=45
                ),
                yaxis=dict(
                    title=dict(
                        text='Price ($)',
                        font=dict(size=16, color='white'),
                        standoff=20
                    ),
                    showgrid=True,
                    gridcolor='rgba(128,128,128,0.2)',
                    gridwidth=1,
                    tickfont=dict(size=12, color='white'),
                    tickprefix='$',
                    tickformat=',.2f',
                    showticklabels=True,
                    side='left',
                    showline=True,
                    linecolor='rgba(128,128,128,0.4)',
                    linewidth=2
                ),
                template='plotly_dark',
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(0,0,0,0.5)',
                    font=dict(color='white', size=12)
                ),
            )

            # Force axis labels to be visible
            fig.update_xaxes(
                title_standoff=25,  # Increase space between axis and its label
                showspikes=True,
                spikecolor='gray',
                spikesnap='cursor',
                spikemode='across',
                spikethickness=1,
                showline=True,
                showgrid=True,
                showticklabels=True,
                ticks='outside',
                ticklen=8,  # Increase tick length
                tickwidth=2,  # Increase tick width
                tickcolor='white'
            )
            
            fig.update_yaxes(
                title_standoff=25,  # Increase space between axis and its label
                showspikes=True,
                spikecolor='gray',
                spikesnap='cursor',
                spikemode='across',
                spikethickness=1,
                showline=True,
                showgrid=True,
                showticklabels=True,
                ticks='outside',
                ticklen=8,  # Increase tick length
                tickwidth=2,  # Increase tick width
                tickcolor='white'
            )

            # Create the plot HTML with custom CSS for modebar
            plot_html = fig.to_html(
                full_html=False,
                include_plotlyjs='cdn',
                config={
                    'displayModeBar': True,
                    'scrollZoom': True,
                    'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape'],
                    'displaylogo': False,
                    'showAxisDragHandles': True,
                    'showAxisRangeEntryBoxes': True,
                    'showTips': True,
                    'modeBarButtonsToRemove': [],
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': f'{self.symbol}_chart',
                        'height': 1000,
                        'width': 1200,
                        'scale': 2
                    }
                }
            )

            # Add custom CSS to force modebar styling
            custom_css = """
            <style>
                .modebar {
                    background-color: transparent !important;
                }
                .modebar-btn path {
                    fill: black !important;
                }
                .modebar-btn.active path {
                    fill: rgba(0, 0, 0, 0.7) !important;
                }
                .modebar-btn:hover path {
                    fill: rgba(0, 0, 0, 0.7) !important;
                }
            </style>
            """

            # Insert the CSS before the plot
            return custom_css + plot_html

        except Exception as e:
            print(f"Error in create_plot: {str(e)}")
            print(f"Data index sample: {self.data.index[:5]}")
            print(f"Data shape: {self.data.shape}")
            raise Exception(f"Error creating plot: {str(e)}") 