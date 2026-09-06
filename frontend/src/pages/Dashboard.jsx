import React, { useState, useEffect } from 'react';
import { getDashboard, updateCheckpoint } from '../services/api';
import StockCard from '../components/StockCard';

const Dashboard = () => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  
  useEffect(() => {
    loadDashboard();
  }, []);
  
  const loadDashboard = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await getDashboard();
      setDashboard(response.data);
    } catch (err) {
      setError('Failed to load dashboard');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await updateCheckpoint();
      await loadDashboard();
    } catch (err) {
      console.error('Failed to refresh:', err);
    } finally {
      setRefreshing(false);
    }
  };
  
  const formatTimeAgo = (hours) => {
    if (!hours) return '';
    
    if (hours < 1) {
      const minutes = Math.floor(hours * 60);
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${Math.floor(hours)}h ago`;
    } else {
      const days = Math.floor(hours / 24);
      return `${days}d ago`;
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-500/20 border border-red-500 rounded-lg p-6 text-red-400">
          {error}
        </div>
      </div>
    );
  }
  
  if (!dashboard || dashboard.changes.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-2xl font-bold text-white mb-2">Your watchlist is empty</h2>
          <p className="text-slate-400 mb-6">Add some stocks to get started and see what matters</p>
          <a
            href="/watchlist"
            className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            Go to Watchlist
          </a>
        </div>
      </div>
    );
  }
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Welcome back</h1>
            <p className="text-slate-400">Here's what changed since your last visit</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <span>{refreshing ? '↻' : '⟳'}</span>
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
        
        {/* Summary Stats */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <div className="text-sm text-slate-400 mb-3">
            Since your last visit — {formatTimeAgo(dashboard.hours_since_check)}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {dashboard.needs_attention_count > 0 && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-red-400">
                  🔴 {dashboard.needs_attention_count}
                </div>
                <div className="text-xs text-red-300 mt-1">Need Attention</div>
              </div>
            )}
            {dashboard.significant_count > 0 && (
              <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-orange-400">
                  🟠 {dashboard.significant_count}
                </div>
                <div className="text-xs text-orange-300 mt-1">Significant</div>
              </div>
            )}
            {dashboard.worth_watching_count > 0 && (
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                <div className="text-2xl font-bold text-yellow-400">
                  🟡 {dashboard.worth_watching_count}
                </div>
                <div className="text-xs text-yellow-300 mt-1">Worth Watching</div>
              </div>
            )}
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
              <div className="text-2xl font-bold text-green-400">
                🟢 {dashboard.normal_count}
              </div>
              <div className="text-xs text-green-300 mt-1">Unchanged</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* What Did I Miss */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-4">WHAT DID I MISS?</h2>
        
        {/* Show meaningful changes first */}
        <div className="space-y-4">
          {dashboard.changes
            .filter((c) => c.severity !== 'normal')
            .map((change) => (
              <div
                key={change.ticker}
                className="bg-slate-800 border border-slate-700 rounded-lg p-6"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="text-3xl">{change.status_emoji}</div>
                    <div>
                      <div className="text-xl font-bold text-white">{change.company_name}</div>
                      <div className="text-sm text-slate-400">{change.ticker}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white">
                      ${change.current_price.toFixed(2)}
                    </div>
                    <div
                      className={`text-lg font-medium ${
                        change.price_change_percent >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {change.price_change_percent >= 0 ? '+' : ''}
                      {change.price_change_percent.toFixed(2)}%
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Attention Score</div>
                    <div className="flex items-center gap-2">
                      <div className="text-xl font-bold text-white">{change.attention_score}/100</div>
                      <div className="flex-1 bg-slate-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            change.attention_score >= 81
                              ? 'bg-red-500'
                              : change.attention_score >= 61
                              ? 'bg-orange-500'
                              : 'bg-yellow-500'
                          }`}
                          style={{ width: `${change.attention_score}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  
                  {change.volume_change_percent !== 0 && (
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Volume Change</div>
                      <div className="text-lg font-medium text-white">
                        {change.volume_change_percent >= 0 ? '+' : ''}
                        {change.volume_change_percent.toFixed(1)}%
                      </div>
                    </div>
                  )}
                  
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Status</div>
                    <div className="text-lg font-medium text-white capitalize">
                      {change.severity.replace('_', ' ')}
                    </div>
                  </div>
                </div>
                
                {change.explanation && (
                  <div className="bg-slate-900/50 rounded-lg p-4 mb-3">
                    <div className="text-sm font-medium text-blue-400 mb-1">Why it matters:</div>
                    <div className="text-sm text-slate-300">{change.explanation}</div>
                  </div>
                )}
                
                {change.reasons && change.reasons.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {change.reasons.map((reason, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-slate-700 rounded-full text-xs text-slate-300"
                      >
                        {reason}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
        </div>
      </div>
      
      {/* Normal stocks (collapsed) */}
      {dashboard.normal_count > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-slate-400 mb-4">
            Normal Activity ({dashboard.normal_count})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dashboard.changes
              .filter((c) => c.severity === 'normal')
              .map((change) => (
                <StockCard key={change.ticker} stock={change} />
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
