from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    watchlist_items = relationship("WatchlistItem", back_populates="user")
    checkpoints = relationship("UserCheckpoint", back_populates="user")

class Stock(Base):
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, index=True)
    company_name = Column(String(255))
    exchange = Column(String(50))
    
    watchlist_items = relationship("WatchlistItem", back_populates="stock")
    snapshots = relationship("StockSnapshot", back_populates="stock")
    events = relationship("MarketEvent", back_populates="stock")
    checkpoints = relationship("UserCheckpoint", back_populates="stock")

class WatchlistItem(Base):
    __tablename__ = 'watchlist_items'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="watchlist_items")
    stock = relationship("Stock", back_populates="watchlist_items")

class StockSnapshot(Base):
    __tablename__ = 'stock_snapshots'
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    price = Column(Float)
    volume = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50))
    fetched_at = Column(DateTime, default=datetime.utcnow)
    daily_change_percent = Column(Float, default=0.0)
    daily_high = Column(Float)
    daily_low = Column(Float)
    week_52_high = Column(Float)
    week_52_low = Column(Float)
    
    stock = relationship("Stock", back_populates="snapshots")

class UserCheckpoint(Base):
    __tablename__ = 'user_checkpoints'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    last_price = Column(Float)
    last_volume = Column(Float)
    last_checked_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="checkpoints")
    stock = relationship("Stock", back_populates="checkpoints")

class MarketEvent(Base):
    __tablename__ = 'market_events'
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    title = Column(String(500))
    description = Column(Text)
    sentiment = Column(String(20))  # positive, negative, neutral
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(50))  # earnings, news, analyst, announcement
    
    stock = relationship("Stock", back_populates="events")
