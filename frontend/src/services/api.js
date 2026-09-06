import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const healthCheck = () => api.get('/health');

export const getWatchlist = () => api.get('/watchlist');

export const addToWatchlist = (ticker) => api.post('/watchlist', { ticker });

export const removeFromWatchlist = (ticker) => api.delete(`/watchlist/${ticker}`);

export const searchStocks = (query) => api.get(`/stocks/search?q=${query}`);

export const getStockDetail = (ticker) => api.get(`/stocks/${ticker}`);

export const getDashboard = () => api.get('/dashboard');

export const updateCheckpoint = () => api.post('/checkpoint');

export const refreshData = () => api.post('/refresh');

export default api;
