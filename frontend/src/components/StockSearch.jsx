import React, { useState } from 'react';
import { searchStocks, addToWatchlist } from '../services/api';

const StockSearch = ({ onStockAdded }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [adding, setAdding] = useState(null);
  
  const handleSearch = async (searchQuery) => {
    setQuery(searchQuery);
    
    if (searchQuery.length < 1) {
      setResults([]);
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await searchStocks(searchQuery);
      setResults(response.data);
    } catch (err) {
      setError('Failed to search stocks');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleAdd = async (ticker) => {
    setAdding(ticker);
    setError('');
    
    try {
      await addToWatchlist(ticker);
      setQuery('');
      setResults([]);
      if (onStockAdded) {
        onStockAdded();
      }
    } catch (err) {
      if (err.response?.status === 400) {
        setError('Stock already in watchlist');
      } else if (err.response?.status === 404) {
        setError('Stock not found');
      } else {
        setError('Failed to add stock');
      }
      console.error(err);
    } finally {
      setAdding(null);
    }
  };
  
  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Search stocks by ticker or name..."
          className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        {loading && (
          <div className="absolute right-3 top-3">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        )}
      </div>
      
      {error && (
        <div className="mt-2 px-4 py-2 bg-red-500/20 border border-red-500 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}
      
      {results.length > 0 && (
        <div className="absolute z-10 w-full mt-2 bg-slate-800 border border-slate-600 rounded-lg shadow-lg max-h-80 overflow-y-auto">
          {results.map((stock) => (
            <div
              key={stock.ticker}
              className="flex justify-between items-center px-4 py-3 hover:bg-slate-700 border-b border-slate-700 last:border-b-0"
            >
              <div>
                <div className="font-semibold text-white">{stock.company_name}</div>
                <div className="text-sm text-slate-400">
                  {stock.ticker} · {stock.exchange}
                </div>
              </div>
              <button
                onClick={() => handleAdd(stock.ticker)}
                disabled={adding === stock.ticker}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
              >
                {adding === stock.ticker ? 'Adding...' : '+ Add'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StockSearch;
