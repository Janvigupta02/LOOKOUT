import React from 'react';
import { useNavigate } from 'react-router-dom';

const StockCard = ({ stock }) => {
  const navigate = useNavigate();
  
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'needs_attention':
        return 'border-red-500 bg-red-500/10';
      case 'significant':
        return 'border-orange-500 bg-orange-500/10';
      case 'worth_watching':
        return 'border-yellow-500 bg-yellow-500/10';
      default:
        return 'border-slate-600 bg-slate-800/50';
    }
  };
  
  const getStatusEmoji = (severity) => {
    switch (severity) {
      case 'needs_attention':
        return '🔴';
      case 'significant':
        return '🟠';
      case 'worth_watching':
        return '🟡';
      default:
        return '🟢';
    }
  };
  
  const getStatusText = (severity) => {
    switch (severity) {
      case 'needs_attention':
        return 'Needs Attention';
      case 'significant':
        return 'Significant';
      case 'worth_watching':
        return 'Worth Watching';
      default:
        return 'Normal';
    }
  };
  
  return (
    <div
      onClick={() => navigate(`/stock/${stock.ticker}`)}
      className={`border-2 rounded-lg p-5 cursor-pointer transition-all hover:scale-105 ${getSeverityColor(
        stock.severity
      )}`}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="text-slate-400 text-sm">{stock.ticker}</div>
          <div className="text-lg font-semibold text-white">{stock.company_name}</div>
        </div>
        <div className="text-2xl">{stock.status_emoji || getStatusEmoji(stock.severity)}</div>
      </div>
      
      <div className="mb-3">
        <div className="text-2xl font-bold text-white">
          ${stock.current_price?.toFixed(2) || stock.price?.toFixed(2)}
        </div>
        <div className="flex gap-3 mt-1">
          <div
            className={`text-sm font-medium ${
              (stock.price_change_percent || stock.change_since_check || 0) >= 0
                ? 'text-green-400'
                : 'text-red-400'
            }`}
          >
            {(stock.price_change_percent || stock.change_since_check || 0) >= 0 ? '+' : ''}
            {(stock.price_change_percent || stock.change_since_check || 0).toFixed(2)}%
          </div>
          {stock.daily_change_percent !== undefined && (
            <div className="text-sm text-slate-400">
              Today: {stock.daily_change_percent >= 0 ? '+' : ''}
              {stock.daily_change_percent.toFixed(2)}%
            </div>
          )}
        </div>
      </div>
      
      {stock.attention_score !== undefined && (
        <div className="mb-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-slate-400">Attention Score</span>
            <span className="text-sm font-bold text-white">{stock.attention_score}/100</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                stock.attention_score >= 81
                  ? 'bg-red-500'
                  : stock.attention_score >= 61
                  ? 'bg-orange-500'
                  : stock.attention_score >= 31
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
              style={{ width: `${stock.attention_score}%` }}
            />
          </div>
        </div>
      )}
      
      <div className="flex items-center justify-between">
        <div className="text-xs font-medium text-slate-300">
          {getStatusText(stock.severity)}
        </div>
        {stock.reasons && stock.reasons.length > 0 && (
          <div className="text-xs text-slate-400">{stock.reasons[0]}</div>
        )}
      </div>
    </div>
  );
};

export default StockCard;
