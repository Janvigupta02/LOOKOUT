from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random
import requests
import os
from time import sleep

class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    @abstractmethod
    def get_quote(self, ticker: str) -> Optional[Dict]:
        """Get current quote for a ticker"""
        pass
    
    @abstractmethod
    def search_stocks(self, query: str) -> List[Dict]:
        """Search for stocks by name or ticker"""
        pass
    
    @abstractmethod
    def get_company_info(self, ticker: str) -> Optional[Dict]:
        """Get company information"""
        pass
    
    @abstractmethod
    def get_news(self, ticker: str) -> List[Dict]:
        """Get recent news for a ticker"""
        pass

class DemoMarketDataProvider(MarketDataProvider):
    """Demo provider with realistic simulated data"""
    
    def __init__(self):
        self.stocks_db = {
            'NVDA': {
                'ticker': 'NVDA',
                'company_name': 'NVIDIA Corporation',
                'exchange': 'NASDAQ',
                'base_price': 175.00,
                'volatility': 0.08
            },
            'AAPL': {
                'ticker': 'AAPL',
                'company_name': 'Apple Inc.',
                'exchange': 'NASDAQ',
                'base_price': 185.00,
                'volatility': 0.02
            },
            'TSLA': {
                'ticker': 'TSLA',
                'company_name': 'Tesla, Inc.',
                'exchange': 'NASDAQ',
                'base_price': 245.00,
                'volatility': 0.05
            },
            'MSFT': {
                'ticker': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'exchange': 'NASDAQ',
                'base_price': 420.00,
                'volatility': 0.02
            },
            'AMZN': {
                'ticker': 'AMZN',
                'company_name': 'Amazon.com, Inc.',
                'exchange': 'NASDAQ',
                'base_price': 178.00,
                'volatility': 0.03
            },
            'GOOGL': {
                'ticker': 'GOOGL',
                'company_name': 'Alphabet Inc.',
                'exchange': 'NASDAQ',
                'base_price': 145.00,
                'volatility': 0.025
            },
            'META': {
                'ticker': 'META',
                'company_name': 'Meta Platforms, Inc.',
                'exchange': 'NASDAQ',
                'base_price': 512.00,
                'volatility': 0.04
            }
        }
        
        # Seed for deterministic demo
        random.seed(42)
    
    def get_quote(self, ticker: str) -> Optional[Dict]:
        """Get simulated quote"""
        ticker = ticker.upper()
        if ticker not in self.stocks_db:
            return None
        
        stock_info = self.stocks_db[ticker]
        base_price = stock_info['base_price']
        volatility = stock_info['volatility']
        
        # Simulate different scenarios for demo
        if ticker == 'NVDA':
            # High movement scenario
            price = base_price * 1.084
            volume = 3100000
            daily_change = 8.4
        elif ticker == 'TSLA':
            # Moderate movement
            price = base_price * 0.952
            volume = 2500000
            daily_change = -4.8
        elif ticker == 'AAPL':
            # Low movement
            price = base_price * 1.011
            volume = 1800000
            daily_change = 1.1
        elif ticker == 'AMZN':
            # Meaningful event
            price = base_price * 1.063
            volume = 2800000
            daily_change = 6.3
        else:
            # Normal movement
            price = base_price * (1 + random.uniform(-0.02, 0.02))
            volume = random.randint(1000000, 2000000)
            daily_change = ((price - base_price) / base_price) * 100
        
        return {
            'ticker': ticker,
            'price': round(price, 2),
            'volume': volume,
            'daily_change_percent': round(daily_change, 2),
            'daily_high': round(price * 1.02, 2),
            'daily_low': round(price * 0.98, 2),
            'week_52_high': round(price * 1.25, 2),
            'week_52_low': round(price * 0.75, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'demo'
        }
    
    def search_stocks(self, query: str) -> List[Dict]:
        """Search stocks in demo database"""
        query = query.upper()
        results = []
        
        for ticker, info in self.stocks_db.items():
            if query in ticker or query in info['company_name'].upper():
                results.append({
                    'ticker': ticker,
                    'company_name': info['company_name'],
                    'exchange': info['exchange']
                })
        
        return results
    
    def get_company_info(self, ticker: str) -> Optional[Dict]:
        """Get company info"""
        ticker = ticker.upper()
        if ticker not in self.stocks_db:
            return None
        
        info = self.stocks_db[ticker]
        return {
            'ticker': ticker,
            'company_name': info['company_name'],
            'exchange': info['exchange']
        }
    
    def get_news(self, ticker: str) -> List[Dict]:
        """Get simulated news"""
        ticker = ticker.upper()
        
        news_templates = {
            'NVDA': [
                {
                    'title': 'NVIDIA announces new AI chip architecture',
                    'description': 'Company unveils next-generation GPU technology',
                    'sentiment': 'positive',
                    'event_type': 'announcement',
                    'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat()
                },
                {
                    'title': 'Analysts raise price target on strong AI demand',
                    'description': 'Multiple analysts upgrade NVIDIA stock',
                    'sentiment': 'positive',
                    'event_type': 'analyst',
                    'timestamp': (datetime.utcnow() - timedelta(hours=5)).isoformat()
                }
            ],
            'TSLA': [
                {
                    'title': 'Tesla reports delivery numbers below expectations',
                    'description': 'Q4 deliveries fall short of analyst estimates',
                    'sentiment': 'negative',
                    'event_type': 'news',
                    'timestamp': (datetime.utcnow() - timedelta(hours=3)).isoformat()
                }
            ],
            'AMZN': [
                {
                    'title': 'Amazon announces major cloud expansion',
                    'description': 'AWS to open new data centers globally',
                    'sentiment': 'positive',
                    'event_type': 'announcement',
                    'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat()
                }
            ]
        }
        
        return news_templates.get(ticker, [])

class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage API integration for real market data"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.demo_fallback = DemoMarketDataProvider()
        self.rate_limit_delay = 12  # Alpha Vantage free tier: 5 calls/min
    
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make API request with rate limiting"""
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                print(f"Alpha Vantage Error: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                print(f"Alpha Vantage Rate Limit: {data['Note']}")
                sleep(60)  # Wait 1 minute on rate limit
                return None
            
            sleep(self.rate_limit_delay)  # Rate limiting
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            return None
    
    def get_quote(self, ticker: str) -> Optional[Dict]:
        """Get real-time quote from Alpha Vantage"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker.upper()
        }
        
        data = self._make_request(params)
        
        if not data or 'Global Quote' not in data:
            print(f"Falling back to demo data for {ticker}")
            return self.demo_fallback.get_quote(ticker)
        
        quote = data['Global Quote']
        
        if not quote:
            return self.demo_fallback.get_quote(ticker)
        
        try:
            price = float(quote.get('05. price', 0))
            change_percent = float(quote.get('10. change percent', '0').replace('%', ''))
            volume = int(quote.get('06. volume', 0))
            high = float(quote.get('03. high', price))
            low = float(quote.get('04. low', price))
            
            return {
                'ticker': ticker.upper(),
                'price': round(price, 2),
                'volume': volume,
                'daily_change_percent': round(change_percent, 2),
                'daily_high': round(high, 2),
                'daily_low': round(low, 2),
                'week_52_high': round(price * 1.25, 2),  # Alpha Vantage doesn't provide this in GLOBAL_QUOTE
                'week_52_low': round(price * 0.75, 2),
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'alphavantage'
            }
        except (KeyError, ValueError) as e:
            print(f"Error parsing quote for {ticker}: {e}")
            return self.demo_fallback.get_quote(ticker)
    
    def search_stocks(self, query: str) -> List[Dict]:
        """Search stocks using Alpha Vantage symbol search"""
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': query
        }
        
        data = self._make_request(params)
        
        if not data or 'bestMatches' not in data:
            return self.demo_fallback.search_stocks(query)
        
        results = []
        for match in data['bestMatches'][:10]:  # Limit to 10 results
            try:
                results.append({
                    'ticker': match['1. symbol'],
                    'company_name': match['2. name'],
                    'exchange': match['4. region']
                })
            except KeyError:
                continue
        
        return results if results else self.demo_fallback.search_stocks(query)
    
    def get_company_info(self, ticker: str) -> Optional[Dict]:
        """Get company overview"""
        params = {
            'function': 'OVERVIEW',
            'symbol': ticker.upper()
        }
        
        data = self._make_request(params)
        
        if not data or 'Symbol' not in data:
            return self.demo_fallback.get_company_info(ticker)
        
        try:
            return {
                'ticker': data.get('Symbol', ticker.upper()),
                'company_name': data.get('Name', ticker.upper()),
                'exchange': data.get('Exchange', 'UNKNOWN')
            }
        except KeyError:
            return self.demo_fallback.get_company_info(ticker)
    
    def get_news(self, ticker: str) -> List[Dict]:
        """Get news sentiment for ticker"""
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': ticker.upper(),
            'limit': 5
        }
        
        data = self._make_request(params)
        
        if not data or 'feed' not in data:
            return self.demo_fallback.get_news(ticker)
        
        news = []
        for item in data['feed'][:5]:
            try:
                # Determine sentiment
                sentiment_score = float(item.get('overall_sentiment_score', 0))
                if sentiment_score > 0.15:
                    sentiment = 'positive'
                elif sentiment_score < -0.15:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
                
                news.append({
                    'title': item.get('title', 'No title'),
                    'description': item.get('summary', '')[:200],
                    'sentiment': sentiment,
                    'event_type': 'news',
                    'timestamp': item.get('time_published', datetime.utcnow().isoformat())
                })
            except (KeyError, ValueError):
                continue
        
        return news if news else self.demo_fallback.get_news(ticker)


class LiveMarketDataProvider(MarketDataProvider):
    """Live market data provider - uses Alpha Vantage or falls back to demo"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        
        if api_key and api_key != 'demo':
            print(f"Initializing Alpha Vantage provider")
            self.provider = AlphaVantageProvider(api_key)
        else:
            print("No valid API key - using demo mode")
            self.provider = DemoMarketDataProvider()
    
    def get_quote(self, ticker: str) -> Optional[Dict]:
        """Get quote"""
        return self.provider.get_quote(ticker)
    
    def search_stocks(self, query: str) -> List[Dict]:
        """Search stocks"""
        return self.provider.search_stocks(query)
    
    def get_company_info(self, ticker: str) -> Optional[Dict]:
        """Get company info"""
        return self.provider.get_company_info(ticker)
    
    def get_news(self, ticker: str) -> List[Dict]:
        """Get news"""
        return self.provider.get_news(ticker)

def get_market_provider(demo_mode: bool = True) -> MarketDataProvider:
    """Factory function to get appropriate market data provider"""
    if demo_mode:
        return DemoMarketDataProvider()
    else:
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY') or os.getenv('MARKET_API_KEY')
        return LiveMarketDataProvider(api_key)
