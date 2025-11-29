'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '@/lib/api';
import { User, LoginRequest } from '@/lib/types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  // Mark component as mounted (client-side only)
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    // Only run on client side after mount
    if (!mounted) {
      return;
    }

    // Check for existing token on mount
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      setToken(storedToken);
      // Sync cookie
      document.cookie = `auth_token=${storedToken}; path=/; max-age=86400; SameSite=Lax`;
      // Fetch user info
      fetchUserInfo(storedToken);
    } else {
      setIsLoading(false);
    }
  }, [mounted]);

  const fetchUserInfo = async (authToken: string) => {
    try {
      const response = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setUser(response.data);
    } catch (error: any) {
      console.error('Failed to fetch user info:', error);
      // Clear invalid token
      localStorage.removeItem('auth_token');
      document.cookie = 'auth_token=; path=/; max-age=0; SameSite=Lax';
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await api.post('/auth/login', credentials);
      const { access_token } = response.data;
      
      if (!access_token) {
        throw new Error('No access token received');
      }
      
      // Store token
      localStorage.setItem('auth_token', access_token);
      document.cookie = `auth_token=${access_token}; path=/; max-age=86400; SameSite=Lax`;
      setToken(access_token);
      
      // Fetch user
      await fetchUserInfo(access_token);
      
      // Hard redirect to dashboard
      window.location.href = '/dashboard';
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    document.cookie = 'auth_token=; path=/; max-age=0; SameSite=Lax';
    setToken(null);
    setUser(null);
    window.location.href = '/login';
  };

  // During SSR or before mount, return loading state
  if (!mounted) {
    return (
      <AuthContext.Provider
        value={{
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: true,
          login: async () => {},
          logout: () => {},
        }}
      >
        {children}
      </AuthContext.Provider>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

