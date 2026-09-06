import React, { useState, useEffect } from 'react';
import { getWatchlist, removeFromWatchlist } from '../services/api';
import StockSearch from '../components/StockSearch';
import StockCard from '../components/StockCard';

const Watchlist = () => {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    loadWatchlist();
  }, []);
  
  const loadWatchlist = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await getWatchlist();
      setWatchlist(response.data);
    } catch (err) {
      setError('Failed to load watchlist');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleRemove = async (ticker) => {
    if (!confirm(`Remove ${ticker} from watchlist?`)) {
      return;
    }
    
    try {
      await removeFromWatchlist(ticker);
      await loadWatchlist();
    } catch (err) {
      console.error('Failed to remove stock:', err);
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Your Watchlist</h1>
        <p className="text-slate-400">Add and manage stocks you want to track</p>
      </div>
      
      {/* Search */}
      <div className="mb-8">
        <StockSearch onStockAdded={loadWatchlist} />
      </div>
      
      {error && (
        <div className="mb-6 px-4 py-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400">
          {error}
        </div>
      )}
      
      {/* Watchlist */}
      {watchlist.length === 0 ? (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
          <div className="text-6xl mb-4">📈</div>
          <h2 className="text-xl font-semibold text-white mb-2">No stocks in your watchlist</h2>
          <p className="text-slate-400">Search and add stocks above to get started</p>
        </div>
      ) : (
        <div className="space-y-4">
          {watchlist.map((stock) => (
            <div
              key={stock.ticker}
              className="bg-slate-800 border border-slate-700 rounded-lg p-6 flex justify-between items-center hover:border-slate-600 transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center gap-4 mb-3">
                  <div>
                    <div className="text-sm text-slate-400">{stock.ticker}</div>
                    <div className="text-xl font-semibold text-white">{stock.company_name}</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Current Price</div>
                    <div className="text-lg font-bold text-white">${stock.price.toFixed(2)}</div>
                  </div>
                  
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Today's Change</div>
                    <div
                      className={`text-lg font-medium ${
                        stock.daily_change_percent >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {stock.daily_change_percent >= 0 ? '+' : ''}
                      {stock.daily_change_percent.toFixed(2)}%
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Since Last Check</div>
                    <div
                      className={`text-lg font-medium ${
                        stock.change_since_check >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {stock.change_since_check >= 0 ? '+' : ''}
                      {stock.change_since_check.toFixed(2)}%
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Volume</div>
                    <div className="text-lg font-medium text-white">
                      {(stock.volume / 1000000).toFixed(2)}M
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-2 ml-6">
                <a
                  href={`/stock/${stock.ticker}`}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Details
                </a>
                <button
                  onClick={() => handleRemove(stock.ticker)}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {watchlist.length > 0 && (
        <div className="mt-6 text-center text-sm text-slate-400">
          Tracking {watchlist.length} stock{watchlist.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
};

export default Watchlist;
