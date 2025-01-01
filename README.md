# Stock Monitor

A real-time stock monitoring and portfolio management system built with Flask and Docker.

## Features

- **Real-time Stock Tracking**: Monitor stock prices with 15-minute updates during market hours
- **Portfolio Management**: Track your stock holdings and performance
- **User Authentication**: Secure login and registration system
- **Stock Search**: Quick search functionality for stocks with real-time suggestions
- **Interactive Dashboard**: Visual representation of portfolio performance
- **Automated Updates**: Scheduled stock price updates using cron jobs
- **Historical Data**: Track and view historical stock performance

## Tech Stack

- **Backend**: Python/Flask
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLAlchemy
- **Stock Data**: yfinance API
- **Task Scheduling**: APScheduler/Cron
- **Containerization**: Docker
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF


## Usage

1. Register a new account at `/register`
2. Login at `/login`
3. Add stocks to your portfolio using the search function
4. Monitor your portfolio performance on the dashboard
5. View detailed stock information by clicking on individual stocks

## API Endpoints

- `/api/portfolio/value`: Get portfolio value history
- `/api/stocks/performance`: Get stock performance data
- `/api/portfolio/stats`: Get current portfolio statistics
- `/api/search/stocks`: Search for stocks

## Scheduled Tasks

The system runs several automated tasks:
- Stock price updates every 15 minutes during market hours (9:30 AM - 4:00 PM EST)
- End-of-day updates at 4:30 PM EST
- Pre-market updates at 9:00 AM EST

## Development
docker-compose up -d

# Future features
These features would enhance your application with:
Advanced monitoring capabilities
Better analytics
Social engagement
Risk management
Portfolio optimization
Data export options
Market awareness
Income tracking
Technical analysis
News integration


# Run database initializationz
docker-compose exec app python init_db.py
# Run database initialization
docker-compose exec app python init_db.py

# Get into the container
docker-compose exec app python app/tasks/stock_updater.py

# Get into the container
docker-compose exec app python app/tasks/load_historical_data.py
