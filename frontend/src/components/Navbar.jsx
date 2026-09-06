import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;
  
  return (
    <nav className="bg-slate-800 border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <div className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                MARKETPULSE
              </div>
            </Link>
            <div className="ml-2 text-xs text-slate-400 hidden sm:block">
              Know what changed. Know what matters.
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <Link
              to="/"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/')
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/watchlist"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/watchlist')
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              Watchlist
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
