import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import apiService, { setQuotaUpdater, setTokenProvider } from '../services/apiService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // JWT lives ONLY in memory — never localStorage or sessionStorage (XSS protection)
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  // Quota state — populated by Story 5.3 via response headers
  const [quotaRemaining, setQuotaRemaining] = useState(null);
  const [quotaLimit, setQuotaLimit] = useState(10);

  // Keep apiService's token getter in sync whenever token changes
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

  // Called by Story 5.3 quota middleware after each generation response
  const updateQuota = useCallback((remaining, limit) => {
    setQuotaRemaining(remaining);
    setQuotaLimit(limit);
  }, []);

  // Wire quota updater so response interceptor can push header values into context
  // Must come after updateQuota is defined
  useEffect(() => {
    setQuotaUpdater(updateQuota);
  }, [updateQuota]);

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
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}

export default AuthProvider;
