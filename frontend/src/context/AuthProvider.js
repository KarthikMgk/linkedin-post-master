import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { setTokenProvider } from '../services/apiService';
import apiService from '../services/apiService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [quotaRemaining, setQuotaRemaining] = useState(null);
  const [quotaLimit, setQuotaLimit] = useState(10);

  // Keep apiService's token provider in sync — NEVER use localStorage
  useEffect(() => {
    setTokenProvider(() => token);
  }, [token]);

  const login = useCallback(async (googleCredential) => {
    const data = await apiService.loginWithGoogle(googleCredential);
    setToken(data.token);
    setUser(data.user);
    return data;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setQuotaRemaining(null);
  }, []);

  const updateQuota = useCallback((remaining, limit) => {
    setQuotaRemaining(remaining);
    setQuotaLimit(limit);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        quotaRemaining,
        quotaLimit,
        isAuthenticated: !!token,
        login,
        logout,
        updateQuota,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export default AuthProvider;
