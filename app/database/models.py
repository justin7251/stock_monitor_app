from flask_login import UserMixin
from . import db
from datetime import datetime
from sqlalchemy import Index

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user_stocks = db.relationship('UserStock', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Stock(db.Model):
    """Stock data table - stores general stock information and current prices"""
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    current_price = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, index=True)  # Index for time-based queries
    
    # Relationship
    user_stocks = db.relationship('UserStock', backref='stock', lazy=True)
    price_history = db.relationship('StockHistory', backref='stock', lazy=True)


    def __repr__(self):
        return f'<Stock {self.symbol}>'

    # Create indexes
    __table_args__ = (
        Index('idx_symbol', 'symbol'),
        Index('idx_symbol_type', 'symbol', 'type'),
        Index('idx_symbol_date', 'symbol', 'last_updated'),
    )

class StockHistory(db.Model):
    """Historical stock price data"""
    __tablename__ = 'stock_history'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    open_price = db.Column(db.Float)
    high_price = db.Column(db.Float)
    low_price = db.Column(db.Float)
    close_price = db.Column(db.Float)
    volume = db.Column(db.BigInteger)
    
    # Create indexes for efficient querying
    __table_args__ = (
        Index('idx_stock_date', 'stock_id', 'date'),
        Index('idx_date', 'date'),
    )

    def __repr__(self):
        return f'<StockHistory {self.stock_id}:{self.date}>'

class UserStock(db.Model):
    """User's stock holdings"""
    __tablename__ = 'user_stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Create indexes
    __table_args__ = (
        Index('idx_user_stock', 'user_id', 'stock_id'),  # Composite index for user + stock queries
        Index('idx_purchase_date', 'purchase_date'),  # Index for date-based queries
    )

    def __repr__(self):
        return f'<UserStock {self.user_id}:{self.stock_id}>'


class Watchlist(db.Model):
    __tablename__ = 'watchlists'  # Specify the table name

    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each watchlist entry
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key referencing the User model
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)  # Foreign key referencing the Stock model
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Timestamp for when the entry was created
    notes = db.Column(db.Text, nullable=True)  # Optional notes for the watchlist entry

    # Relationships
    user = db.relationship('User', backref='watchlist_items', foreign_keys=[user_id])  # Relationship to the User model
    stock = db.relationship('Stock', backref='watchlist_entries', foreign_keys=[stock_id])  # Relationship to the Stock model

    __table_args__ = (
        db.UniqueConstraint('user_id', 'stock_id', name='idx_user_watchlist'),  # Ensure a user can only have one entry per stock
    )

    def __repr__(self):
        return f'<Watchlist {self.stock_id} for User {self.user_id}>'