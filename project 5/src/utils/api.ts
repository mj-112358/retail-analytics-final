import axios from 'axios';

// API configuration - MUST be set via environment variable for production
export const API_BASE_URL = (() => {
  const apiUrl = import.meta.env.VITE_API_URL;
  
  if (!apiUrl) {
    console.warn('⚠️ VITE_API_URL not set. Using development fallback.');
    console.warn('🔧 Set VITE_API_URL in Vercel environment variables to: https://YOUR-RAILWAY-PROJECT.railway.app');
    return 'http://localhost:3000'; // Development fallback - matches Railway PORT default
  }
  
  // Clean up URL (remove trailing slash)
  const cleanUrl = apiUrl.replace(/\/$/, '');
  console.log('🌐 API Base URL configured:', cleanUrl);
  return cleanUrl;
})();

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // Increased timeout for backend cold starts
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request interceptor to add auth token with automatic refresh
api.interceptors.request.use(
  async (config) => {
    try {
      const { default: TokenManager } = await import('./tokenManager');
      const tokenManager = TokenManager.getInstance();
      const token = await tokenManager.getValidAccessToken();
      
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error getting valid token:', error);
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('🔥 API Error Details:', {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
      url: error.config?.url,
      baseURL: error.config?.baseURL,
      fullURL: `${error.config?.baseURL}${error.config?.url}`,
      timeout:
        error.code === 'ECONNABORTED' ? 'Request timed out' : 'No timeout',
      networkError:
        error.code === 'ERR_NETWORK'
          ? 'Network connection failed'
          : 'No network error',
    });

    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API functions
export const authAPI = {
  signup: (data: { name: string; email: string; password: string; store_name: string }) => {
    console.log('🚀 Making signup request to:', `${API_BASE_URL}/api/auth/signup`);
    console.log('📦 Request data:', data);
    return api.post('/api/auth/signup', data);
  },

  login: (data: { email: string; password: string }) => {
    console.log('🚀 Making login request to:', `${API_BASE_URL}/api/auth/login`);
    return api.post('/api/auth/login', data);
  },

  getProfile: () => {
    console.log(
      '🚀 Making profile request to:',
      `${API_BASE_URL}/api/auth/me`
    );
    return api.get('/api/auth/me');
  },

  verifyToken: () => {
    console.log(
      '🚀 Making verify token request to:',
      `${API_BASE_URL}/api/auth/verify-token`
    );
    const token = localStorage.getItem('auth_token');
    return api.post('/api/auth/verify-token', { token });
  },

  // Health check endpoint
  healthCheck: () => {
    console.log('🚀 Making health check request to:', `${API_BASE_URL}/health`);
    return api.get('/health');
  },

  // Direct test endpoint
  testConnection: async () => {
    console.log('🔍 Testing direct connection to backend...');
    try {
      // Test direct fetch to bypass axios
      const response = await fetch(`${API_BASE_URL}/api/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('✅ Direct fetch response:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
      });

      const data = await response.json();
      console.log('✅ Direct fetch data:', data);
      return { success: true, data };
    } catch (error) {
      console.error('❌ Direct fetch failed:', error);
      return { success: false, error };
    }
  },
};

// Camera Management API
export const cameraAPI = {
  // Get all cameras for user
  getCameras: () => {
    console.log('🚀 Making get cameras request to:', `${API_BASE_URL}/cameras`);
    return api.get('/cameras');
  },

  // Add new camera
  addCamera: (data: { name: string; rtsp_url: string; zone_type: string; location_description?: string }) => {
    console.log('🚀 Making add camera request to:', `${API_BASE_URL}/cameras`);
    return api.post('/cameras', data);
  },

  // Update camera
  updateCamera: (cameraId: number, data: any) => {
    console.log('🚀 Making update camera request to:', `${API_BASE_URL}/cameras/${cameraId}`);
    return api.put(`/cameras/${cameraId}`, data);
  },

  // Delete camera
  deleteCamera: (cameraId: number) => {
    console.log('🚀 Making delete camera request to:', `${API_BASE_URL}/cameras/${cameraId}`);
    return api.delete(`/cameras/${cameraId}`);
  },

  // Get camera status
  getCameraStatus: (cameraId: number) => {
    console.log('🚀 Making get camera status request to:', `${API_BASE_URL}/cameras/${cameraId}/status`);
    return api.get(`/cameras/${cameraId}/status`);
  },

  // Test RTSP connection
  testRTSP: (rtsp_url: string) => {
    console.log('🚀 Making test RTSP request to:', `${API_BASE_URL}/test-rtsp`);
    return api.post('/test-rtsp', null, { params: { rtsp_url } });
  },

  // Get detection status for all cameras
  getDetectionStatus: () => {
    console.log('🚀 Making get detection status request to:', `${API_BASE_URL}/cameras/status`);
    return api.get('/cameras/status');
  },

  // Get feature types
  getFeatureTypes: () => {
    console.log('🚀 Making get feature types request to:', `${API_BASE_URL}/cameras/features`);
    return api.get('/cameras/features');
  },
};

// Dashboard Analytics API
export const dashboardAPI = {
  // Get dashboard metrics
  getMetrics: (date?: string) => {
    console.log('🚀 Making get dashboard metrics request to:', `${API_BASE_URL}/api/dashboard/metrics`);
    return api.get(`/api/dashboard/metrics${date ? `?date=${date}` : ''}`);
  },

  // Generate AI insights
  generateInsights: (data: {
    period_start: string;
    period_end: string;
    insight_type?: string;
    include_promo?: boolean;
    promo_start?: string;
    promo_end?: string;
  }) => {
    console.log('🚀 Making generate insights request to:', `${API_BASE_URL}/api/dashboard/insights`);
    return api.post('/api/dashboard/insights', data);
  },

  // Get insights history
  getInsightsHistory: (limit = 10) => {
    console.log('🚀 Making get insights history request to:', `${API_BASE_URL}/api/insights/history`);
    return api.get(`/api/insights/history?limit=${limit}`);
  },
};

// Analytics API
export const analyticsAPI = {
  // Get hourly analytics
  getHourlyAnalytics: (cameraId: number, date: string) => {
    console.log('🚀 Making get hourly analytics request to:', `${API_BASE_URL}/api/analytics/hourly`);
    return api.get(`/api/analytics/hourly?camera_id=${cameraId}&date=${date}`);
  },

  // Get daily analytics
  getDailyAnalytics: (date: string) => {
    console.log('🚀 Making get daily analytics request to:', `${API_BASE_URL}/api/analytics/daily`);
    return api.get(`/api/analytics/daily?date=${date}`);
  },

  // Get combined store metrics
  getCombinedMetrics: (storeId: number, startDate: string, endDate: string) => {
    console.log('🚀 Making get combined metrics request to:', `${API_BASE_URL}/stores/${storeId}/metrics/combined`);
    return api.get(`/stores/${storeId}/metrics/combined?start_date=${startDate}&end_date=${endDate}`);
  },
};

// Promotion API
export const promotionAPI = {
  // Create promotion
  createPromotion: (data: any) => {
    console.log('🚀 Making create promotion request to:', `${API_BASE_URL}/api/promotions`);
    return api.post('/api/promotions', data);
  },

  // Get promotions
  getPromotions: (activeOnly = true) => {
    console.log('🚀 Making get promotions request to:', `${API_BASE_URL}/api/promotions`);
    return api.get(`/api/promotions?active_only=${activeOnly}`);
  },
};

// System API
export const systemAPI = {
  // Get system health
  getSystemHealth: () => {
    console.log('🚀 Making get system health request to:', `${API_BASE_URL}/api/system/health`);
    return api.get('/api/system/health');
  },
};

export default api;
