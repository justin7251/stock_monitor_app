
# Run database initialization
docker-compose exec app python init_db.py

# Get into the container
docker-compose exec app python app/tasks/stock_updater.py

# Get into the container
docker-compose exec app python app/tasks/load_historical_data.py
