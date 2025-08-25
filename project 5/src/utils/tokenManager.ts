/**
 * Token Management for RetailIQ Analytics
 * Handles JWT token refresh and expiration
 */

import { authAPI } from './api';

interface TokenData {
  access_token: string;
  refresh_token: string;
  expires_at: number;
}

class TokenManager {
  private static instance: TokenManager;
  private refreshPromise: Promise<boolean> | null = null;

  private constructor() {}

  public static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }

  /**
   * Check if token is expired or will expire soon (within 5 minutes)
   */
  public isTokenExpired(token?: string): boolean {
    const tokenToCheck = token || this.getAccessToken();
    if (!tokenToCheck) return true;

    // For local development with simple string tokens
    if (tokenToCheck === 'local-test-token') {
      console.log('✅ Local development token detected - never expires');
      return false;
    }

    try {
      // Try to parse as JWT token
      const parts = tokenToCheck.split('.');
      if (parts.length !== 3) {
        console.warn('⚠️  Token is not a valid JWT format, treating as simple token');
        return false; // For non-JWT tokens, assume they don't expire
      }

      const payload = JSON.parse(atob(parts[1]));
      const expiresAt = payload.exp * 1000; // Convert to milliseconds
      const now = Date.now();
      const fiveMinutes = 5 * 60 * 1000; // 5 minutes in milliseconds
      
      return (expiresAt - now) < fiveMinutes;
    } catch (error) {
      console.error('Error parsing token:', error);
      // For local development, if token parsing fails, assume it's a simple token
      return false;
    }
  }

  /**
   * Get access token from localStorage
   */
  public getAccessToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  /**
   * Get refresh token from localStorage
   */
  public getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  /**
   * Store tokens in localStorage
   */
  public setTokens(tokenData: TokenData): void {
    localStorage.setItem('auth_token', tokenData.access_token);
    localStorage.setItem('refresh_token', tokenData.refresh_token);
    
    // Calculate expiration time
    const expiresAt = Date.now() + (tokenData.expires_at * 1000);
    localStorage.setItem('token_expires_at', expiresAt.toString());
  }

  /**
   * Clear all tokens from localStorage
   */
  public clearTokens(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expires_at');
    localStorage.removeItem('user_data');
  }

  /**
   * Refresh access token using refresh token
   */
  public async refreshAccessToken(): Promise<boolean> {
    // Prevent multiple simultaneous refresh attempts
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      this.clearTokens();
      return false;
    }

    this.refreshPromise = this.performTokenRefresh(refreshToken);
    const result = await this.refreshPromise;
    this.refreshPromise = null;
    
    return result;
  }

  /**
   * Perform the actual token refresh API call
   */
  private async performTokenRefresh(refreshToken: string): Promise<boolean> {
    try {
      // Note: This endpoint needs to be implemented in the backend
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:3000'}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        
        this.setTokens({
          access_token: data.access_token,
          refresh_token: data.refresh_token || refreshToken,
          expires_at: data.expires_in || 3600,
        });

        console.log('✅ Token refreshed successfully');
        return true;
      } else {
        console.log('❌ Token refresh failed:', response.status);
        this.clearTokens();
        return false;
      }
    } catch (error) {
      console.error('❌ Token refresh error:', error);
      this.clearTokens();
      return false;
    }
  }

  /**
   * Get a valid access token, refreshing if necessary
   */
  public async getValidAccessToken(): Promise<string | null> {
    const accessToken = this.getAccessToken();
    
    if (!accessToken) {
      return null;
    }

    // For local development with simple tokens
    if (accessToken === 'local-test-token') {
      console.log('✅ Returning local development token');
      return accessToken;
    }

    // If token is not expired, return it
    if (!this.isTokenExpired(accessToken)) {
      return accessToken;
    }

    // Try to refresh the token
    const refreshed = await this.refreshAccessToken();
    if (refreshed) {
      return this.getAccessToken();
    }

    // Refresh failed, redirect to login
    window.location.href = '/';
    return null;
  }

  /**
   * Schedule automatic token refresh
   */
  public scheduleTokenRefresh(): void {
    const token = this.getAccessToken();
    if (!token || this.isTokenExpired(token)) {
      return;
    }

    // For local development, don't schedule refresh
    if (token === 'local-test-token') {
      console.log('✅ Local development token - no refresh needed');
      return;
    }

    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        console.log('⚠️  Non-JWT token - no refresh needed');
        return;
      }

      const payload = JSON.parse(atob(parts[1]));
      const expiresAt = payload.exp * 1000;
      const now = Date.now();
      const refreshTime = expiresAt - now - (10 * 60 * 1000); // Refresh 10 minutes before expiry

      if (refreshTime > 0) {
        setTimeout(() => {
          this.refreshAccessToken();
        }, refreshTime);
      }
    } catch (error) {
      console.error('Error scheduling token refresh:', error);
    }
  }
}

export default TokenManager;