import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import axiosService, { getAuth, setAuth, clearAuth } from '../api/axios';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUserInfo = useCallback(async () => {
    const auth = getAuth();
    if (!auth?.access_token) {
      setUser(null);
      setLoading(false);
      return null;
    }

    try {
      const { data } = await axiosService.get('/user/info');
      const next = {
        username: data.username,
        role: data.role,
      };
      setUser(next);
      return next;
    } catch {
      clearAuth();
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUserInfo();
  }, [loadUserInfo]);

  const login = useCallback(async (username, password) => {
    const { data } = await axiosService.post('/auth', { username, password });
    setAuth({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    });
    const info = await loadUserInfo();
    return info;
  }, [loadUserInfo]);

  const register = useCallback(async (username, password) => {
    await axiosService.post('/signup', { username, password });
  }, []);

  const logout = useCallback(async () => {
    try {
      await axiosService.post('/logout');
    } catch {
      // ignore network errors on logout
    } finally {
      clearAuth();
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      isAdmin: user?.role === 'admin',
      login,
      register,
      logout,
      loadUserInfo,
    }),
    [user, loading, login, register, logout, loadUserInfo],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
