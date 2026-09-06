from models.database_models import User, Stock, WatchlistItem, StockSnapshot, UserCheckpoint, MarketEvent
from database import get_db_context
from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_database():
    """Seed database with initial demo data"""
    
    with get_db_context() as db:
        # Check if already seeded
        existing_user = db.query(User).filter(User.email == "demo@marketpulse.com").first()
        if existing_user:
            print("Database already seeded")
            return
        
        print("Seeding database...")
        
        # Create demo user
        try:
            hashed_pw = pwd_context.hash("demo123")
        except Exception as e:
            print(f"Password hash warning: {e}")
            # Simple fallback hash for demo
            hashed_pw = "demo_hashed_password_placeholder"
        
        demo_user = User(
            email="demo@marketpulse.com",
            hashed_password=hashed_pw
        )
        db.add(demo_user)
        db.flush()
        print(f"Created demo user with ID: {demo_user.id}")
        
        # Create stocks
        stocks_data = [
            {'ticker': 'NVDA', 'company_name': 'NVIDIA Corporation', 'exchange': 'NASDAQ'},
            {'ticker': 'AAPL', 'company_name': 'Apple Inc.', 'exchange': 'NASDAQ'},
            {'ticker': 'TSLA', 'company_name': 'Tesla, Inc.', 'exchange': 'NASDAQ'},
            {'ticker': 'MSFT', 'company_name': 'Microsoft Corporation', 'exchange': 'NASDAQ'},
            {'ticker': 'AMZN', 'company_name': 'Amazon.com, Inc.', 'exchange': 'NASDAQ'},
            {'ticker': 'GOOGL', 'company_name': 'Alphabet Inc.', 'exchange': 'NASDAQ'},
            {'ticker': 'META', 'company_name': 'Meta Platforms, Inc.', 'exchange': 'NASDAQ'},
        ]
        
        stocks = {}
        for stock_data in stocks_data:
            stock = Stock(**stock_data)
            db.add(stock)
            db.flush()
            stocks[stock_data['ticker']] = stock
        
        # Add some stocks to watchlist
        for ticker in ['NVDA', 'AAPL', 'TSLA', 'AMZN']:
            watchlist_item = WatchlistItem(
                user_id=demo_user.id,
                stock_id=stocks[ticker].id
            )
            db.add(watchlist_item)
        
        # Create previous snapshots (5 hours ago)
        previous_time = datetime.utcnow() - timedelta(hours=5)
        
        previous_snapshots = {
            'NVDA': {'price': 175.00, 'volume': 1200000},
            'AAPL': {'price': 183.00, 'volume': 1800000},
            'TSLA': {'price': 257.00, 'volume': 2200000},
            'AMZN': {'price': 167.50, 'volume': 1900000},
        }
        
        for ticker, data in previous_snapshots.items():
            snapshot = StockSnapshot(
                stock_id=stocks[ticker].id,
                price=data['price'],
                volume=data['volume'],
                timestamp=previous_time,
                source='demo',
                fetched_at=previous_time,
                daily_change_percent=0.0,
                daily_high=data['price'] * 1.02,
                daily_low=data['price'] * 0.98,
                week_52_high=data['price'] * 1.25,
                week_52_low=data['price'] * 0.75
            )
            db.add(snapshot)
            
            # Create checkpoint
            checkpoint = UserCheckpoint(
                user_id=demo_user.id,
                stock_id=stocks[ticker].id,
                last_price=data['price'],
                last_volume=data['volume'],
                last_checked_at=previous_time
            )
            db.add(checkpoint)
        
        # Create current snapshots
        current_time = datetime.utcnow()
        
        current_snapshots = {
            'NVDA': {'price': 189.70, 'volume': 3100000, 'daily_change': 8.4},
            'AAPL': {'price': 185.01, 'volume': 1800000, 'daily_change': 1.1},
            'TSLA': {'price': 244.66, 'volume': 2500000, 'daily_change': -4.8},
            'AMZN': {'price': 178.05, 'volume': 2800000, 'daily_change': 6.3},
        }
        
        for ticker, data in current_snapshots.items():
            snapshot = StockSnapshot(
                stock_id=stocks[ticker].id,
                price=data['price'],
                volume=data['volume'],
                timestamp=current_time,
                source='demo',
                fetched_at=current_time,
                daily_change_percent=data['daily_change'],
                daily_high=data['price'] * 1.02,
                daily_low=data['price'] * 0.98,
                week_52_high=data['price'] * 1.25,
                week_52_low=data['price'] * 0.75
            )
            db.add(snapshot)
        
        # Add market events for NVDA
        events = [
            {
                'stock_id': stocks['NVDA'].id,
                'title': 'NVIDIA announces new AI chip architecture',
                'description': 'Company unveils next-generation GPU technology for AI workloads',
                'sentiment': 'positive',
                'event_type': 'announcement',
                'timestamp': current_time - timedelta(hours=2)
            },
            {
                'stock_id': stocks['NVDA'].id,
                'title': 'Analysts raise price target on strong AI demand',
                'description': 'Multiple analysts upgrade NVIDIA stock citing robust AI market growth',
                'sentiment': 'positive',
                'event_type': 'analyst',
                'timestamp': current_time - timedelta(hours=4)
            },
            {
                'stock_id': stocks['TSLA'].id,
                'title': 'Tesla reports delivery numbers below expectations',
                'description': 'Q4 deliveries fall short of analyst estimates',
                'sentiment': 'negative',
                'event_type': 'news',
                'timestamp': current_time - timedelta(hours=3)
            },
            {
                'stock_id': stocks['AMZN'].id,
                'title': 'Amazon announces major AWS cloud expansion',
                'description': 'AWS to open new data centers in multiple regions',
                'sentiment': 'positive',
                'event_type': 'announcement',
                'timestamp': current_time - timedelta(hours=1)
            }
        ]
        
        for event_data in events:
            event = MarketEvent(**event_data)
            db.add(event)
        
        db.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()
