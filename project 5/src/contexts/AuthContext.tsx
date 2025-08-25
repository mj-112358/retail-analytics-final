import React, { createContext, useContext, useState, ReactNode } from 'react';
import { authAPI } from '../utils/api';

interface User {
  id: string;
  name: string;
  email: string;
  storeName: string;
  storeId?: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (
    name: string,
    storeName: string,
    email: string,
    password: string
  ) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
  error: string;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('user_data');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [loading, setLoading] = useState(true); // Start as loading to prevent race condition
  const [error, setError] = useState('');
  const [isInitialized, setIsInitialized] = useState(false);

  const login = async (email: string, password: string): Promise<boolean> => {
    setLoading(true);
    setError('');
    try {
      console.log('🚀 Attempting login...');
      const response = await authAPI.login({
        email,
        password,
      });

      // Backend returns: {"token": "...", "user": {...}}
      const { token, user: userData } = response.data;

      // Transform backend user data to frontend format
      const user = {
        id: userData.id.toString(),
        name: userData.name,
        email: userData.email,
        storeName: userData.store_name,
        storeId: userData.store_id || '1',
      };

      setUser(user);
      localStorage.setItem('user_data', JSON.stringify(user));
      localStorage.setItem('auth_token', token);

      // Console log for testing
      console.log('✅ Login successful:', { user, token });

      // Ensure we're not in loading state after successful login
      setLoading(false);
      return true;
    } catch (error: unknown) {
      const errorObj = error as {
        code?: string;
        message?: string;
        response?: { data?: { error?: string }; status?: number };
      };
      let errorMessage = 'Login failed';

      if (errorObj.code === 'ERR_NETWORK' || errorObj.message === 'Network Error') {
        errorMessage =
          'Network error: Cannot connect to server. Please check if your backend is running.';
      } else if (errorObj.response?.data?.error) {
        errorMessage = errorObj.response.data.error;
      } else if (errorObj.message) {
        errorMessage = errorObj.message;
      }

      console.error('❌ Login error:', errorMessage);
      setError(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (
    name: string,
    storeName: string,
    email: string,
    password: string
  ): Promise<boolean> => {
    setLoading(true);
    setError('');
    try {
      console.log('🚀 Attempting signup...');
      const response = await authAPI.signup({
        name,
        email,
        password,
        store_name: storeName,
      });

      // Backend returns: {"token": "...", "user": {...}}
      const { token, user: userData } = response.data;

      // Transform backend user data to frontend format
      const user = {
        id: userData.id.toString(),
        name: userData.name,
        email: userData.email,
        storeName: userData.store_name,
        storeId: userData.store_id || '1',
      };

      setUser(user);
      localStorage.setItem('user_data', JSON.stringify(user));
      localStorage.setItem('auth_token', token);

      console.log('✅ Signup successful:', { user, token });
      
      // Ensure we're not in loading state after successful signup
      setLoading(false);
      return true;
    } catch (error: unknown) {
      const errorObj = error as {
        code?: string;
        message?: string;
        response?: { data?: { error?: string }; status?: number };
      };
      let errorMessage = 'Signup failed';

      console.error('🔥 Signup error details:', {
        message: errorObj.message,
        code: errorObj.code,
        response: errorObj.response?.data,
        status: errorObj.response?.status,
      });

      if (errorObj.code === 'ECONNABORTED') {
        errorMessage =
          'Request timed out. Your backend might be starting up. Please try again in 30 seconds.';
      } else if (
        errorObj.code === 'ERR_NETWORK' ||
        errorObj.message === 'Network Error'
      ) {
        errorMessage =
          'Network error: Cannot reach server. Please check if your backend is running.';
      } else if (errorObj.response?.status === 503) {
        errorMessage =
          'Server temporarily unavailable. Backend might be restarting.';
      } else if (errorObj.response?.data?.error) {
        errorMessage = errorObj.response.data.error;
      } else if (errorObj.message) {
        errorMessage = errorObj.message;
      }

      setError(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user_data');
    localStorage.removeItem('auth_token');
    setError('');
    console.log('✅ Logout successful');
  };

  const clearError = () => {
    setError('');
  };
  React.useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('auth_token');
      const savedUser = localStorage.getItem('user_data');

      if (token && savedUser) {
        console.log('✅ Found existing auth token - user already logged in');
        // User is already set from useState initializer
        // No need to call setUser again - prevents race condition
      } else {
        console.log('❌ No auth token found - user not logged in');
        setUser(null);
      }
      
      setIsInitialized(true);
      setLoading(false);
    };

    // Small delay to ensure login calls complete first
    const timeoutId = setTimeout(initializeAuth, 100);
    return () => clearTimeout(timeoutId);
  }, []);

  // For local development, we don't need to load user profile
  // since we already have all the user data from login/signup
  const value = {
    user,
    login,
    signup,
    logout,
    isAuthenticated: !!user && isInitialized,
    loading,
    error,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
