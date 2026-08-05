import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

interface AuthContextType {
  user: {
    email: string;
    organization_id: number;
    first_name: string;
    last_name: string;
    roles: string[];
    permissions: string[];
  } | null;
  token: string | null;
  login: (token: string, refreshToken?: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const decodeToken = (token: string) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map((c) => {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthContextType['user']>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  useEffect(() => {
    if (!token) {
      setUser(null);
      return;
    }

    const decoded = decodeToken(token);
    if (!decoded) {
      setUser(null);
      return;
    }

    setUser({
      email: decoded.sub,
      organization_id: decoded.org_id,
      first_name: '',
      last_name: '',
      roles: decoded.roles || [],
      permissions: [],
    });

    api.get('/api/auth/me').then((res) => {
      setUser({
        email: res.data.email,
        organization_id: res.data.organization_id,
        first_name: res.data.first_name,
        last_name: res.data.last_name,
        roles: res.data.roles || [],
        permissions: res.data.permissions || [],
      });
    }).catch(() => {
      // fallback: keep basic info from JWT
    });
  }, [token]);

  const login = (newToken: string, refreshToken?: string) => {
    localStorage.setItem('token', newToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
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
