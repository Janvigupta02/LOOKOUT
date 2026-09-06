from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from database import get_db
from models.database_models import User, Stock, WatchlistItem, StockSnapshot, UserCheckpoint, MarketEvent
from providers import get_market_provider
from services import ChangeDetector, ExplanationService
from auth.auth_service import get_current_user_optional
import os

router = APIRouter()

# Pydantic models
class StockSearch(BaseModel):
    ticker: str
    company_name: str
    exchange: str

class WatchlistAdd(BaseModel):
    ticker: str

class StockQuote(BaseModel):
    ticker: str
    company_name: str
    price: float
    daily_change_percent: float
    volume: float
    timestamp: str
    source: str

class ChangeInfo(BaseModel):
    ticker: str
    company_name: str
    current_price: float
    price_change_percent: float
    volume_change_percent: float
    attention_score: int
    severity: str
    reasons: List[str]
    explanation: str
    status_emoji: str

class DashboardResponse(BaseModel):
    last_checked: Optional[str]
    hours_since_check: Optional[float]
    needs_attention_count: int
    significant_count: int
    worth_watching_count: int
    normal_count: int
    changes: List[ChangeInfo]
    summary: str

# Get current user (simplified for demo - supports both JWT and demo mode)
def get_current_user(user: User = Depends(get_current_user_optional)) -> User:
    """Get current user - works with JWT token or falls back to demo user"""
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please login or run seed_database.py")
    return user

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "MarketPulse API"}

@router.get("/stocks")
def get_all_stocks(db: Session = Depends(get_db)):
    """Get all available stocks for dashboard"""
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    provider = get_market_provider(demo_mode)
    
    # Get all stocks from database or demo stocks
    stocks = db.query(Stock).all()
    
    if not stocks:
        # If no stocks in DB, show demo stocks
        demo_tickers = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'META']
        result = []
        for ticker in demo_tickers:
            quote = provider.get_quote(ticker)
            company_info = provider.get_company_info(ticker)
            if quote and company_info:
                result.append({
                    'symbol': ticker,
                    'name': company_info['company_name'],
                    'price': quote['price'],
                    'change': quote['daily_change_percent']
                })
        return result
    
    result = []
    for stock in stocks:
        quote = provider.get_quote(stock.ticker)
        if quote:
            result.append({
                'symbol': stock.ticker,
                'name': stock.company_name,
                'price': quote['price'],
                'change': quote['daily_change_percent']
            })
    
    return result

@router.get("/watchlist")
def get_watchlist(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get user's watchlist"""
    watchlist_items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id
    ).all()
    
    if not watchlist_items:
        return []
    
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    provider = get_market_provider(demo_mode)
    
    result = []
    for item in watchlist_items:
        stock = item.stock
        quote = provider.get_quote(stock.ticker)
        
        if quote:
            # Get checkpoint
            checkpoint = db.query(UserCheckpoint).filter(
                UserCheckpoint.user_id == user.id,
                UserCheckpoint.stock_id == stock.id
            ).first()
            
            change_since_check = 0
            if checkpoint and checkpoint.last_price:
                change_since_check = ((quote['price'] - checkpoint.last_price) / checkpoint.last_price) * 100
            
            result.append({
                'id': item.id,
                'symbol': stock.ticker,
                'name': stock.company_name,
                'price': quote['price'],
                'change': quote['daily_change_percent'],
                'change_since_check': round(change_since_check, 2),
                'volume': quote['volume'],
                'timestamp': quote['timestamp'],
                'source': quote['source']
            })
    
    return result

@router.post("/watchlist/{symbol}")
def toggle_watchlist(
    symbol: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Add or remove stock from watchlist"""
    ticker = symbol.upper()
    
    # Check if stock exists
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    
    if not stock:
        # Get stock info from provider
        demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
        provider = get_market_provider(demo_mode)
        company_info = provider.get_company_info(ticker)
        
        if not company_info:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        
        # Create stock
        stock = Stock(
            ticker=ticker,
            company_name=company_info['company_name'],
            exchange=company_info['exchange']
        )
        db.add(stock)
        db.flush()
    
    # Check if already in watchlist
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id,
        WatchlistItem.stock_id == stock.id
    ).first()
    
    if existing:
        # Remove from watchlist
        db.delete(existing)
        db.commit()
        return {"message": f"{ticker} removed from watchlist", "action": "removed"}
    
    # Add to watchlist
    watchlist_item = WatchlistItem(
        user_id=user.id,
        stock_id=stock.id
    )
    db.add(watchlist_item)
    
    # Create initial snapshot and checkpoint
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    provider = get_market_provider(demo_mode)
    quote = provider.get_quote(ticker)
    
    if quote:
        snapshot = StockSnapshot(
            stock_id=stock.id,
            price=quote['price'],
            volume=quote['volume'],
            timestamp=datetime.utcnow(),
            source=quote['source'],
            fetched_at=datetime.utcnow(),
            daily_change_percent=quote.get('daily_change_percent', 0),
            daily_high=quote.get('daily_high'),
            daily_low=quote.get('daily_low'),
            week_52_high=quote.get('week_52_high'),
            week_52_low=quote.get('week_52_low')
        )
        db.add(snapshot)
        
        checkpoint = UserCheckpoint(
            user_id=user.id,
            stock_id=stock.id,
            last_price=quote['price'],
            last_volume=quote['volume'],
            last_checked_at=datetime.utcnow()
        )
        db.add(checkpoint)
    
    db.commit()
    
    return {"message": f"{ticker} added to watchlist", "action": "added"}

@router.get("/stocks/{symbol}/explain")
def explain_stock_changes(
    symbol: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get explanation for stock changes"""
    ticker = symbol.upper()
    
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    provider = get_market_provider(demo_mode)
    quote = provider.get_quote(ticker)
    
    if not quote:
        return {"explanation": "Unable to fetch current data"}
    
    # Get checkpoint if exists
    checkpoint = None
    if stock:
        checkpoint = db.query(UserCheckpoint).filter(
            UserCheckpoint.user_id == user.id,
            UserCheckpoint.stock_id == stock.id
        ).first()
    
    change_detector = ChangeDetector()
    explanation_service = ExplanationService()
    
    previous_data = {}
    if checkpoint:
        previous_data = {
            'price': checkpoint.last_price,
            'volume': checkpoint.last_volume
        }
    
    current_data = {
        'price': quote['price'],
        'volume': quote['volume'],
        'company_name': provider.get_company_info(ticker)['company_name'] if provider.get_company_info(ticker) else ticker,
        'week_52_high': quote.get('week_52_high'),
        'week_52_low': quote.get('week_52_low')
    }
    
    events_data = []
    if stock:
        recent_events = db.query(MarketEvent).filter(
            MarketEvent.stock_id == stock.id,
            MarketEvent.timestamp >= datetime.utcnow() - timedelta(days=7)
        ).all()
        events_data = [{'title': e.title, 'sentiment': e.sentiment} for e in recent_events]
    
    change_info = change_detector.detect_meaningful_changes(
        previous_data,
        current_data,
        events_data
    )
    
    explanation = explanation_service.generate_explanation(
        ticker,
        change_info,
        current_data
    )
    
    return {"explanation": explanation}

@router.get("/stocks/search")
def search_stocks(query: str = ""):
    """Search for stocks"""
    if not query or len(query) < 1:
        return []
    
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    provider = get_market_provider(demo_mode)
    
    results = provider.search_stocks(query)
    
    # Format for frontend
    formatted = []
    for r in results:
        quote = provider.get_quote(r['ticker'])
        if quote:
            formatted.append({
                'symbol': r['ticker'],
                'name': r['company_name'],
                'price': quote['price'],
                'change': quote['daily_change_percent']
            })
    
    return formatted

@router.get("/stocks/{ticker}")
def get_stock_detail(
    ticker: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get detailed stock information"""
    ticker = ticker.upper()
    
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Get current quote
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    provider = get_market_provider(demo_mode)
    quote = provider.get_quote(ticker)
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not available")
    
    # Get checkpoint
    checkpoint = db.query(UserCheckpoint).filter(
        UserCheckpoint.user_id == user.id,
        UserCheckpoint.stock_id == stock.id
    ).first()
    
    # Calculate changes
    change_detector = ChangeDetector()
    explanation_service = ExplanationService()
    
    previous_data = {}
    if checkpoint:
        previous_data = {
            'price': checkpoint.last_price,
            'volume': checkpoint.last_volume
        }
    
    current_data = {
        'price': quote['price'],
        'volume': quote['volume'],
        'company_name': stock.company_name,
        'week_52_high': quote.get('week_52_high'),
        'week_52_low': quote.get('week_52_low')
    }
    
    # Get events
    recent_events = db.query(MarketEvent).filter(
        MarketEvent.stock_id == stock.id,
        MarketEvent.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).all()
    
    events_data = [{'title': e.title, 'sentiment': e.sentiment} for e in recent_events]
    
    change_info = change_detector.detect_meaningful_changes(
        previous_data,
        current_data,
        events_data
    )
    
    explanation = explanation_service.generate_explanation(
        ticker,
        change_info,
        current_data
    )
    
    # Get price history
    history = db.query(StockSnapshot).filter(
        StockSnapshot.stock_id == stock.id
    ).order_by(StockSnapshot.timestamp.desc()).limit(20).all()
    
    history_data = [{
        'timestamp': snap.timestamp.isoformat(),
        'price': snap.price,
        'volume': snap.volume
    } for snap in reversed(history)]
    
    # Get news
    news = provider.get_news(ticker)
    
    # Check if in watchlist
    in_watchlist = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id,
        WatchlistItem.stock_id == stock.id
    ).first() is not None
    
    return {
        'ticker': ticker,
        'company_name': stock.company_name,
        'exchange': stock.exchange,
        'price': quote['price'],
        'daily_change_percent': quote['daily_change_percent'],
        'change_since_check': change_info['price_change_percent'],
        'volume': quote['volume'],
        'volume_change': change_info['volume_change_percent'],
        'attention_score': change_info['attention_score'],
        'severity': change_info['severity'],
        'reasons': change_info['reasons'],
        'explanation': explanation,
        'timestamp': quote['timestamp'],
        'source': quote['source'],
        'history': history_data,
        'events': news,
        'last_checked': checkpoint.last_checked_at.isoformat() if checkpoint else None,
        'in_watchlist': in_watchlist,
        'daily_high': quote.get('daily_high'),
        'daily_low': quote.get('daily_low'),
        'week_52_high': quote.get('week_52_high'),
        'week_52_low': quote.get('week_52_low')
    }

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get dashboard with 'What Did I Miss?' summary"""
    watchlist_items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id
    ).all()
    
    if not watchlist_items:
        return DashboardResponse(
            last_checked=None,
            hours_since_check=None,
            needs_attention_count=0,
            significant_count=0,
            worth_watching_count=0,
            normal_count=0,
            changes=[],
            summary="Your watchlist is empty. Add some stocks to get started!"
        )
    
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    provider = get_market_provider(demo_mode)
    change_detector = ChangeDetector()
    explanation_service = ExplanationService()
    
    changes = []
    oldest_check = None
    
    for item in watchlist_items:
        stock = item.stock
        
        # Get checkpoint
        checkpoint = db.query(UserCheckpoint).filter(
            UserCheckpoint.user_id == user.id,
            UserCheckpoint.stock_id == stock.id
        ).first()
        
        if not checkpoint:
            continue
        
        if not oldest_check or checkpoint.last_checked_at < oldest_check:
            oldest_check = checkpoint.last_checked_at
        
        # Get current quote
        quote = provider.get_quote(stock.ticker)
        if not quote:
            continue
        
        previous_data = {
            'price': checkpoint.last_price,
            'volume': checkpoint.last_volume
        }
        
        current_data = {
            'price': quote['price'],
            'volume': quote['volume'],
            'company_name': stock.company_name,
            'week_52_high': quote.get('week_52_high'),
            'week_52_low': quote.get('week_52_low')
        }
        
        # Get recent events
        recent_events = db.query(MarketEvent).filter(
            MarketEvent.stock_id == stock.id,
            MarketEvent.timestamp >= checkpoint.last_checked_at
        ).all()
        
        events_data = [{'title': e.title, 'sentiment': e.sentiment} for e in recent_events]
        
        # Detect changes
        change_info = change_detector.detect_meaningful_changes(
            previous_data,
            current_data,
            events_data
        )
        
        # Generate explanation
        explanation = explanation_service.generate_explanation(
            stock.ticker,
            change_info,
            current_data
        )
        
        # Map severity to emoji
        emoji_map = {
            'needs_attention': '🔴',
            'significant': '🟠',
            'worth_watching': '🟡',
            'normal': '🟢'
        }
        
        changes.append(ChangeInfo(
            ticker=stock.ticker,
            company_name=stock.company_name,
            current_price=quote['price'],
            price_change_percent=change_info['price_change_percent'],
            volume_change_percent=change_info['volume_change_percent'],
            attention_score=change_info['attention_score'],
            severity=change_info['severity'],
            reasons=change_info['reasons'],
            explanation=explanation,
            status_emoji=emoji_map[change_info['severity']]
        ))
    
    # Sort by attention score
    changes.sort(key=lambda x: x.attention_score, reverse=True)
    
    # Count by severity
    needs_attention = sum(1 for c in changes if c.severity == 'needs_attention')
    significant = sum(1 for c in changes if c.severity == 'significant')
    worth_watching = sum(1 for c in changes if c.severity == 'worth_watching')
    normal = sum(1 for c in changes if c.severity == 'normal')
    
    # Calculate time since check
    hours_since = None
    if oldest_check:
        time_diff = datetime.utcnow() - oldest_check
        hours_since = time_diff.total_seconds() / 3600
    
    # Generate summary
    summary = explanation_service.generate_batch_summary([c.dict() for c in changes])
    
    return DashboardResponse(
        last_checked=oldest_check.isoformat() if oldest_check else None,
        hours_since_check=round(hours_since, 1) if hours_since else None,
        needs_attention_count=needs_attention,
        significant_count=significant,
        worth_watching_count=worth_watching,
        normal_count=normal,
        changes=changes,
        summary=summary
    )

@router.post("/checkpoint")
def update_checkpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Update user checkpoints for all watchlist stocks"""
    watchlist_items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id
    ).all()
    
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    provider = get_market_provider(demo_mode)
    
    updated_count = 0
    
    for item in watchlist_items:
        stock = item.stock
        quote = provider.get_quote(stock.ticker)
        
        if not quote:
            continue
        
        # Update or create checkpoint
        checkpoint = db.query(UserCheckpoint).filter(
            UserCheckpoint.user_id == user.id,
            UserCheckpoint.stock_id == stock.id
        ).first()
        
        if checkpoint:
            checkpoint.last_price = quote['price']
            checkpoint.last_volume = quote['volume']
            checkpoint.last_checked_at = datetime.utcnow()
        else:
            checkpoint = UserCheckpoint(
                user_id=user.id,
                stock_id=stock.id,
                last_price=quote['price'],
                last_volume=quote['volume'],
                last_checked_at=datetime.utcnow()
            )
            db.add(checkpoint)
        
        # Store snapshot
        snapshot = StockSnapshot(
            stock_id=stock.id,
            price=quote['price'],
            volume=quote['volume'],
            timestamp=datetime.utcnow(),
            source=quote['source'],
            fetched_at=datetime.utcnow(),
            daily_change_percent=quote.get('daily_change_percent', 0),
            daily_high=quote.get('daily_high'),
            daily_low=quote.get('daily_low'),
            week_52_high=quote.get('week_52_high'),
            week_52_low=quote.get('week_52_low')
        )
        db.add(snapshot)
        
        updated_count += 1
    
    db.commit()
    
    return {"message": f"Updated {updated_count} checkpoints"}

@router.post("/refresh")
def refresh_data(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Refresh market data for all watchlist stocks"""
    return update_checkpoint(db, user)
